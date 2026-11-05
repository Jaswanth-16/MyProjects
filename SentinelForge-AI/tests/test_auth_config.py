from fastapi.testclient import TestClient

from sentinelforge.main import InMemoryStore, create_app


def test_bearer_auth(monkeypatch):
    monkeypatch.setenv("SENTINELFORGE_API_TOKEN", "unit-test-secret")
    api = TestClient(create_app(store=InMemoryStore()))
    assert api.get("/health").status_code == 200
    assert api.get("/findings").status_code == 401
    assert api.get("/findings", headers={"Authorization": "Bearer wrong"}).status_code == 401
    assert api.get("/findings", headers={"Authorization": "Bearer unit-test-secret"}).status_code == 200


def test_sqlite_configuration(tmp_path, monkeypatch):
    monkeypatch.setenv("SENTINELFORGE_DB_PATH", str(tmp_path / "findings.db"))
    monkeypatch.delenv("SENTINELFORGE_API_TOKEN", raising=False)
    api = TestClient(create_app())
    assert api.get("/findings").json() == []
    assert (tmp_path / "findings.db").exists()
