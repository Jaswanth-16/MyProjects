"""Import normalized findings from trusted local scanner JSON reports.

This module parses reports only; it never launches scanners or accesses targets.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from sentinelforge.main import FindingInput, Severity


class ScannerImportError(ValueError):
    pass


def _severity(value: str) -> Severity:
    aliases = {"error": "high", "warning": "medium", "note": "low",
               "unknown": "info", "negligible": "info", "moderate": "medium"}
    normalized = aliases.get(str(value).lower(), str(value).lower())
    try:
        return Severity(normalized)
    except ValueError as exc:
        raise ScannerImportError(f"Unsupported severity: {value}") from exc


def _record(source: str, rule: str, resource: str, severity: str,
            title: str, evidence: str, recommendation: str,
            scope: str) -> FindingInput:
    try:
        return FindingInput(source=source, rule_id=rule, resource=resource,
                            severity=_severity(severity), title=title,
                            evidence=evidence, recommendation=recommendation,
                            authorized_scope=scope)
    except ValidationError as exc:
        raise ScannerImportError("Invalid scanner finding") from exc


def parse_semgrep(data: dict[str, Any], scope: str) -> list[FindingInput]:
    output = []
    for item in data.get("results", []):
        extra = item.get("extra", {})
        start = item.get("start", {})
        output.append(_record(
            "semgrep", item.get("check_id", "unknown"),
            item.get("path", "unknown"), extra.get("severity", "info"),
            extra.get("message", "Semgrep finding"),
            f"Line {start.get('line', '?')}; rule {item.get('check_id', 'unknown')}",
            "Review the matched code and apply the rule guidance.", scope))
    return output


def parse_trivy(data: dict[str, Any], scope: str) -> list[FindingInput]:
    output = []
    for result in data.get("Results", []):
        target = result.get("Target", "unknown")
        for vuln in result.get("Vulnerabilities") or []:
            output.append(_record(
                "trivy", vuln.get("VulnerabilityID", "unknown"),
                target, vuln.get("Severity", "info"),
                vuln.get("Title") or vuln.get("VulnerabilityID", "Vulnerability"),
                f"Package: {vuln.get('PkgName', 'unknown')}; installed: {vuln.get('InstalledVersion', 'unknown')}",
                f"Review fixed version: {vuln.get('FixedVersion') or 'not provided'}", scope))
    return output


def parse_checkov(data: dict[str, Any] | list[Any], scope: str) -> list[FindingInput]:
    reports = data if isinstance(data, list) else [data]
    output = []
    for report in reports:
        for item in report.get("results", {}).get("failed_checks", []):
            output.append(_record(
                "checkov", item.get("check_id", "unknown"),
                item.get("file_path") or item.get("resource", "unknown"),
                "medium", item.get("check_name", "Checkov failed check"),
                f"Resource: {item.get('resource', 'unknown')}; check: {item.get('check_id', 'unknown')}",
                "Review the infrastructure configuration against the check guidance.", scope))
    return output


PARSERS = {"semgrep": parse_semgrep, "trivy": parse_trivy, "checkov": parse_checkov}


def parse_report(scanner: str, data: dict[str, Any] | list[Any],
                 authorized_scope: str) -> list[FindingInput]:
    if not authorized_scope.strip():
        raise ScannerImportError("Authorized scope is required")
    if scanner not in PARSERS:
        raise ScannerImportError(f"Unsupported scanner: {scanner}")
    return PARSERS[scanner](data, authorized_scope)


def load_local_report(scanner: str, path: str | Path, scope: str,
                      max_bytes: int = 5_000_000) -> list[FindingInput]:
    """Read a local JSON file explicitly supplied by the operator."""
    file = Path(path)
    if not file.is_file() or file.stat().st_size > max_bytes:
        raise ScannerImportError("Report missing or exceeds size limit")
    try:
        data = json.loads(file.read_text(encoding="utf-8"))
    except (ValueError, UnicodeError) as exc:
        raise ScannerImportError("Report must be valid UTF-8 JSON") from exc
    if not isinstance(data, (dict, list)):
        raise ScannerImportError("Expected JSON object or array")
    return parse_report(scanner, data, scope)
