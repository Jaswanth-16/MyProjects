import unittest
from loglens.core import analyse,numbered,offline_extract,validate_summary,CODES
from loglens.contracts import ContractError
from loglens.providers import ProviderError
class CoreTests(unittest.TestCase):
    def test_all_eight_codes(self):
        for code,category in CODES.items():
            with self.subTest(code=code):
                answer=analyse('pipeline: demo\nactivity: copy\n'+code)['summary']
                self.assertEqual(answer['category'],category);self.assertEqual(answer['pipeline'],'demo')
    def test_unknown_and_multiple_codes(self):
        for log in ['unrecognised failure','SqlTimeout and LoginFailed']:
            self.assertEqual(analyse(log)['summary']['category'],'unknown')
    def test_credential_free_mode_never_calls_client(self):
        class Forbidden:
            def step(self,*a,**kw):raise AssertionError('offline made a model call')
        self.assertEqual(analyse('SqlTimeout',client=Forbidden())['mode'],'offline')
    def test_input_limits(self):
        for log in ['', 'a'*1001, '\n'.join(['a']*101)]:
            with self.assertRaises(ContractError):numbered(log)
    def test_invented_quote_and_field_rejected(self):
        lines=numbered('pipeline: demo\nSqlTimeout')
        for mutation in ['quote','pipeline','category']:
            answer=offline_extract(lines)
            if mutation=='quote':answer['evidence'][0]['quote']='invented'
            else:answer[mutation]='invented'
            with self.assertRaises(ContractError):validate_summary(answer,lines)
    def test_live_failure_reports_usage_and_fallback(self):
        class Broken:
            usage={'input_tokens':20,'output_tokens':2}
            def step(self,*a,**kw):raise ProviderError('private provider detail')
        result=analyse('SqlTimeout','claude',Broken())
        self.assertEqual(result['mode'],'offline');self.assertEqual(result['usage']['input_tokens'],20)
        self.assertNotIn('private provider detail',result['warning'])
    def test_valid_live_output_for_all_three_providers(self):
        import test_providers
        helper=test_providers.ProviderTests();text='pipeline: demo\nactivity: copy\nSqlTimeout';answer=offline_extract(numbered(text))
        for provider in ['azure','claude','groq']:
            client=helper.client(provider,lambda *a:helper.response(provider,[{'id':'summary','name':'emit_summary','arguments':answer}]))
            result=analyse(text,provider,client)
            self.assertEqual(result['mode'],provider);self.assertIsNone(result['warning']);self.assertEqual(result['summary'],answer)
