from fastapi.testclient import TestClient

from sentinelforge.main import InMemoryStore, create_app


def client():
    return TestClient(create_app(store=InMemoryStore()))


SAMPLE = {
    "source": "checkov",
    "rule_id": "CKV_AZURE_SAMPLE",
    "resource": "fixtures/storage.tf",
    "severity": "high",
    "title": "Storage configuration needs review",
    "evidence": "Synthetic fixture: public access enabled",
    "recommendation": "Disable public access and review policy",
    "authorized_scope": "local-fixtures",
}


def test_health():
    assert client().get("/health").json() == {"status": "ok"}


def test_ingest_list_and_investigate():
    api = client()
    response = api.post("/findings", json=SAMPLE)
    assert response.status_code == 201
    item = response.json()
    assert item["risk_score"] == 80
    assert len(api.get("/findings").json()) == 1
    report = api.get(f"/findings/{item['id']}/investigation").json()
    assert report["provider"] == "deterministic"
    assert report["evidence"] == SAMPLE["evidence"]


def test_idempotency():
    api = client()
    a = api.post("/findings", json=SAMPLE).json()
    b = api.post("/findings", json=SAMPLE).json()
    assert a["id"] == b["id"]
    assert len(api.get("/findings").json()) == 1


def test_invalid_and_missing():
    api = client()
    assert api.post("/findings", json={**SAMPLE, "authorized_scope": " "}).status_code == 422
    assert api.get("/findings/unknown/investigation").status_code == 404


def test_sorted_by_risk():
    api = client()
    api.post("/findings", json={**SAMPLE, "resource": "low", "severity": "low"})
    api.post("/findings", json={**SAMPLE, "resource": "critical", "severity": "critical"})
    assert [f["risk_score"] for f in api.get("/findings").json()] == [95, 25]
