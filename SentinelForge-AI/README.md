# SentinelForge AI

Evidence-driven defensive security findings dashboard and API.

## Features

- FastAPI ingestion, deduplication, severity prioritization and read-only investigation.
- Offline Semgrep, Trivy and Checkov JSON parsing, plus authenticated HTTP report ingestion.
- Optional local Ollama investigator with deterministic offline fallback.
- Local HTML dashboard at `/dashboard`, no JavaScript build tools required.
- SQLite persistence for local use; optional PostgreSQL backend and Docker Compose.
- Optional single-operator bearer token guard for findings endpoints.
- Pytest suite and GitHub Actions CI.

## Run locally

Requires Python 3.11+.

```bash
cd SentinelForge-AI
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pytest -q
export SENTINELFORGE_DB_PATH=./sentinelforge.db
export SENTINELFORGE_API_TOKEN="$(python -c 'import secrets; print(secrets.token_urlsafe(32))')"
uvicorn sentinelforge.main:app --host 127.0.0.1 --port 8000
```

Open http://127.0.0.1:8000/dashboard or http://127.0.0.1:8000/docs.
For PostgreSQL, see [local deployment guide](docs/DEPLOYMENT.md).
For token and persistence configuration, see [configuration guide](docs/PERSISTENCE_AND_AUTH.md).

## Scanner JSON ingestion

```bash
curl -X POST 'http://127.0.0.1:8000/scanner-reports/semgrep?authorized_scope=local-fixtures' \
  -H "Authorization: Bearer $SENTINELFORGE_API_TOKEN" \
  -H 'Content-Type: application/json' --data-binary @semgrep.json
```

The service parses supplied reports only. It does not scan remote systems or perform
automatic remediation.

## Architecture

```text
Authorized scanner JSON -> FastAPI validation + bearer token
                       -> SQLite / PostgreSQL / memory store
                       -> Risk prioritization and investigation
                       -> Local HTML dashboard / REST consumers
```

## Security limitations

**Development-stage prototype, not production-ready.** No multi-user RBAC,
tenant isolation, TLS termination, rate limiting, database migration framework,
structured audit trail or independently validated security assessment.
The shared token is optional for local development but required in Docker Compose.
Bind the API to localhost and never ingest secrets or unauthorized scan data.
Human approval is required before any remediation.

## Validation

`pytest -q` runs automated tests. GitHub Actions checks commits and pull requests.
A passing CI run is not proof of production security or successful Docker deployment.
