"""Integration backup/restore test using isolated temporary PostgreSQL databases."""
from __future__ import annotations
import os
import shutil
import uuid
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit
import pytest


@pytest.mark.skipif(not os.getenv("SENTINELFORGE_TEST_DATABASE_URL"),
                    reason="PostgreSQL test database not configured")
def test_backup_restore_round_trip(tmp_path):
    if not shutil.which("pg_dump") or not shutil.which("pg_restore"):
        pytest.skip("PostgreSQL client utilities unavailable")
    psycopg = pytest.importorskip("psycopg")
    from psycopg import sql
    from sentinelforge.backup import backup, restore
    from sentinelforge.postgres import PostgresStore
    from sentinelforge.main import FindingInput

    dsn = os.environ["SENTINELFORGE_TEST_DATABASE_URL"]
    parsed = urlsplit(dsn)
    dbname = "sf_restore_" + uuid.uuid4().hex[:12]
    target_dsn = urlunsplit(parsed._replace(path="/" + dbname))
    with psycopg.connect(dsn, autocommit=True) as admin:
        admin.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(dbname)))
    try:
        source = PostgresStore(dsn)
        payload = FindingInput(source="semgrep", rule_id=uuid.uuid4().hex,
                               resource="fixture.py", severity="high", title="Synthetic",
                               evidence="local test", recommendation="Review",
                               authorized_scope="backup-test")
        item = source.add(payload)
        dump = tmp_path / "backup.dump"
        backup(dsn, dump)
        restore(target_dsn, dump, confirmed=True)
        recovered = PostgresStore(target_dsn).get(item.id)
        assert recovered == item
    finally:
        with psycopg.connect(dsn, autocommit=True) as admin:
            admin.execute(sql.SQL("DROP DATABASE {} WITH (FORCE)").format(sql.Identifier(dbname)))
