import json

import pytest

from sentinelforge.scanners import ScannerImportError, load_local_report, parse_report


def test_semgrep_normalization():
    report = {"results": [{"check_id": "python.example", "path": "demo.py",
                            "start": {"line": 7},
                            "extra": {"severity": "WARNING", "message": "Review this"}}]}
    items = parse_report("semgrep", report, "local-fixtures")
    assert len(items) == 1
    assert items[0].severity.value == "medium"
    assert items[0].resource == "demo.py"


def test_trivy_normalization():
    report = {"Results": [{"Target": "demo:latest", "Vulnerabilities": [
        {"VulnerabilityID": "CVE-TEST-1", "Severity": "HIGH",
         "PkgName": "demo", "InstalledVersion": "1", "FixedVersion": "2"}]}]}
    items = parse_report("trivy", report, "local-fixtures")
    assert items[0].rule_id == "CVE-TEST-1"
    assert items[0].severity.value == "high"


def test_checkov_normalization():
    report = {"results": {"failed_checks": [
        {"check_id": "CKV_TEST", "file_path": "/main.tf",
         "resource": "test.demo", "check_name": "Review config"}]}}
    items = parse_report("checkov", report, "local-fixtures")
    assert items[0].source == "checkov"
    assert items[0].severity.value == "medium"


def test_local_report(tmp_path):
    path = tmp_path / "report.json"
    path.write_text(json.dumps({"results": []}))
    assert load_local_report("semgrep", path, "test") == []


def test_reject_missing_scope_and_unknown_scanner():
    with pytest.raises(ScannerImportError):
        parse_report("semgrep", {}, " ")
    with pytest.raises(ScannerImportError):
        parse_report("unknown", {}, "local")


def test_reject_large_and_invalid_reports(tmp_path):
    path = tmp_path / "bad.json"
    path.write_text("{invalid")
    with pytest.raises(ScannerImportError):
        load_local_report("semgrep", path, "local")
    path.write_text("x" * 100)
    with pytest.raises(ScannerImportError):
        load_local_report("semgrep", path, "local", max_bytes=20)
