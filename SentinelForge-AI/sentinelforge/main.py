"""Read-only findings ingestion and deterministic risk assessment API."""
from __future__ import annotations

from datetime import datetime, timezone
import csv
import io
from enum import Enum
from hashlib import sha256
import os
import secrets
from pathlib import Path
from threading import Lock
from typing import Protocol

from fastapi import Body, Depends, FastAPI, Header, HTTPException, Request
from fastapi.responses import FileResponse, StreamingResponse
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
    signing_secret = os.getenv("SENTINELFORGE_SIGNING_SECRET")
    if signing_secret and len(signing_secret) < 32:
        raise ValueError("SENTINELFORGE_SIGNING_SECRET must be at least 32 characters")
    if store is not None:
        database = store
    elif os.getenv('SENTINELFORGE_DATABASE_URL'):
        from sentinelforge.postgres import PostgresStore
        database = PostgresStore(os.environ['SENTINELFORGE_DATABASE_URL'])
    elif os.getenv('SENTINELFORGE_DB_PATH'):
        from sentinelforge.persistence import SQLiteStore
        database = SQLiteStore(os.environ['SENTINELFORGE_DB_PATH'])
    else:
        database = InMemoryStore()

    from sentinelforge.rate_limit import RateLimiter
    limiter = RateLimiter(limit=120, window_seconds=60)

    def require_token(request: Request, authorization: str | None = Header(default=None)) -> dict | None:
        expected = os.getenv("SENTINELFORGE_API_TOKEN")
        signing_secret = os.getenv("SENTINELFORGE_SIGNING_SECRET")
        if signing_secret and len(signing_secret) < 32:
            raise RuntimeError("SENTINELFORGE_SIGNING_SECRET must be at least 32 characters")
        claims = None
        if signing_secret:
            from sentinelforge.tokens import TokenError, verify_token
            try:
                if not authorization or not authorization.startswith("Bearer "):
                    raise TokenError("Missing token")
                claims = verify_token(signing_secret, authorization[7:])
            except TokenError as exc:
                raise HTTPException(status_code=401, detail="Unauthorized") from exc
        elif expected and (not authorization or not secrets.compare_digest(authorization, "Bearer " + expected)):
            raise HTTPException(status_code=401, detail="Unauthorized")
        if not limiter.allow(request.client.host if request.client else "unknown"):
            raise HTTPException(status_code=429, detail="Rate limit exceeded")
        return claims

    def authorize_scope(scope: str, claims: dict | None) -> None:
        if claims is not None and claims["scope"] != scope:
            raise HTTPException(status_code=403, detail="Scope access denied")

    if investigator is None:
        from sentinelforge.ai import configured_investigator
        analyst = configured_investigator()
    else:
        analyst = investigator

    class BodyLimitMiddleware:
        def __init__(self, wrapped, max_bytes: int = 5_000_000):
            self.wrapped = wrapped
            self.max_bytes = max_bytes

        async def __call__(self, scope, receive, send):
            if scope["type"] != "http" or scope.get("method") not in ("POST", "PUT", "PATCH"):
                await self.wrapped(scope, receive, send)
                return
            from starlette.responses import JSONResponse
            headers = dict(scope.get("headers", []))
            length = headers.get(b"content-length")
            if length is not None:
                try:
                    if int(length) > self.max_bytes:
                        await JSONResponse({"detail": "Request too large"}, status_code=413)(scope, receive, send)
                        return
                except ValueError:
                    await JSONResponse({"detail": "Invalid Content-Length"}, status_code=400)(scope, receive, send)
                    return
            total = 0
            chunks = []
            while True:
                message = await receive()
                if message["type"] != "http.request":
                    return
                chunk = message.get("body", b"")
                total += len(chunk)
                if total > self.max_bytes:
                    await JSONResponse({"detail": "Request too large"}, status_code=413)(scope, receive, send)
                    return
                chunks.append(chunk)
                if not message.get("more_body", False):
                    break
            delivered = False
            async def buffered_receive():
                nonlocal delivered
                if not delivered:
                    delivered = True
                    return {"type": "http.request", "body": b"".join(chunks), "more_body": False}
                return {"type": "http.disconnect"}
            await self.wrapped(scope, buffered_receive, send)

    app.add_middleware(BodyLimitMiddleware)

    @app.get("/dashboard", include_in_schema=False)
    def dashboard() -> FileResponse:
        return FileResponse(Path(__file__).with_name("dashboard.html"))

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.post("/findings", response_model=Finding, status_code=201, dependencies=[Depends(require_token)])
    def ingest(payload: FindingInput, claims: dict | None = Depends(require_token)) -> Finding:
        authorize_scope(payload.authorized_scope, claims)
        from sentinelforge.audit import record
        item = database.add(payload)
        record('finding_ingested', finding_id=item.id, source=item.source)
        return item

    @app.post("/scanner-reports/{scanner}", response_model=list[Finding], status_code=201,
              dependencies=[Depends(require_token)])
    def import_scanner_report(scanner: str, authorized_scope: str,
                              report: dict | list = Body(...),
                              claims: dict | None = Depends(require_token)) -> list[Finding]:
        authorize_scope(authorized_scope, claims)
        from sentinelforge.scanners import ScannerImportError, parse_report
        try:
            findings = parse_report(scanner, report, authorized_scope)
        except (ScannerImportError, AttributeError, TypeError) as exc:
            raise HTTPException(status_code=422, detail="Invalid scanner report") from exc
        if len(findings) > 1000:
            raise HTTPException(status_code=413, detail="Too many findings")
        from sentinelforge.audit import record
        stored = [database.add(item) for item in findings]
        record('scanner_report_imported', source=scanner)
        return stored

    @app.get("/findings", response_model=list[Finding], dependencies=[Depends(require_token)])
    def list_findings(claims: dict | None = Depends(require_token)) -> list[Finding]:
        items = database.list()
        return [item for item in items if item.authorized_scope == claims["scope"]] if claims else items

    @app.get("/findings/export.csv", dependencies=[Depends(require_token)])
    def export_findings(claims: dict | None = Depends(require_token)) -> StreamingResponse:
        """CSV export for BI; protects spreadsheet applications from formula injection."""
        columns = ["id", "source", "rule_id", "resource", "severity", "title",
                   "evidence", "recommendation", "authorized_scope", "risk_score", "recorded_at"]
        def safe_cell(value: object) -> str:
            raw = str(value)
            if raw.lstrip().startswith(("=", "+", "-", "@", "\\t", "\\r", "\\n")):
                return "'" + raw
            return raw
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(columns)
        for finding in database.list():
            if claims is not None and finding.authorized_scope != claims["scope"]:
                continue
            data = finding.model_dump(mode="json")
            writer.writerow([safe_cell(data[column]) for column in columns])
        output.seek(0)
        return StreamingResponse(iter([output.getvalue()]), media_type="text/csv",
                                 headers={"Content-Disposition": "attachment; filename=sentinelforge-findings.csv",
                                          "Cache-Control": "no-store"})

    @app.get("/findings/{finding_id}/investigation", dependencies=[Depends(require_token)])
    def investigate(finding_id: str, claims: dict | None = Depends(require_token)) -> dict[str, str]:
        item = database.get(finding_id)
        if item is None or (claims and item.authorized_scope != claims["scope"]):
            raise HTTPException(status_code=404, detail="Finding not found")
        from sentinelforge.audit import record
        record('finding_investigated', finding_id=item.id, source=item.source)
        return analyst.explain(item)

    return app


app = create_app()
