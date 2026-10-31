# SentinelForge AI — verification checklist

## Automated verification

Run from `SentinelForge-AI`:

```bash
python -m pip install -e ".[dev,postgres]"
pytest -q
ruff check sentinelforge tests --select E4,E7,E9,F63,F7,F82
```

The dedicated security workflow additionally runs `pip-audit`. Dependency advisories
can cause this workflow to fail independently of the normal test workflow.

## Manual end-to-end local check

1. Set `POSTGRES_PASSWORD` and `SENTINELFORGE_API_TOKEN` to independent random values.
2. Run `docker compose up --build -d`.
3. Check `curl http://127.0.0.1:8000/health` returns `{"status":"ok"}`.
4. Open `http://127.0.0.1:8000/dashboard`; enter your API token.
5. POST a synthetic Semgrep report to `/scanner-reports/semgrep?authorized_scope=local-fixtures`.
6. Verify the dashboard shows the finding and its investigation.
7. Restart the API container; confirm the finding remains in PostgreSQL.
8. Check requests without the token receive HTTP 401.
9. Stop services with `docker compose down` (do not use `-v` unless intentionally deleting stored findings).

## Release blockers

- No multi-user RBAC, tenant isolation, or secret management integration.
- No formal database migration process, backup/restore testing, or PostgreSQL CI service test.
- No rate limiting, HTTPS reverse proxy, or hardened cloud deployment.
- No comprehensive threat model or independent penetration test.
- AI output requires human review; no automatic remediation is implemented.

A passing CI run verifies the automated checks only, not this entire manual checklist.
