"""Simple SQL migration runner for an operator-controlled PostgreSQL database."""
from __future__ import annotations
import os


MIGRATIONS = [
    (1, """CREATE TABLE IF NOT EXISTS sentinelforge_findings (
        id VARCHAR(20) PRIMARY KEY, payload JSONB NOT NULL
    )"""),
    (2, """CREATE INDEX IF NOT EXISTS idx_sentinelforge_findings_severity
        ON sentinelforge_findings ((payload->>'severity'))"""),
]


def apply_migrations(dsn: str) -> list[int]:
    import psycopg
    applied = []
    with psycopg.connect(dsn) as conn:
        conn.execute("""CREATE TABLE IF NOT EXISTS sentinelforge_schema_migrations (
            version INTEGER PRIMARY KEY, applied_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )""")
        for version, sql in MIGRATIONS:
            with conn.transaction():
                exists = conn.execute(
                    "SELECT 1 FROM sentinelforge_schema_migrations WHERE version=%s",
                    (version,),
                ).fetchone()
                if exists:
                    continue
                conn.execute(sql)
                conn.execute("INSERT INTO sentinelforge_schema_migrations(version) VALUES (%s)", (version,))
                applied.append(version)
    return applied


if __name__ == "__main__":
    url = os.environ.get("SENTINELFORGE_DATABASE_URL")
    if not url:
        raise SystemExit("Set SENTINELFORGE_DATABASE_URL before running migrations")
    print("Applied migrations:", apply_migrations(url))
