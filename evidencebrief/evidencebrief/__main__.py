import argparse
import json
import os
from pathlib import Path
from evidencebrief.core import load_corpus, Retriever, answer
from evidencebrief.provider import GroqClient

parser = argparse.ArgumentParser(description="Evidence-grounded business brief assistant")
parser.add_argument("--corpus", default="corpus")
parser.add_argument("--question", required=True)
parser.add_argument("--provider", choices=["offline", "groq"], default="offline")
parser.add_argument("--output", help="Optional fresh JSON result file")
args = parser.parse_args()
if args.output and Path(args.output).exists():
    parser.error("Output exists; choose a new path")
chunks, rejected = load_corpus(args.corpus)
client = GroqClient(os.environ.get("GROQ_API_KEY"), os.environ.get("GROQ_MODEL")) if args.provider == "groq" else None
result = answer(args.question, Retriever(chunks), client)
result["excluded_suspicious_paragraphs"] = rejected
text = json.dumps(result, indent=2)
if args.output:
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    Path(args.output).write_text(text + "\n")
print(text)
if result["status"] == "rejected":
    raise SystemExit(2)
