"""Transactional, content-addressed batch ingestion and version-aware upserts."""

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sqlite3
import uuid

from .validation import InvalidRecord, validate

MAX_BATCH_BYTES = 10 * 1024 * 1024


class QualityGateError(ValueError):
    pass


def connect(path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA foreign_keys = ON')
    conn.executescript(Path(__file__).with_name('schema.sql').read_text(encoding='utf-8'))
    return conn


def now():
    return datetime.now(timezone.utc).isoformat()


def _reject_constant(value):
    raise ValueError(f'non-finite JSON number: {value}')


def _unique_keys(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f'duplicate JSON key: {key}')
        result[key] = value
    return result


def ingest(db_path, source_path, max_reject_ratio=0.05):
    """Commit facts and batch ledger together, or roll both back.

    Incrementality is at file-content level. Per-trip update timestamps resolve
    out-of-order events; no global timestamp filter discards late-arriving trips.
    Invalid rows are durably quarantined even when the quality gate rejects a batch.
    """
    if not 0 <= max_reject_ratio <= 1:
        raise ValueError('max_reject_ratio must be between 0 and 1')
    source_path = Path(source_path)
    with source_path.open('rb') as handle:
        payload = handle.read(MAX_BATCH_BYTES + 1)
    if len(payload) > MAX_BATCH_BYTES:
        raise ValueError('batch exceeds 10 MiB limit; split into smaller batches')
    batch_hash = hashlib.sha256(payload).hexdigest()
    text = payload.decode('utf-8')
    lines = [(n, line) for n, line in enumerate(text.splitlines(), 1) if line.strip()]
    if not lines:
        raise ValueError('empty batch')
    metrics = dict(rows_read=len(lines), inserted=0, updated=0, unchanged=0, stale=0, rejected=0)
    started, run_id, rejects = now(), uuid.uuid4().hex, []
    conn = connect(db_path)
    try:
        # Serialize writers before checking the ledger; replay cannot race another commit.
        conn.execute('BEGIN IMMEDIATE')
        if conn.execute('SELECT 1 FROM ingested_batch WHERE batch_hash = ?', (batch_hash,)).fetchone():
            metrics['rows_read'] = 0
            status = 'skipped'
        else:
            routes = {r[0] for r in conn.execute('SELECT route_id FROM dim_route')}
            versions = []
            for line_number, raw in lines:
                try:
                    record = json.loads(raw, parse_constant=_reject_constant, object_pairs_hook=_unique_keys)
                    row = validate(record, routes)
                    old = conn.execute(
                        'SELECT updated_at_utc, payload_hash FROM fact_trip WHERE trip_id = ?',
                        (row['trip_id'],),
                    ).fetchone()
                    if old and row['updated_at_utc'] == old['updated_at_utc']:
                        if row['payload_hash'] != old['payload_hash']:
                            raise InvalidRecord('version conflict: same trip and update time have different payloads')
                        metrics['unchanged'] += 1
                    elif old and row['updated_at_utc'] < old['updated_at_utc']:
                        metrics['stale'] += 1
                    else:
                        columns = list(row)
                        assignments = ', '.join(f'{c}=excluded.{c}' for c in columns if c != 'trip_id')
                        conn.execute(
                            f"INSERT INTO fact_trip ({','.join(columns)}) VALUES ({','.join('?' for _ in columns)}) "
                            f'ON CONFLICT(trip_id) DO UPDATE SET {assignments}',
                            [row[c] for c in columns],
                        )
                        metrics['updated' if old else 'inserted'] += 1
                    versions.append(row['updated_at_utc'])
                except (InvalidRecord, ValueError, TypeError, OverflowError) as exc:
                    metrics['rejected'] += 1
                    rejects.append((run_id, line_number, str(exc), raw))
            if metrics['rejected'] / metrics['rows_read'] > max_reject_ratio:
                raise QualityGateError(
                    f"{metrics['rejected']}/{metrics['rows_read']} rejected; limit is {max_reject_ratio:.1%}"
                )
            conn.execute('INSERT INTO ingested_batch VALUES (?, ?, ?, ?, ?)', (
                batch_hash, source_path.name, now(), len(lines), max(versions, default=None),
            ))
            status = 'committed'
        conn.execute('INSERT INTO run_audit VALUES (?, ?, ?, ?, ?, ?, ?, ?)', (
            run_id, batch_hash, source_path.name, status, started, now(), json.dumps(metrics), None,
        ))
        conn.executemany('INSERT INTO quarantine VALUES (?, ?, ?, ?)', rejects)
        conn.commit()
    except Exception as exc:
        conn.rollback()
        # Failure audit is a separate transaction; fact changes and ledger remain rolled back.
        failure = {**metrics, 'attempted_inserted': metrics['inserted'], 'attempted_updated': metrics['updated'],
                   'inserted': 0, 'updated': 0}
        with conn:
            conn.execute('INSERT INTO run_audit VALUES (?, ?, ?, ?, ?, ?, ?, ?)', (
                run_id, batch_hash, source_path.name, 'failed', started, now(), json.dumps(failure), str(exc),
            ))
            conn.executemany('INSERT INTO quarantine VALUES (?, ?, ?, ?)', rejects)
        raise
    finally:
        conn.close()
    return dict(run_id=run_id, batch_hash=batch_hash, status=status, **metrics)
