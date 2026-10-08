import argparse,json
from pathlib import Path
from .core import analyse
from .contracts import ContractError
ROOT=Path(__file__).resolve().parent.parent

def main():
    p=argparse.ArgumentParser(description='LogLens: beginner structured extraction lab')
    sub=p.add_subparsers(dest='command',required=True)
    sub.add_parser('demo')
    a=sub.add_parser('analyse');a.add_argument('log',type=Path);a.add_argument('--provider',choices=['offline','azure','claude'],default='offline')
    s=sub.add_parser('serve');s.add_argument('--port',type=int,default=8766);s.add_argument('--provider',choices=['offline','azure','claude'],default='offline')
    args=p.parse_args()
    if args.command=='serve':
        from .server import serve
        serve(args.port,args.provider);return
    try:
        if args.command=='demo':
            out=[{'sample':f.name,'result':analyse(f.read_text())}for f in sorted((ROOT/'examples').glob('*.log'))]
        else:
            if args.log.stat().st_size>16000:raise ContractError('Log file exceeds 16000 bytes')
            out=analyse(args.log.read_text(),args.provider)
        print(json.dumps(out,indent=2))
    except (ContractError,OSError,UnicodeError) as exc:p.error(str(exc))
if __name__=='__main__':main()
