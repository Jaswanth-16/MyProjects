"""SQLite-backed persistence for local development; no cloud credentials needed."""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from threading import Lock

from sentinelforge.main import Finding, FindingInput, WEIGHTS


class SQLiteStore:
    def __init__(self, path: str | Path):
        self.path = str(path)
        self._lock = Lock()
        with self._connect() as db:
            db.execute("""CREATE TABLE IF NOT EXISTS findings (
                id TEXT PRIMARY KEY, payload TEXT NOT NULL
            )""")

    def _connect(self):
        return sqlite3.connect(self.path, timeout=10)

    def add(self, payload: FindingInput) -> Finding:
        key = "|".join([payload.authorized_scope, payload.source, payload.rule_id, payload.resource])
        identifier = sha256(key.encode("utf-8")).hexdigest()[:20]
        with self._lock, self._connect() as db:
            row = db.execute("SELECT payload FROM findings WHERE id=?", (identifier,)).fetchone()
            if row:
                return Finding.model_validate_json(row[0])
            item = Finding(**payload.model_dump(), id=identifier,
                           risk_score=WEIGHTS[payload.severity],
                           recorded_at=datetime.now(timezone.utc))
            db.execute("INSERT INTO findings (id, payload) VALUES (?, ?)",
                       (identifier, item.model_dump_json()))
            return item

    def list(self) -> list[Finding]:
        with self._lock, self._connect() as db:
            rows = db.execute("SELECT payload FROM findings").fetchall()
        return sorted((Finding.model_validate_json(row[0]) for row in rows),
                      key=lambda item: (-item.risk_score, item.id))

    def get(self, identifier: str) -> Finding | None:
        with self._lock, self._connect() as db:
            row = db.execute("SELECT payload FROM findings WHERE id=?", (identifier,)).fetchone()
        return Finding.model_validate_json(row[0]) if row else None
