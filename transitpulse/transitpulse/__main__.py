"""Run with python -m transitpulse. The local pipeline needs only Python 3.11+."""

import argparse
import json
from pathlib import Path
import sqlite3
import sys
import time
import uuid

from .export import export_snapshot
from .generate import generate
from .pipeline import ingest


def demo(workspace, count, seed):
    workspace = Path(workspace)
    if workspace.exists() and any(workspace.iterdir()):
        raise FileExistsError('workspace is not empty; choose a new path (no files will be deleted)')
    expected = generate(workspace / 'input', count=count, seed=seed)
    db = workspace / 'warehouse.sqlite'
    started = time.perf_counter()
    initial = ingest(db, workspace / 'input/initial.jsonl')
    delta = ingest(db, workspace / 'input/delta.jsonl')
    replay = ingest(db, workspace / 'input/delta.jsonl')
    with sqlite3.connect(db) as conn:
        actual = conn.execute('SELECT COUNT(*) FROM fact_trip').fetchone()[0]
    if actual != expected['expected_unique_trips'] or replay['status'] != 'skipped':
        raise RuntimeError('demo reconciliation failed')
    for field in ('inserted', 'updated', 'unchanged', 'stale', 'rejected'):
        if delta[field] != expected[f'delta_{field}']:
            raise RuntimeError(f'delta reconciliation failed: {field}')
    output = workspace / 'exports' / uuid.uuid4().hex
    manifest = export_snapshot(db, output)
    result = dict(dataset='deterministic synthetic trips', seed=seed, initial=initial, delta=delta, replay=replay,
                  unique_trips=actual, elapsed_seconds=round(time.perf_counter() - started, 4),
                  exports=str(output.resolve()), kpis=manifest['kpis'])
    (workspace / 'demo-results.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    (workspace / 'LATEST.json').write_text(json.dumps({'exports': str(output.resolve())}, indent=2) + '\n', encoding='utf-8')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    d = commands.add_parser('demo', help='generate, load, correct, replay and reconcile synthetic trips')
    d.add_argument('--workspace', default='workspace')
    d.add_argument('--count', type=int, default=10_000)
    d.add_argument('--seed', type=int, default=42)
    g = commands.add_parser('generate', help='create deterministic JSONL input files')
    g.add_argument('--output', required=True)
    g.add_argument('--count', type=int, default=10_000)
    g.add_argument('--seed', type=int, default=42)
    r = commands.add_parser('run', help='incrementally ingest one JSONL batch')
    r.add_argument('--db', required=True)
    r.add_argument('--input', required=True)
    r.add_argument('--max-reject-ratio', type=float, default=0.05)
    e = commands.add_parser('export', help='export committed facts into a new immutable directory')
    e.add_argument('--db', required=True)
    e.add_argument('--output', required=True)
    args = parser.parse_args()
    try:
        if args.command == 'demo':
            result = demo(args.workspace, args.count, args.seed)
        elif args.command == 'generate':
            result = generate(args.output, args.count, args.seed)
        elif args.command == 'run':
            result = ingest(args.db, args.input, args.max_reject_ratio)
        else:
            result = export_snapshot(args.db, args.output)
        print(json.dumps(result, indent=2))
    except Exception as exc:
        print(json.dumps({'status': 'failed', 'error': str(exc)}), file=sys.stderr)
        raise SystemExit(1) from exc


if __name__ == '__main__':
    main()
