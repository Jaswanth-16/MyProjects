import json
from fastapi.testclient import TestClient
from sentinelforge.main import InMemoryStore, create_app


def test_audit_metadata_only(tmp_path, monkeypatch):
    destination = tmp_path / "audit.jsonl"
    monkeypatch.setenv("SENTINELFORGE_AUDIT_LOG", str(destination))
    monkeypatch.delenv("SENTINELFORGE_API_TOKEN", raising=False)
    api = TestClient(create_app(store=InMemoryStore()))
    payload = {"source": "semgrep", "rule_id": "R1", "resource": "fixture.py",
               "severity": "low", "title": "Synthetic", "evidence": "PRIVATE-EVIDENCE",
               "recommendation": "Review", "authorized_scope": "local"}
    response = api.post("/findings", json=payload)
    assert response.status_code == 201
    api.get("/findings/" + response.json()["id"] + "/investigation")
    lines = [json.loads(line) for line in destination.read_text().splitlines()]
    assert [line["event"] for line in lines] == ["finding_ingested", "finding_investigated"]
    assert "PRIVATE-EVIDENCE" not in destination.read_text()
