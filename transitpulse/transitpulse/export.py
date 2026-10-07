"""Export a consistent SQL read snapshot to CSV, JSON and an offline dashboard."""

import csv
import hashlib
import json
from pathlib import Path

from .pipeline import connect
from .report import dashboard_html, preview_svg

TABLES = {
    'fact_trip': 'SELECT * FROM fact_trip ORDER BY trip_id',
    'dim_route': 'SELECT * FROM dim_route ORDER BY route_id',
    'dim_date': 'SELECT * FROM dim_date ORDER BY date_key',
    'route_daily': 'SELECT * FROM route_daily ORDER BY service_date, route_id',
    'quarantine': 'SELECT * FROM quarantine ORDER BY run_id, line_number',
}


def export_snapshot(db_path, output_dir):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    if any(output_dir.iterdir()):
        raise FileExistsError('export destination must be empty (snapshots are immutable)')
    conn = connect(db_path)
    try:
        conn.execute('BEGIN')
        for name, query in TABLES.items():
            cursor = conn.execute(query)
            with (output_dir / f'{name}.csv').open('w', encoding='utf-8', newline='') as handle:
                writer = csv.writer(handle)
                writer.writerow([column[0] for column in cursor.description])
                writer.writerows(cursor)
        kpis = dict(conn.execute('SELECT * FROM kpi_summary').fetchone())
        daily = [dict(row) for row in conn.execute(TABLES['route_daily'])]
        routes = [dict(row) for row in conn.execute(TABLES['dim_route'])]
        audits = [dict(row) for row in conn.execute('SELECT * FROM run_audit ORDER BY started_at_utc, run_id')]
        watermarks = [dict(row) for row in conn.execute(
            'SELECT route_id, MAX(updated_at_utc) AS max_updated_at_utc FROM fact_trip GROUP BY route_id ORDER BY route_id'
        )]
        conn.commit()
    finally:
        conn.close()
    for name, value in [('kpis', kpis), ('run_audit', audits), ('watermarks', watermarks)]:
        (output_dir / f'{name}.json').write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8')
    (output_dir / 'dashboard.html').write_text(dashboard_html(daily, routes), encoding='utf-8')
    (output_dir / 'preview.svg').write_text(preview_svg(kpis, daily, routes), encoding='utf-8')
    hashes = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(output_dir.iterdir())}
    manifest = dict(schema_version=1, synthetic_demo=True, kpis=kpis, files=hashes)
    (output_dir / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
    return manifest
