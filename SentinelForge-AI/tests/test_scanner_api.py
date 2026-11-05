from fastapi.testclient import TestClient
from sentinelforge.main import InMemoryStore, create_app


def test_semgrep_report_import(monkeypatch):
    monkeypatch.setenv("SENTINELFORGE_API_TOKEN", "test-token")
    api = TestClient(create_app(store=InMemoryStore()))
    report = {"results": [{"check_id": "python.test", "path": "sample.py",
               "start": {"line": 4}, "extra": {"severity": "ERROR", "message": "Synthetic match"}}]}
    endpoint = "/scanner-reports/semgrep?authorized_scope=fixture"
    assert api.post(endpoint, json=report).status_code == 401
    headers = {"Authorization": "Bearer test-token"}
    response = api.post(endpoint, json=report, headers=headers)
    assert response.status_code == 201
    assert response.json()[0]["severity"] == "high"
    assert api.post(endpoint, json=report, headers=headers).json()[0]["id"] == response.json()[0]["id"]
    assert len(api.get("/findings", headers=headers).json()) == 1


def test_invalid_scanner_report():
    api = TestClient(create_app(store=InMemoryStore()))
    assert api.post("/scanner-reports/unknown?authorized_scope=fixture", json={}).status_code == 422
    assert api.post("/scanner-reports/semgrep?authorized_scope=fixture", json={"results": [None]}).status_code == 422
    assert api.get("/dashboard").status_code == 200
