import os
import pytest


@pytest.mark.skipif(not os.getenv("SENTINELFORGE_TEST_DATABASE_URL"),
                    reason="PostgreSQL test database not configured")
def test_migrations_are_idempotent():
    from sentinelforge.migrations import apply_migrations
    dsn = os.environ["SENTINELFORGE_TEST_DATABASE_URL"]
    apply_migrations(dsn)
    assert apply_migrations(dsn) == []
