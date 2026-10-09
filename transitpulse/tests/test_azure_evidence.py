import importlib.util,json,unittest
from pathlib import Path
from types import SimpleNamespace
spec=importlib.util.spec_from_file_location('collect_azure_evidence',Path(__file__).resolve().parents[1]/'scripts/collect_azure_evidence.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
class EvidenceTests(unittest.TestCase):
    def test_status_only_queries_and_failure_reporting(self):
        seen=[]
        def runner(args,**kw):
            seen.append(args)
            return SimpleNamespace(returncode=0,stdout=json.dumps({'status':'Succeeded' if len(seen)==1 else 'Failed','pipeline':'pl_transitpulse','started':'2026-10-09T00:00:00Z','ended':'2026-10-09T00:01:00Z'}))
        result=module.collect('demo','factory',['one','two'],runner)
        self.assertEqual(result['status'],'fail');self.assertEqual(len(result['runs']),2)
        self.assertEqual(seen[0][1:4],['datafactory','pipeline-run','show'])
        self.assertNotIn('parameters',seen[0][seen[0].index('--query')+1]);self.assertNotIn('run_id',result['runs'][0])
    def test_access_failure_and_duplicate_runs_rejected(self):
        with self.assertRaises(RuntimeError):module.collect('g','f',['one'],lambda *a,**k:SimpleNamespace(returncode=1,stderr='SECRET',stdout=''))
        with self.assertRaises(ValueError):module.collect('g','f',['one','one'],lambda *a,**k:self.fail('must not query'))
