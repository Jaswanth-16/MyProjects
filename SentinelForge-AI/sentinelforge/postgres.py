"""Optional PostgreSQL findings store. Requires psycopg and an existing database."""
from __future__ import annotations
from datetime import datetime, timezone
from hashlib import sha256

from sentinelforge.main import Finding, FindingInput, WEIGHTS


class PostgresStore:
    def __init__(self, dsn: str):
        import psycopg
        self.dsn = dsn
        with psycopg.connect(self.dsn) as conn:
            conn.execute("""CREATE TABLE IF NOT EXISTS sentinelforge_findings (
                id VARCHAR(20) PRIMARY KEY,
                payload JSONB NOT NULL
            )""")

    def add(self, payload: FindingInput) -> Finding:
        import psycopg
        key = "|".join([payload.authorized_scope, payload.source, payload.rule_id, payload.resource])
        identifier = sha256(key.encode("utf-8")).hexdigest()[:20]
        item = Finding(**payload.model_dump(), id=identifier,
                       risk_score=WEIGHTS[payload.severity],
                       recorded_at=datetime.now(timezone.utc))
        with psycopg.connect(self.dsn) as conn:
            row = conn.execute("""INSERT INTO sentinelforge_findings(id, payload)
                VALUES (%s, %s::jsonb) ON CONFLICT (id) DO NOTHING
                RETURNING payload""", (identifier, item.model_dump_json())).fetchone()
            if row is None:
                row = conn.execute("SELECT payload FROM sentinelforge_findings WHERE id=%s", (identifier,)).fetchone()
        return Finding.model_validate(row[0])

    def list(self) -> list[Finding]:
        import psycopg
        with psycopg.connect(self.dsn) as conn:
            rows = conn.execute("SELECT payload FROM sentinelforge_findings").fetchall()
        return sorted((Finding.model_validate(row[0]) for row in rows),
                      key=lambda item: (-item.risk_score, item.id))

    def get(self, identifier: str) -> Finding | None:
        import psycopg
        with psycopg.connect(self.dsn) as conn:
            row = conn.execute("SELECT payload FROM sentinelforge_findings WHERE id=%s", (identifier,)).fetchone()
        return Finding.model_validate(row[0]) if row else None
