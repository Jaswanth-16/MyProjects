"""Import local, authorized scanner reports into a JSON findings export."""
from __future__ import annotations

import argparse
import json

from sentinelforge.scanners import load_local_report


def main() -> None:
    parser = argparse.ArgumentParser(description="Normalize local security scanner JSON")
    parser.add_argument("scanner", choices=["semgrep", "trivy", "checkov"])
    parser.add_argument("report", help="Path to local scanner JSON output")
    parser.add_argument("--scope", required=True, help="Authorized asset scope label")
    args = parser.parse_args()
    findings = load_local_report(args.scanner, args.report, args.scope)
    print(json.dumps([finding.model_dump(mode="json") for finding in findings], indent=2))


if __name__ == "__main__":
    main()
