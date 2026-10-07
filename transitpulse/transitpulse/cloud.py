"""Cloud-agnostic snapshot coordinator, tested with an in-memory object store.

Only the HEAD compare-and-swap publishes a snapshot. Upload failures or competing
writers leave the last committed snapshot intact. Unreferenced snapshots may be
garbage-collected later; consumers must follow HEAD, never glob all snapshots.
"""

import json
from pathlib import Path
import re
import tempfile
from typing import Protocol
import uuid

from .export import export_snapshot
from .pipeline import MAX_BATCH_BYTES, connect, ingest


class ConcurrentPublishError(RuntimeError):
    pass


class ObjectStore(Protocol):
    def read(self, key: str, limit: int) -> tuple[bytes, str] | None: ...
    def write_new(self, key: str, value: bytes) -> None: ...
    def compare_and_swap(self, key: str, value: bytes, expected_etag: str | None) -> None: ...


def encode(value):
    return (json.dumps(value, indent=2, sort_keys=True) + '\n').encode('utf-8')


def process_remote(store: ObjectStore, blob_name: str):
    if not isinstance(blob_name, str) or not re.fullmatch(r'bronze/[A-Za-z0-9_-]+/[A-Za-z0-9_-]+\.jsonl', blob_name):
        raise ValueError('blob_name must match bronze/<batch-id>/<file>.jsonl')
    source = store.read(blob_name, MAX_BATCH_BYTES)
    if source is None:
        raise FileNotFoundError('input blob was not found')
    current = store.read('state/HEAD.json', 64 * 1024)
    head = json.loads(current[0]) if current else None
    expected_etag = current[1] if current else None
    snapshot_id = uuid.uuid4().hex
    with tempfile.TemporaryDirectory(prefix='transitpulse-') as tmp:
        tmp = Path(tmp)
        db = tmp / 'warehouse.sqlite'
        if head:
            if head.get('schema_version') != 1:
                raise ValueError('unsupported state schema version')
            database = store.read(head['database_blob'], 50 * 1024 * 1024)
            if database is None:
                raise FileNotFoundError('HEAD references a missing database; refusing to reset state')
            db.write_bytes(database[0])
        source_path = tmp / Path(blob_name).name
        source_path.write_bytes(source[0])
        try:
            result = ingest(db, source_path)
        except Exception as exc:
            failure = dict(status='failed', input_blob=blob_name, error=str(exc))
            if db.exists():
                conn = connect(db)
                try:
                    failure['quarantine'] = [dict(row) for row in conn.execute('SELECT * FROM quarantine')]
                finally:
                    conn.close()
            store.write_new(f'audit/{snapshot_id}/failure.json', encode(failure))
            raise
        if result['status'] == 'skipped':
            store.write_new(f'audit/{snapshot_id}/replay.json', encode(result))
            return dict(status='skipped', snapshot=head, run=result)
        output = tmp / 'gold'
        manifest = export_snapshot(db, output)
        prefix = f'snapshots/{snapshot_id}'
        for path in sorted(output.iterdir()):
            store.write_new(f'{prefix}/gold/{path.name}', path.read_bytes())
        database_blob = f'{prefix}/warehouse.sqlite'
        store.write_new(database_blob, db.read_bytes())
        next_head = dict(schema_version=1, snapshot_id=snapshot_id, database_blob=database_blob,
                         outputs_prefix=f'{prefix}/gold/', input_blob=blob_name,
                         run=result, kpis=manifest['kpis'])
        store.compare_and_swap('state/HEAD.json', encode(next_head), expected_etag)
        return dict(status='committed', snapshot=next_head, run=result)
