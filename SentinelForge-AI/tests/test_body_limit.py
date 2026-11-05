from fastapi.testclient import TestClient
from sentinelforge.main import InMemoryStore, create_app


def test_request_body_limit_rejects_large_payload():
    api = TestClient(create_app(store=InMemoryStore()))
    response = api.post("/findings", content=b"x" * 5_000_001,
                        headers={"content-type": "application/json"})
    assert response.status_code == 413


def test_normal_request_body_still_parses():
    api = TestClient(create_app(store=InMemoryStore()))
    payload = {"source": "fixture", "rule_id": "R1", "resource": "demo.py",
               "severity": "low", "title": "Synthetic", "evidence": "fixture",
               "recommendation": "Review", "authorized_scope": "local"}
    assert api.post("/findings", json=payload).status_code == 201
