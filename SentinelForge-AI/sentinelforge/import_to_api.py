"""Local defensive report importer. Does not execute security scanners."""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from sentinelforge.scanners import load_local_report


def main() -> int:
    parser = argparse.ArgumentParser(description="Import an authorized local scanner report")
    parser.add_argument("scanner", choices=("semgrep", "trivy", "checkov"))
    parser.add_argument("report", type=Path)
    parser.add_argument("--scope", required=True)
    parser.add_argument("--url", default="http://127.0.0.1:8000")
    args = parser.parse_args()
    if args.url.rstrip("/") not in ("http://127.0.0.1:8000", "http://localhost:8000"):
        parser.error("Only the local development API at port 8000 is supported")
    findings = load_local_report(args.scanner, args.report, args.scope)
    if len(findings) > 1000:
        parser.error("Report exceeds the 1000-finding limit")
    token = os.getenv("SENTINELFORGE_API_TOKEN")
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = "Bearer " + token
    query = urlencode({"authorized_scope": args.scope})
    request = Request(args.url.rstrip("/") + "/scanner-reports/" + args.scanner + "?" + query,
                      data=args.report.read_bytes(), headers=headers, method="POST")
    try:
        with urlopen(request, timeout=30) as response:
            result = json.load(response)
    except (HTTPError, URLError) as exc:
        parser.exit(1, f"Import failed: {exc}\n")
    print(f"Imported {len(result)} findings ({len(findings)} parsed)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
