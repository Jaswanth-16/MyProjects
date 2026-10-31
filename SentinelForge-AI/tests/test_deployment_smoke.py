from pathlib import Path
from fastapi.testclient import TestClient
from sentinelforge.main import InMemoryStore, create_app


def test_dashboard_html():
    api = TestClient(create_app(store=InMemoryStore()))
    response = api.get("/dashboard")
    assert response.status_code == 200
    assert "SentinelForge AI" in response.text
    assert "Refresh findings" in response.text


def test_missing_and_malformed_imports(tmp_path):
    from sentinelforge.scanners import ScannerImportError, load_local_report
    import pytest
    with pytest.raises(ScannerImportError):
        load_local_report("semgrep", tmp_path / "missing.json", "fixture")
    invalid = tmp_path / "bad.json"
    invalid.write_text("{not json", encoding="utf-8")
    with pytest.raises(ScannerImportError):
        load_local_report("semgrep", invalid, "fixture")


def test_postgres_optional_module_import():
    from sentinelforge.postgres import PostgresStore
    assert PostgresStore.__name__ == "PostgresStore"
