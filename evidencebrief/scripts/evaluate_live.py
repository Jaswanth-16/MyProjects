"""Explicit live smoke test. Never stores the API key or falls back offline."""
import argparse
import getpass
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from evidencebrief.core import load_corpus, Retriever, answer
from evidencebrief.provider import GroqClient


class CountedClient:
    def __init__(self, client):
        self.client, self.attempted, self.completed, self.last_error = client, 0, 0, None
        self.last_response = None

    def complete(self, messages):
        self.attempted += 1
        try:
            result = self.client.complete(messages)
            self.last_response = result
            self.completed += 1
            return result
        except (ValueError, RuntimeError) as error:
            self.last_error = {"type": type(error).__name__, "message": str(error)}
            raise


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="openai/gpt-oss-120b")
    parser.add_argument("--output", required=True)
    parser.add_argument("--prompt-key", action="store_true", help="Read key without terminal echo")
    args = parser.parse_args()
    target = Path(args.output)
    if target.exists():
        parser.error("Use a new report path; earlier failures are retained")
    key = getpass.getpass("Groq API key (hidden): ") if args.prompt_key else os.getenv("GROQ_API_KEY")
    provider = CountedClient(GroqClient(key, args.model))
    del key
    retriever = Retriever(load_corpus(ROOT / "corpus")[0])
    cases = json.loads((ROOT / "evaluation/cases.json").read_text())
    checks = []
    for case in cases:
        before = provider.attempted
        provider.last_error = None
        provider.last_response = None
        result = answer(case["question"], retriever, provider)
        passed = result["status"] == case["expected"] and (
            "contains" not in case or any(case["contains"].lower() in c["quote"].lower() for c in result["claims"]))
        checks.append({"question": case["question"], "passed": passed,
                       "api_called": provider.attempted > before,
                       "provider_error": provider.last_error, "result": result})
        if result["status"] == "rejected" and provider.last_response is not None:
            # Test inputs are checked-in synthetic documents. Retain a rejected
            # candidate for debugging instead of rewriting it into a false pass.
            checks[-1]["rejected_candidate"] = provider.last_response
        print(json.dumps({"question": case["question"], "passed": passed,
                          "status": result["status"], "api_called": provider.attempted > before}), flush=True)
    report = {"executed_at_utc": datetime.now(timezone.utc).isoformat(), "model": args.model,
              "mode": "groq_llm", "api_calls_attempted": provider.attempted,
              "api_responses_parsed": provider.completed,
              "passed": sum(c["passed"] for c in checks), "total": len(checks),
              "live_answer_cases_passed": sum(c["passed"] and c["api_called"] for c in checks),
              "local_abstention_cases_passed": sum(c["passed"] and not c["api_called"] for c in checks),
              "checks": checks,
              "limitation": "Small developer-authored synthetic smoke set; not general model accuracy"}
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({k: v for k, v in report.items() if k != "checks"}, indent=2))
    if report["passed"] != report["total"] or report["api_responses_parsed"] < 1:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
