from copy import deepcopy
import csv
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest

from transitpulse.export import export_snapshot
from transitpulse.generate import generate, write_jsonl
from transitpulse.pipeline import QualityGateError, connect, ingest


def trip(**changes):
    row = dict(trip_id='T1', route_id='R01', scheduled_departure_utc='2026-01-01T09:00:00Z',
               scheduled_arrival_utc='2026-01-01T10:00:00Z', actual_arrival_utc='2026-01-01T10:05:00Z',
               status='completed', passengers=20, capacity=40, revenue_paise=60_000,
               updated_at_utc='2026-01-01T11:00:00Z')
    row.update(changes)
    return row


class PipelineTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.db = self.root / 'test.sqlite'
        self.sequence = 0

    def load(self, records, **kwargs):
        self.sequence += 1
        path = self.root / f'batch-{self.sequence}.jsonl'
        write_jsonl(path, records)
        return ingest(self.db, path, **kwargs)

    def query(self, sql):
        with sqlite3.connect(self.db) as conn:
            return conn.execute(sql).fetchall()

    def test_first_load_and_exact_batch_replay(self):
        self.assertEqual(self.load([trip()])['inserted'], 1)
        self.assertEqual(self.load([trip()])['status'], 'skipped')
        self.assertEqual(self.query('SELECT COUNT(*) FROM fact_trip'), [(1,)])
        self.assertEqual(self.query('SELECT COUNT(*) FROM ingested_batch'), [(1,)])

    def test_reformatted_batch_deduplicates_semantic_rows(self):
        self.load([trip()])
        path = self.root / 'pretty.jsonl'
        path.write_text(json.dumps(trip(), separators=(',', ':')) + '\n')
        self.assertEqual(ingest(self.db, path)['unchanged'], 1)

    def test_late_correction_updates_existing_trip(self):
        self.load([trip()])
        result = self.load([trip(passengers=25, updated_at_utc='2026-02-10T11:00:00Z')])
        self.assertEqual(result['updated'], 1)
        self.assertEqual(self.query('SELECT passengers FROM fact_trip'), [(25,)])

    def test_old_version_cannot_overwrite_correction(self):
        self.load([trip(passengers=25, updated_at_utc='2026-02-10T11:00:00Z')])
        self.assertEqual(self.load([trip()])['stale'], 1)
        self.assertEqual(self.query('SELECT passengers FROM fact_trip'), [(25,)])

    def test_unseen_old_trip_is_not_lost_to_global_watermark(self):
        self.load([trip(updated_at_utc='2026-03-10T11:00:00Z')])
        self.assertEqual(self.load([trip(trip_id='LATE')])['inserted'], 1)

    def test_equal_version_conflict_is_quarantined(self):
        self.load([trip()])
        result = self.load([trip(passengers=21)], max_reject_ratio=1)
        self.assertEqual(result['rejected'], 1)
        self.assertEqual(self.query('SELECT passengers FROM fact_trip'), [(20,)])
        self.assertIn('version conflict', self.query('SELECT reason FROM quarantine')[0][0])

    def test_quality_gate_rolls_back_valid_rows_and_batch_ledger(self):
        with self.assertRaises(QualityGateError):
            self.load([trip(), trip(trip_id='BAD', passengers=-1)])
        self.assertEqual(self.query('SELECT COUNT(*) FROM fact_trip'), [(0,)])
        self.assertEqual(self.query('SELECT COUNT(*) FROM ingested_batch'), [(0,)])
        self.assertEqual(self.query('SELECT status FROM run_audit'), [('failed',)])
        self.assertEqual(self.query('SELECT COUNT(*) FROM quarantine'), [(1,)])
        metrics = json.loads(self.query('SELECT metrics_json FROM run_audit')[0][0])
        self.assertEqual(metrics['inserted'], 0)
        self.assertEqual(metrics['attempted_inserted'], 1)

    def test_exact_five_percent_rejections_are_allowed(self):
        rows = [trip(trip_id=f'T{i}') for i in range(19)] + [trip(trip_id='BAD', capacity=0)]
        result = self.load(rows)
        self.assertEqual((result['inserted'], result['rejected']), (19, 1))

    def test_database_failure_rolls_back_batch_and_is_audited(self):
        conn = connect(self.db)
        conn.execute("CREATE TRIGGER fail_second BEFORE INSERT ON fact_trip WHEN NEW.trip_id='T2' BEGIN SELECT RAISE(ABORT, 'injected failure'); END")
        conn.close()
        with self.assertRaises(sqlite3.IntegrityError):
            self.load([trip(), trip(trip_id='T2')])
        self.assertEqual(self.query('SELECT COUNT(*) FROM fact_trip'), [(0,)])
        self.assertEqual(self.query('SELECT COUNT(*) FROM ingested_batch'), [(0,)])
        self.assertEqual(self.query('SELECT status FROM run_audit'), [('failed',)])

    def test_kpi_denominators_and_integer_money(self):
        self.load([trip(), trip(trip_id='T2', actual_arrival_utc='2026-01-01T10:06:00Z'),
                   trip(trip_id='T3', status='cancelled', actual_arrival_utc=None, passengers=0, revenue_paise=0)])
        manifest = export_snapshot(self.db, self.root / 'export')
        kpis = manifest['kpis']
        self.assertEqual(kpis['on_time_pct'], 50)
        self.assertEqual(kpis['cancellation_pct'], 33.33)
        self.assertEqual(kpis['load_factor_pct'], 50)
        self.assertEqual(kpis['revenue_paise'], 120_000)
        self.assertEqual(kpis['avg_delay_minutes'], 5.5)
        with (self.root / 'export/fact_trip.csv').open() as handle:
            self.assertEqual(len(list(csv.DictReader(handle))), 3)

    def test_no_completed_trips_produces_null_rates(self):
        self.load([trip(status='cancelled', actual_arrival_utc=None, passengers=0, revenue_paise=0)])
        kpis = export_snapshot(self.db, self.root / 'export')['kpis']
        self.assertIsNone(kpis['on_time_pct'])
        self.assertIsNone(kpis['load_factor_pct'])

    def test_malformed_json_is_quarantined_with_line_number(self):
        path = self.root / 'broken.jsonl'
        path.write_text(json.dumps(trip()) + '\n{broken\n')
        result = ingest(self.db, path, max_reject_ratio=1)
        self.assertEqual(result['rejected'], 1)
        self.assertEqual(self.query('SELECT line_number FROM quarantine'), [(2,)])

    def test_duplicate_json_keys_are_rejected(self):
        path = self.root / 'keys.jsonl'
        path.write_text(json.dumps(trip())[:-1] + ',"passengers":30}\n')
        with self.assertRaises(QualityGateError):
            ingest(self.db, path)

    def test_invalid_contract_values_are_rejected(self):
        bad_changes = [dict(passengers=True), dict(passengers=41), dict(route_id='R99'),
                       dict(updated_at_utc='2026-01-01T11:00:00'), dict(revenue_paise=-10),
                       dict(actual_arrival_utc='2025-01-01T00:00:00Z'), dict(status='planned')]
        for index, changes in enumerate(bad_changes):
            with self.subTest(changes=changes):
                result = self.load([trip(trip_id=f'BAD{index}', **changes)], max_reject_ratio=1)
                self.assertEqual(result['rejected'], 1)

    def test_timezone_equivalent_payload_is_unchanged(self):
        self.load([trip()])
        row = trip(scheduled_departure_utc='2026-01-01T14:30:00+05:30')
        self.assertEqual(self.load([row])['unchanged'], 1)

    def test_export_refuses_to_overwrite_existing_files(self):
        self.load([trip()])
        export_snapshot(self.db, self.root / 'export')
        with self.assertRaises(FileExistsError):
            export_snapshot(self.db, self.root / 'export')

    def test_empty_batch_rejected(self):
        path = self.root / 'empty.jsonl'
        path.write_text('\n')
        with self.assertRaisesRegex(ValueError, 'empty'):
            ingest(self.db, path)

    def test_generator_is_reproducible_and_refuses_overwrite(self):
        generate(self.root / 'a', count=100)
        generate(self.root / 'b', count=100)
        self.assertEqual((self.root / 'a/initial.jsonl').read_bytes(), (self.root / 'b/initial.jsonl').read_bytes())
        with self.assertRaises(FileExistsError):
            generate(self.root / 'a', count=100)


if __name__ == '__main__':
    unittest.main()
