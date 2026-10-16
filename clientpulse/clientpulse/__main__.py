import argparse
import json
from clientpulse.data import generate
from clientpulse.analysis import run

parser = argparse.ArgumentParser(description="Python/SQL EDA and retention modelling")
commands = parser.add_subparsers(dest="command", required=True)
sample = commands.add_parser("sample")
sample.add_argument("--output", required=True)
sample.add_argument("--count", type=int, default=600)
analyse = commands.add_parser("analyse")
analyse.add_argument("--input", required=True)
analyse.add_argument("--output", required=True)
args = parser.parse_args()
if args.command == "sample":
    generate(args.output, count=args.count)
else:
    print(json.dumps(run(args.input, args.output), indent=2))
