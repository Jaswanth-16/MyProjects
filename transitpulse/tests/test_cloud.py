import json
import unittest

from transitpulse.cloud import ConcurrentPublishError, process_remote
from transitpulse.pipeline import QualityGateError
from test_pipeline import trip


class MemoryStore:
    def __init__(self):
        self.data = {}
        self.versions = {}
        self.fail_on = None
        self.conflict = False

    def read(self, key, limit):
        if key not in self.data:
            return None
        if len(self.data[key]) > limit:
            raise ValueError('object exceeds size limit')
        return self.data[key], str(self.versions[key])

    def write_new(self, key, value):
        if self.fail_on and self.fail_on in key:
            raise OSError('injected upload failure')
        if key in self.data:
            raise FileExistsError(key)
        self.data[key] = value
        self.versions[key] = 1

    def compare_and_swap(self, key, value, expected_etag):
        version = str(self.versions[key]) if key in self.data else None
        if self.conflict or version != expected_etag:
            raise ConcurrentPublishError('injected competing writer')
        self.data[key] = value
        self.versions[key] = self.versions.get(key, 0) + 1

    def batch(self, name, records):
        key = f'bronze/demo/{name}.jsonl'
        self.write_new(key, ('\n'.join(json.dumps(row) for row in records) + '\n').encode())
        return key


class CloudTests(unittest.TestCase):
    def setUp(self):
        self.store = MemoryStore()

    def first(self):
        return process_remote(self.store, self.store.batch('initial', [trip()]))

    def test_success_publishes_manifest_after_every_artifact_exists(self):
        result = self.first()
        head = json.loads(self.store.data['state/HEAD.json'])
        self.assertEqual(result['status'], 'committed')
        self.assertIn(head['database_blob'], self.store.data)
        self.assertIn(head['outputs_prefix'] + 'fact_trip.csv', self.store.data)
        self.assertEqual(head['kpis']['scheduled_trips'], 1)

    def test_replay_preserves_committed_head_and_fact_count(self):
        self.first()
        head = self.store.read('state/HEAD.json', 65536)
        result = process_remote(self.store, 'bronze/demo/initial.jsonl')
        self.assertEqual(result['status'], 'skipped')
        self.assertEqual(self.store.read('state/HEAD.json', 65536), head)

    def test_delta_load_restores_prior_state(self):
        self.first()
        result = process_remote(self.store, self.store.batch('delta', [trip(trip_id='T2')]))
        self.assertEqual(result['snapshot']['kpis']['scheduled_trips'], 2)

    def test_upload_failure_leaves_head_unchanged_and_retry_recovers(self):
        self.first()
        head = self.store.read('state/HEAD.json', 65536)
        key = self.store.batch('delta', [trip(trip_id='T2')])
        self.store.fail_on = 'warehouse.sqlite'
        with self.assertRaises(OSError):
            process_remote(self.store, key)
        self.assertEqual(self.store.read('state/HEAD.json', 65536), head)
        self.store.fail_on = None
        self.assertEqual(process_remote(self.store, key)['snapshot']['kpis']['scheduled_trips'], 2)

    def test_concurrent_publish_cannot_overwrite_a_newer_head(self):
        self.first()
        head = self.store.read('state/HEAD.json', 65536)
        self.store.conflict = True
        with self.assertRaises(ConcurrentPublishError):
            process_remote(self.store, self.store.batch('delta', [trip(trip_id='T2')]))
        self.assertEqual(self.store.read('state/HEAD.json', 65536), head)

    def test_quality_failure_retains_prior_snapshot_and_creates_audit(self):
        self.first()
        head = self.store.read('state/HEAD.json', 65536)
        with self.assertRaises(QualityGateError):
            process_remote(self.store, self.store.batch('bad', [trip(passengers=-1)]))
        self.assertEqual(self.store.read('state/HEAD.json', 65536), head)
        self.assertTrue(any(key.endswith('failure.json') for key in self.store.data))

    def test_missing_database_fails_closed(self):
        self.first()
        head = json.loads(self.store.data['state/HEAD.json'])
        del self.store.data[head['database_blob']]
        with self.assertRaisesRegex(FileNotFoundError, 'refusing to reset'):
            process_remote(self.store, 'bronze/demo/initial.jsonl')

    def test_arbitrary_blob_paths_are_rejected(self):
        for name in ['state/HEAD.json', 'https://example.com/data', 'bronze/../input.jsonl', '../input.jsonl']:
            with self.subTest(name=name), self.assertRaises(ValueError):
                process_remote(self.store, name)


if __name__ == '__main__':
    unittest.main()
