"""Security tests for streamed request bodies without Content-Length."""
from fastapi.testclient import TestClient
from sentinelforge.main import InMemoryStore, create_app


def test_oversized_stream_without_content_length():
    api = TestClient(create_app(store=InMemoryStore()))
    def chunks():
        for _ in range(6):
            yield b"x" * 1_000_000
    response = api.post("/findings", content=chunks(),
                        headers={"content-type": "application/json"})
    assert response.status_code == 413
