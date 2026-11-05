# Local persistence and API authentication

This project supports opt-in SQLite persistence for development and a single-token API guard.

Set `SENTINELFORGE_DB_PATH=./sentinelforge.db` to persist findings across restarts. Set `SENTINELFORGE_API_TOKEN` to a long random value to require `Authorization: Bearer <token>` for all `/findings` endpoints. Do not commit secrets.

Example:

```bash
export SENTINELFORGE_DB_PATH=./sentinelforge.db
export SENTINELFORGE_API_TOKEN="$(python -c 'import secrets; print(secrets.token_urlsafe(32))')"
uvicorn sentinelforge.main:app --host 127.0.0.1 --port 8000
```

This is **not** a multi-user production authorization system. Keep the API bound to localhost. Use a managed identity solution, PostgreSQL, migrations, encryption, and audit logs before deploying publicly.
