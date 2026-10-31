"""Read-only findings ingestion and deterministic risk assessment API."""
from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from hashlib import sha256
import os
import secrets
from pathlib import Path
from threading import Lock
from typing import Protocol

from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field, field_validator


class Severity(str, Enum):
    critical = "critical"
    high = "high"
    medium = "medium"
    low = "low"
    info = "info"


class FindingInput(BaseModel):
    source: str = Field(min_length=1, max_length=80)
    rule_id: str = Field(min_length=1, max_length=120)
    resource: str = Field(min_length=1, max_length=500)
    severity: Severity
    title: str = Field(min_length=1, max_length=250)
    evidence: str = Field(min_length=1, max_length=4000)
    recommendation: str = Field(min_length=1, max_length=2000)
    authorized_scope: str = Field(min_length=1, max_length=200)

    @field_validator("source", "rule_id", "resource", "title", "evidence", "recommendation", "authorized_scope")
    @classmethod
    def no_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("must not be blank")
        return value.strip()


class Finding(FindingInput):
    id: str
    risk_score: int
    recorded_at: datetime


class Investigator(Protocol):
    def explain(self, finding: Finding) -> dict[str, str]: ...


class DeterministicInvestigator:
    """Safe fallback; does not send data to any external provider."""

    def explain(self, finding: Finding) -> dict[str, str]:
        return {
            "provider": "deterministic",
            "assessment": f"{finding.severity.value.upper()} finding: {finding.title}",
            "evidence": finding.evidence,
            "recommended_action": finding.recommendation,
            "disclaimer": "Review manually. No exploitation or automatic remediation performed.",
        }


WEIGHTS = {
    Severity.critical: 95,
    Severity.high: 80,
    Severity.medium: 55,
    Severity.low: 25,
    Severity.info: 5,
}


class InMemoryStore:
    """Development-only store; resets on process restart."""

    def __init__(self) -> None:
        self._items: dict[str, Finding] = {}
        self._lock = Lock()

    def add(self, payload: FindingInput) -> Finding:
        key = "|".join([payload.authorized_scope, payload.source, payload.rule_id, payload.resource])
        identifier = sha256(key.encode("utf-8")).hexdigest()[:20]
        with self._lock:
            existing = self._items.get(identifier)
            if existing:
                return existing
            item = Finding(
                **payload.model_dump(),
                id=identifier,
                risk_score=WEIGHTS[payload.severity],
                recorded_at=datetime.now(timezone.utc),
            )
            self._items[identifier] = item
            return item

    def list(self) -> list[Finding]:
        with self._lock:
            return sorted(self._items.values(), key=lambda item: (-item.risk_score, item.id))

    def get(self, identifier: str) -> Finding | None:
        with self._lock:
            return self._items.get(identifier)


def create_app(store: InMemoryStore | None = None, investigator: Investigator | None = None) -> FastAPI:
    app = FastAPI(title="SentinelForge AI", version="0.1.0")
    if store is not None:
        database = store
    elif os.getenv('SENTINELFORGE_DB_PATH'):
        from sentinelforge.persistence import SQLiteStore
        database = SQLiteStore(os.environ['SENTINELFORGE_DB_PATH'])
    else:
        database = InMemoryStore()

    def require_token(authorization: str | None = Header(default=None)) -> None:
        expected = os.getenv('SENTINELFORGE_API_TOKEN')
        if expected and (not authorization or not secrets.compare_digest(authorization, 'Bearer ' + expected)):
            raise HTTPException(status_code=401, detail='Unauthorized')
    if investigator is None:
        from sentinelforge.ai import configured_investigator
        analyst = configured_investigator()
    else:
        analyst = investigator

    @app.get("/dashboard", include_in_schema=False)
    def dashboard() -> FileResponse:
        return FileResponse(Path(__file__).with_name("dashboard.html"))

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.post("/findings", response_model=Finding, status_code=201, dependencies=[Depends(require_token)])
    def ingest(payload: FindingInput) -> Finding:
        return database.add(payload)

    @app.get("/findings", response_model=list[Finding], dependencies=[Depends(require_token)])
    def list_findings() -> list[Finding]:
        return database.list()

    @app.get("/findings/{finding_id}/investigation", dependencies=[Depends(require_token)])
    def investigate(finding_id: str) -> dict[str, str]:
        item = database.get(finding_id)
        if item is None:
            raise HTTPException(status_code=404, detail="Finding not found")
        return analyst.explain(item)

    return app


app = create_app()
