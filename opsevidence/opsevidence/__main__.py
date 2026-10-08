import argparse,json
from .agent import investigate
from .tools import Tools
from .contracts import ContractError

def main():
    p=argparse.ArgumentParser(description='OpsEvidence: bounded read-only incident agent lab')
    sub=p.add_subparsers(dest='command',required=True)
    sub.add_parser('list');sub.add_parser('demo')
    a=sub.add_parser('investigate');a.add_argument('incident_id');a.add_argument('--question',default='What failed, what does the history show, and what should I check?');a.add_argument('--provider',choices=['offline','azure','claude'],default='offline')
    s=sub.add_parser('serve');s.add_argument('--port',type=int,default=8767);s.add_argument('--provider',choices=['offline','azure','claude'],default='offline')
    args=p.parse_args()
    if args.command=='serve':
        from .server import serve
        serve(args.port,args.provider);return
    try:
        if args.command=='list':out=Tools.incidents()
        elif args.command=='demo':out=[investigate(r['id'],'What failed and what checks are supported?')for r in Tools.incidents()[:5]]
        else:out=investigate(args.incident_id,args.question,args.provider)
        print(json.dumps(out,indent=2))
    except ContractError as exc:p.error(str(exc))
if __name__=='__main__':main()
