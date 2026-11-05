import csv
import io

from fastapi.testclient import TestClient
from sentinelforge.main import InMemoryStore, create_app
from sentinelforge.tokens import issue_token


SECRET = "csv-export-test-signing-secret-123456"


def test_csv_export_is_scope_filtered_and_formula_safe(monkeypatch):
    monkeypatch.setenv("SENTINELFORGE_SIGNING_SECRET", SECRET)
    monkeypatch.delenv("SENTINELFORGE_API_TOKEN", raising=False)
    api = TestClient(create_app(store=InMemoryStore()))
    a = {"Authorization": "Bearer " + issue_token(SECRET, "alice", "a")}
    b = {"Authorization": "Bearer " + issue_token(SECRET, "bob", "b")}
    for scope, headers, title in (("a", a, "=2+2"), ("b", b, "Private B")):
        payload = {"source": "fixture", "rule_id": title, "resource": "file.py",
                   "severity": "low", "title": title, "evidence": "fixture",
                   "recommendation": "Review", "authorized_scope": scope}
        assert api.post("/findings", json=payload, headers=headers).status_code == 201
    assert api.get("/findings/export.csv").status_code == 401
    response = api.get("/findings/export.csv", headers=a)
    assert response.status_code == 200
    assert response.headers["cache-control"] == "no-store"
    rows = list(csv.DictReader(io.StringIO(response.text)))
    assert len(rows) == 1
    assert rows[0]["authorized_scope"] == "a"
    assert rows[0]["title"] == "'=2+2"
    assert "Private B" not in response.text
