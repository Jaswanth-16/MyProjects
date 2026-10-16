import argparse
import json
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from evidencebrief.core import load_corpus, Retriever, answer

parser = argparse.ArgumentParser()
parser.add_argument("--output", required=True)
args = parser.parse_args()
corpus, excluded = load_corpus(ROOT / "corpus")
retriever = Retriever(corpus)
checks = []
for case in json.loads((ROOT / "evaluation/cases.json").read_text()):
    result = answer(case["question"], retriever)
    passed = result["status"] == case["expected"] and (
        "contains" not in case or any(case["contains"].lower() in c["quote"].lower() for c in result["claims"]))
    checks.append({"question": case["question"], "passed": passed, "result": result})
report = {"mode": "offline_extractive", "passed": sum(c["passed"] for c in checks),
          "total": len(checks), "live_llm_test": "not_executed", "checks": checks,
          "limitation": "Developer-authored synthetic regression set, not a held-out accuracy benchmark"}
target = Path(args.output)
target.parent.mkdir(parents=True, exist_ok=True)
target.write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps({k: v for k, v in report.items() if k != "checks"}, indent=2))
if report["passed"] != report["total"]:
    raise SystemExit(1)
