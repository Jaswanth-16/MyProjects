"""Real Azure Blob SDK requests against local Azurite; no managed identity.

Set TRANSITPULSE_TEST_AZURITE=1 after starting loopback Azurite with telemetry disabled.
The key below is the public emulator fixture key from the Azurite documentation.
"""
import json,os,unittest,uuid
from function_app import AzureBlobStore
from azure.storage.blob import BlobServiceClient
from azure.core.exceptions import ResourceExistsError
from transitpulse.cloud import ConcurrentPublishError,process_remote
from transitpulse.pipeline import QualityGateError
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tests'))
from test_pipeline import trip
CONNECTION='DefaultEndpointsProtocol=http;AccountName=devstoreaccount1;AccountKey=Eby8vdM02xNOcqFlqUwJPLlmEtlCDXJ1OUzFT50uSRZ6IFsuFq2UVErCz4I6tq/K1SZFPTOtr/KBHBeksoGMGw==;BlobEndpoint=http://127.0.0.1:10000/devstoreaccount1;'
@unittest.skipUnless(os.environ.get('TRANSITPULSE_TEST_AZURITE')=='1','Azurite opt-in required')
class AzuriteTests(unittest.TestCase):
    def setUp(self):
        self.client=BlobServiceClient.from_connection_string(CONNECTION,retry_total=0,connection_timeout=5,read_timeout=5)
        self.container=self.client.get_container_client('transitpulse-test-'+uuid.uuid4().hex)
        self.container.create_container();self.store=AzureBlobStore(self.container)
    def tearDown(self):self.container.delete_container();self.client.close()
    def batch(self,name,records):
        key='bronze/audit/'+name+'.jsonl';self.store.write_new(key,('\n'.join(json.dumps(r)for r in records)+'\n').encode());return key
    def test_publish_delta_and_replay(self):
        first=self.batch('initial',[trip()]);self.assertEqual(process_remote(self.store,first)['status'],'committed')
        second=self.batch('delta',[trip(trip_id='T2')]);result=process_remote(self.store,second)
        self.assertEqual(result['snapshot']['kpis']['scheduled_trips'],2)
        head=self.store.read('state/HEAD.json',65536)
        self.assertEqual(process_remote(self.store,second)['status'],'skipped')
        self.assertEqual(self.store.read('state/HEAD.json',65536),head)
        self.assertIsNotNone(self.store.read(result['snapshot']['database_blob'],50*1024*1024))
    def test_stale_etag_and_creation_conflict(self):
        self.store.compare_and_swap('state/HEAD.json',b'first',None);_,etag=self.store.read('state/HEAD.json',100)
        self.store.compare_and_swap('state/HEAD.json',b'new',etag)
        with self.assertRaises(ConcurrentPublishError):self.store.compare_and_swap('state/HEAD.json',b'stale',etag)
        with self.assertRaises(ConcurrentPublishError):self.store.compare_and_swap('state/HEAD.json',b'overwrite',None)
        self.assertEqual(self.store.read('state/HEAD.json',100)[0],b'new')
    def test_immutable_write_and_download_limit(self):
        self.store.write_new('fixture.json',b'12345')
        with self.assertRaises(ResourceExistsError):self.store.write_new('fixture.json',b'changed')
        with self.assertRaises(ValueError):self.store.read('fixture.json',4)
        self.assertIsNone(self.store.read('missing.json',100))
    def test_failed_quality_gate_keeps_head_and_writes_audit(self):
        process_remote(self.store,self.batch('initial',[trip()]));head=self.store.read('state/HEAD.json',65536)
        with self.assertRaises(QualityGateError):process_remote(self.store,self.batch('bad',[trip(passengers=-1)]))
        self.assertEqual(self.store.read('state/HEAD.json',65536),head)
        self.assertTrue(any(b.name.endswith('failure.json')for b in self.container.list_blobs(name_starts_with='audit/')))
if __name__=='__main__':unittest.main()
