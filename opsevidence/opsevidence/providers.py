"""Provider-neutral tool calling for Azure OpenAI v1, Claude Messages and Groq.

The HTTP boundary is injectable in tests. No paid request in offline mode.
"""
import json
import os
import re
from urllib.parse import urlsplit
from urllib.request import Request, build_opener, HTTPRedirectHandler
from .contracts import ContractError

class ProviderError(RuntimeError):pass

class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ProviderError('Redirect refused')

def http_post(url, headers, payload):
    data=json.dumps(payload,allow_nan=False).encode()
    if len(data)>150000:raise ProviderError('Provider request exceeds context limit')
    req=Request(url,data=data,headers={**headers,'Content-Type':'application/json'},method='POST')
    try:
        with build_opener(NoRedirect()).open(req,timeout=25) as response:
            raw=response.read(150001)
        if len(raw)>150000:raise ProviderError('Provider response too large')
        return json.loads(raw)
    except ProviderError:raise
    except Exception:raise ProviderError('Provider request failed; check configuration, quota and model capabilities') from None

class Client:
    def __init__(self, provider, transport=http_post):
        if provider not in {'azure','claude','groq'}:raise ProviderError('Choose azure, claude or groq')
        self.provider=provider;self.transport=transport
        self.requests=0;self.usage={'input_tokens':0,'output_tokens':0}
        if provider=='claude':
            self.key=os.environ.get('ANTHROPIC_API_KEY','');self.model=os.environ.get('ANTHROPIC_MODEL','')
            self.url='https://api.anthropic.com/v1/messages'
            self.headers={'x-api-key':self.key,'anthropic-version':'2023-06-01'}
        elif provider=='groq':
            self.key=os.environ.get('GROQ_API_KEY','');self.model=os.environ.get('GROQ_MODEL','')
            self.url='https://api.groq.com/openai/v1/chat/completions'
            self.headers={'Authorization':'Bearer '+self.key}
        else:
            base=os.environ.get('AZURE_OPENAI_BASE_URL','').rstrip('/')
            try:u=urlsplit(base);port=u.port
            except ValueError:raise ProviderError('Invalid Azure endpoint') from None
            if (u.scheme!='https' or not u.hostname or u.username or u.password or u.query or u.fragment
                or port not in (None,443) or u.path!='/openai/v1'
                or not re.fullmatch(r'[a-z0-9-]+\.(?:openai|services\.ai)\.azure\.com',u.hostname)):
                raise ProviderError('Use your Azure HTTPS endpoint ending /openai/v1')
            self.key=os.environ.get('AZURE_OPENAI_API_KEY','');self.model=os.environ.get('AZURE_OPENAI_DEPLOYMENT','')
            self.url=base+'/chat/completions';self.headers={'api-key':self.key}
        self.headers['User-Agent']='JaswanthPortfolioVerification/1.0'
        if not self.key or not self.model:raise ProviderError('Provider API key and model/deployment name are required')

    def step(self, system, messages, tools, force=None):
        if len(messages)>20:raise ProviderError('Conversation limit exceeded')
        if self.provider=='claude':
            payload={'model':self.model,'max_tokens':1200,'system':system,'messages':messages,
                     'tools':[{'name':t['name'],'description':t['description'],'input_schema':t['schema']}for t in tools],
                     'tool_choice':{'type':'tool','name':force} if force else {'type':'any'}}
        else:
            payload={'model':self.model,'max_completion_tokens':1200,'messages':[{'role':'system','content':system}]+messages,
                     'tools':[{'type':'function','function':{'name':t['name'],'description':t['description'],'parameters':t['schema']}}for t in tools],
                     'tool_choice':{'type':'function','function':{'name':force}} if force else 'required'}
        self.requests+=1
        try:
            response=self.transport(self.url,self.headers,payload)
            usage=response.get('usage',{})
            self.usage['input_tokens']+=int(usage.get('input_tokens',usage.get('prompt_tokens',0)))
            self.usage['output_tokens']+=int(usage.get('output_tokens',usage.get('completion_tokens',0)))
            if self.provider=='claude':
                blocks=response['content']
                if response.get('stop_reason')!='tool_use':raise ProviderError('Model did not finish with tool calls')
                calls=[{'id':b['id'],'name':b['name'],'arguments':b['input']}for b in blocks if b['type']=='tool_use']
                wire={'role':'assistant','content':blocks}
            else:
                if response['choices'][0].get('finish_reason')!='tool_calls':raise ProviderError('Model did not finish with tool calls')
                wire=response['choices'][0]['message']
                calls=[{'id':b['id'],'name':b['function']['name'],'arguments':json.loads(b['function']['arguments'])}for b in wire.get('tool_calls',[])]
                wire={'role':'assistant','content':wire.get('content'),'tool_calls':wire['tool_calls']}
            if not 1<=len(calls)<=6 or len({c['id'] for c in calls})!=len(calls):raise ProviderError('Invalid tool-call count or duplicate IDs')
            for call in calls:
                if not isinstance(call['id'],str) or not isinstance(call['name'],str) or not isinstance(call['arguments'],dict):raise ProviderError('Invalid tool call')
            return wire,calls
        except ProviderError:raise
        except Exception:raise ProviderError('Malformed model response') from None

    def append_results(self, messages, wire, results):
        messages.append(wire)
        if self.provider=='claude':
            messages.append({'role':'user','content':[{'type':'tool_result','tool_use_id':r['id'],'content':json.dumps(r['result']), 'is_error':r.get('error',False)}for r in results]})
        else:
            messages.extend({'role':'tool','tool_call_id':r['id'],'content':json.dumps(r['result'])}for r in results)
