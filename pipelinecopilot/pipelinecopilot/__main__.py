import argparse
import json
from pathlib import Path
from .core import Assistant, DATA
from .safety import InputError

def main():
    p = argparse.ArgumentParser(description='PipelineCopilot: read-only troubleshooting')
    sub = p.add_subparsers(dest='command', required=True)
    ask = sub.add_parser('ask'); ask.add_argument('question'); ask.add_argument('--log', type=Path); ask.add_argument('--llm', action='store_true'); ask.add_argument('--provider',choices=['azure','groq'],default='azure')
    demo = sub.add_parser('demo')
    server = sub.add_parser('serve'); server.add_argument('--port', type=int, default=8765); server.add_argument('--llm', action='store_true'); server.add_argument('--provider',choices=['azure','groq'],default='azure')
    sub.add_parser('evaluate')
    args = p.parse_args()
    if args.command == 'serve':
        from .server import serve
        serve(args.port, args.llm,args.provider); return
    if args.command == 'evaluate':
        from .evaluate import evaluate
        report = evaluate(); print(json.dumps(report, indent=2))
        if report['top1_accuracy'] < .85 or report['abstention_accuracy'] < 1:
            raise SystemExit(1)
        return
    assistant = Assistant(use_llm=getattr(args, 'llm', False),provider=getattr(args,'provider','azure'))
    if args.command == 'demo':
        for case in json.loads((DATA / 'sample_runs.json').read_text()):
            print(json.dumps({'sample': case['name'], 'answer': assistant.ask({'question': case['question'], 'log': case['log']})}, indent=2))
    else:
        try:
            log = ''
            if args.log:
                if args.log.stat().st_size > 16000:
                    raise InputError('Log file exceeds 16000 bytes')
                log = args.log.read_text()
            print(json.dumps(assistant.ask({'question': args.question, 'log': log}), indent=2))
        except (InputError, OSError, UnicodeError) as e:
            p.error(str(e))

if __name__ == '__main__':
    main()
