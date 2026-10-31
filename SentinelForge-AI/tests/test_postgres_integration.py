"""PostgreSQL integration tests, opt-in via SENTINELFORGE_TEST_DATABASE_URL."""
import os
import uuid
import pytest

from sentinelforge.main import FindingInput


@pytest.mark.skipif(not os.getenv("SENTINELFORGE_TEST_DATABASE_URL"),
                    reason="PostgreSQL test database not configured")
def test_postgres_round_trip():
    pytest.importorskip("psycopg")
    from sentinelforge.postgres import PostgresStore
    store = PostgresStore(os.environ["SENTINELFORGE_TEST_DATABASE_URL"])
    scope = "test-" + uuid.uuid4().hex
    payload = FindingInput(source="checkov", rule_id="CKV_TEST", resource="synthetic.tf",
                           severity="medium", title="Test", evidence="fixture",
                           recommendation="Review", authorized_scope=scope)
    item = store.add(payload)
    assert store.get(item.id) == item
    assert store.add(payload).id == item.id
    assert any(f.id == item.id for f in store.list())
