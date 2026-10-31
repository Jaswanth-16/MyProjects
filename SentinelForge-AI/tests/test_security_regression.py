"""Basic security regression tests for the local API."""
from fastapi.testclient import TestClient
from sentinelforge.main import InMemoryStore, create_app


def test_auth_guard_covers_import_and_investigation(monkeypatch):
    monkeypatch.setenv("SENTINELFORGE_API_TOKEN", "secret-for-tests")
    api = TestClient(create_app(store=InMemoryStore()))
    report = {"results": []}
    assert api.post("/scanner-reports/semgrep?authorized_scope=fixture", json=report).status_code == 401
    assert api.get("/findings/missing/investigation").status_code == 401
    assert api.get("/findings/missing/investigation",
                   headers={"Authorization": "Bearer secret-for-tests"}).status_code == 404


def test_input_validation_blocks_oversized_evidence(monkeypatch):
    monkeypatch.delenv("SENTINELFORGE_API_TOKEN", raising=False)
    api = TestClient(create_app(store=InMemoryStore()))
    payload = {"source": "fixture", "rule_id": "R1", "resource": "a.py",
               "severity": "high", "title": "Synthetic", "evidence": "X" * 4001,
               "recommendation": "Review", "authorized_scope": "fixture"}
    assert api.post("/findings", json=payload).status_code == 422
