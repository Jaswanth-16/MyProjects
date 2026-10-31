# SentinelForge AI — local deployment

## Docker + PostgreSQL

Requires Docker Compose. Use only on machines and networks you control.

```bash
cd SentinelForge-AI
export POSTGRES_PASSWORD="$(python -c 'import secrets; print(secrets.token_urlsafe(32))')"
export SENTINELFORGE_API_TOKEN="$(python -c 'import secrets; print(secrets.token_urlsafe(32))')"
docker compose up --build -d
curl http://127.0.0.1:8000/health
```

Open http://127.0.0.1:8000/dashboard and enter the configured API token.
The dashboard is served locally and its token is held only in the browser page's memory.

## Import a scanner report

```bash
curl -X POST 'http://127.0.0.1:8000/scanner-reports/semgrep?authorized_scope=local-fixtures' \
  -H "Authorization: Bearer $SENTINELFORGE_API_TOKEN" \
  -H 'Content-Type: application/json' \
  --data-binary @semgrep.json
```

Supported scanner names: `semgrep`, `trivy`, `checkov`. Reports must be JSON.
Only import reports from assets you own or are authorized to assess.

## Current security boundaries

This is a single-operator prototype, not a hardened public service. The API token is
shared rather than per-user; there is no tenant isolation, migration framework, audit log,
TLS termination, or rate limiting. Docker Compose binds the API to localhost only.
Do not expose it to the public Internet. Never commit environment secrets.
