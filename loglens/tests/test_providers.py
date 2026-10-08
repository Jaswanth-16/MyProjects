import json, os, unittest
from unittest.mock import patch
from loglens.providers import Client, ProviderError
from loglens.contracts import validate, ContractError
from loglens.safety import clean_text

class ProviderTests(unittest.TestCase):
    def client(self,provider,transport):
        env={'GROQ_API_KEY':'test-only','GROQ_MODEL':'test-model','ANTHROPIC_API_KEY':'test-only','ANTHROPIC_MODEL':'test-model','AZURE_OPENAI_BASE_URL':'https://example.openai.azure.com/openai/v1','AZURE_OPENAI_API_KEY':'test-only','AZURE_OPENAI_DEPLOYMENT':'test-deployment'}
        with patch.dict(os.environ,env):return Client(provider,transport)
    def response(self,provider,calls,finish=True):
        if provider=='claude':return {'stop_reason':'tool_use' if finish else 'max_tokens','content':[{'type':'tool_use','id':c['id'],'name':c['name'],'input':c['arguments']}for c in calls],'usage':{'input_tokens':10,'output_tokens':5}}
        return {'choices':[{'finish_reason':'tool_calls' if finish else 'length','message':{'content':None,'tool_calls':[{'id':c['id'],'type':'function','function':{'name':c['name'],'arguments':json.dumps(c['arguments'])}}for c in calls]}}],'usage':{'prompt_tokens':10,'completion_tokens':5}}
    def test_provider_round_trip(self):
        for provider in ['azure','claude','groq']:
            with self.subTest(provider=provider):
                seen=[];call={'id':'c1','name':'read','arguments':{'days':7}}
                def transport(url,headers,payload):seen.append(payload);return self.response(provider,[call])
                client=self.client(provider,transport);messages=[{'role':'user','content':'test'}]
                wire,calls=client.step('system',messages,[{'name':'read','description':'read only','schema':{'type':'object'}}])
                self.assertEqual(calls,[call]);client.append_results(messages,wire,[{'id':'c1','result':{'count':2}}])
                self.assertEqual(messages[-1]['role'],'user' if provider=='claude' else 'tool')
                if provider=='claude':self.assertEqual(messages[-1]['content'][0]['tool_use_id'],'c1')
                else:self.assertEqual(messages[-1]['tool_call_id'],'c1')
                self.assertEqual(client.usage,{'input_tokens':10,'output_tokens':5})
                self.assertEqual(client.requests,1)
                self.assertEqual(client.headers['User-Agent'],'JaswanthPortfolioVerification/1.0')
                if provider=='groq':
                    self.assertEqual(client.url,'https://api.groq.com/openai/v1/chat/completions')
                    self.assertEqual(client.headers['Authorization'],'Bearer test-only')
    def test_truncation_rejected(self):
        for provider in ['azure','claude','groq']:
            client=self.client(provider,lambda *a:self.response(provider,[{'id':'c','name':'read','arguments':{}}],False))
            with self.assertRaises(ProviderError):client.step('s',[],[])
    def test_duplicate_call_ids_rejected(self):
        call={'id':'same','name':'read','arguments':{}}
        for provider in ['azure','claude','groq']:
            client=self.client(provider,lambda *a:self.response(provider,[call,call]))
            with self.assertRaises(ProviderError):client.step('s',[],[])
    def test_malformed_response_rejected(self):
        client=self.client('claude',lambda *a:{'content':[]})
        with self.assertRaises(ProviderError):client.step('s',[],[])
    def test_endpoint_restrictions(self):
        for endpoint in ['http://example.openai.azure.com/openai/v1','https://evil.test/openai/v1','https://example.openai.azure.com/openai/v1?token=x','https://user:pass@example.openai.azure.com/openai/v1']:
            with patch.dict(os.environ,{'AZURE_OPENAI_BASE_URL':endpoint}):
                with self.assertRaises(ProviderError):Client('azure')
    def test_context_limit(self):
        client=self.client('claude',lambda *a:self.fail('must not call transport'))
        with self.assertRaises(ProviderError):client.step('s',[{}]*21,[])
    def test_schema_rejects_boolean_integer_and_extra_fields(self):
        schema={'type':'object','properties':{'days':{'type':'integer','minimum':1,'maximum':28}},'required':['days'],'additionalProperties':False}
        for value in [{'days':True},{'days':0},{'days':29},{'days':7,'sql':'DELETE'},{}]:
            with self.assertRaises(ContractError):validate(value,schema)
    def test_secrets_redacted(self):
        value=clean_text('Authorization: Bearer private-value\nAccountKey=private-key;\nhttps://example.test?a=1&sig=private-sig')
        for secret in ['private-value','private-key','private-sig']:self.assertNotIn(secret,value)
