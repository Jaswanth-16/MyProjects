"""Opt-in paid/free-plan inference checks. A fallback is NEVER a live pass.

Run from the repository root. Uses synthetic fixtures only and prints no credentials.
Missing configuration exits 2; provider/fallback/quality failures exit 1.
"""
import argparse,json,os,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
for project in ['loglens','opsevidence','pipelinecopilot']:sys.path.insert(0,str(ROOT/project))
from loglens.core import analyse
from opsevidence.agent import investigate
from pipelinecopilot.core import Assistant

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--provider',choices=['groq','azure','claude'],default='groq')
    p.add_argument('--interval',type=float,default=5,help='Seconds between cases, 0-60; no retries')
    args=p.parse_args()
    if not 0<=args.interval<=60:p.error('interval must be between 0 and 60')
    names={'groq':['GROQ_API_KEY','GROQ_MODEL'],'claude':['ANTHROPIC_API_KEY','ANTHROPIC_MODEL'],'azure':['AZURE_OPENAI_BASE_URL','AZURE_OPENAI_API_KEY','AZURE_OPENAI_DEPLOYMENT','PIPELINECOPILOT_AZURE_BASE_URL','PIPELINECOPILOT_AZURE_API_KEY','PIPELINECOPILOT_AZURE_DEPLOYMENT']}[args.provider]
    missing=[name for name in names if not os.environ.get(name)]
    if missing:
        print(json.dumps({'status':'blocked','reason':'missing_configuration','missing_variables':missing,'live_calls':0},indent=2));return 2
    report=[]
    for code in ['AuthorizationPermissionMismatch','SqlTimeout']:
        start=time.perf_counter();result=analyse('Pipeline: demo\nActivity: copy\nErrorCode: '+code,args.provider)
        passed=result['mode']==args.provider and not result['warning'] and result['summary']['error_code']==code
        report.append({'project':'LogLens','case':code,'pass':passed,'mode':result['mode'],'warning':result['warning'],'usage':result['usage'],'elapsed_seconds':round(time.perf_counter()-start,2)})
        time.sleep(args.interval)
    for run_id in ['run-0408','run-0420']:
        result=investigate(run_id,'What failed, what does recent history show and which check is supported?',args.provider)
        report.append({'project':'OpsEvidence','case':run_id,'pass':result['mode']==args.provider and not result['warning'] and result['status']=='supported','mode':result['mode'],'warning':result['warning'],'metrics':result['metrics']})
        time.sleep(args.interval)
    if args.provider!='claude':
        assistant=Assistant(use_llm=True,provider=args.provider)
        for code,expected in [('SqlTimeout','sql-timeout'),('AuthorizationPermissionMismatch','storage-access')]:
            result=assistant.ask({'question':'What should I check?','log':code})
            report.append({'project':'PipelineCopilot','case':code,'pass':result['mode']=='llm' and not result['warning'] and expected in [c['id']for c in result['citations']],'mode':result['mode'],'warning':result['warning']})
            time.sleep(args.interval)
    print(json.dumps({'provider':args.provider,'status':'pass' if all(r['pass']for r in report)else 'fail','scope':'Small synthetic smoke suite; not a semantic quality or production accuracy benchmark','results':report},indent=2))
    return 0 if all(r['pass']for r in report)else 1
if __name__=='__main__':raise SystemExit(main())
