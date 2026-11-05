from fastapi.testclient import TestClient
from sentinelforge.main import InMemoryStore, create_app
from sentinelforge.tokens import issue_token


SECRET = "integration-test-signing-secret-123456789"


def test_signed_tokens_enforce_scope_isolation(monkeypatch):
    monkeypatch.setenv("SENTINELFORGE_SIGNING_SECRET", SECRET)
    monkeypatch.delenv("SENTINELFORGE_API_TOKEN", raising=False)
    api = TestClient(create_app(store=InMemoryStore()))
    team_a = {"Authorization": "Bearer " + issue_token(SECRET, "alice", "team-a")}
    team_b = {"Authorization": "Bearer " + issue_token(SECRET, "bob", "team-b")}
    payload = {"source": "fixture", "rule_id": "R1", "resource": "file.py",
               "severity": "low", "title": "Synthetic", "evidence": "safe fixture",
               "recommendation": "Review", "authorized_scope": "team-a"}
    assert api.post("/findings", json=payload, headers=team_b).status_code == 403
    created = api.post("/findings", json=payload, headers=team_a)
    assert created.status_code == 201
    finding_id = created.json()["id"]
    assert len(api.get("/findings", headers=team_a).json()) == 1
    assert api.get("/findings", headers=team_b).json() == []
    assert api.get(f"/findings/{finding_id}/investigation", headers=team_b).status_code == 404
    assert api.get("/findings").status_code == 401
