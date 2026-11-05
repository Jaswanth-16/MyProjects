# Signed scoped tokens (prototype)

SentinelForge can optionally enforce short-lived HMAC-signed tokens with an
authorized scope. This is intended for controlled local demos, **not** as a
replacement for OIDC, user provisioning, revocation, or a centralized policy
engine.

Set `SENTINELFORGE_SIGNING_SECRET` to a random secret of at least 32 characters
before starting the API. When enabled, every protected request must use a
valid signed token; the legacy `SENTINELFORGE_API_TOKEN` is not accepted.

Issue a token locally (never paste signing secrets or tokens into a repository):

```bash
python - <<'PY'
import os
from sentinelforge.tokens import issue_token
print(issue_token(os.environ["SENTINELFORGE_SIGNING_SECRET"], "local-analyst", "local-fixtures", ttl_seconds=900))
PY
```

Use it as `Authorization: Bearer <token>`. The token's scope must match
`authorized_scope` for ingestion; list and investigation endpoints hide
findings outside that scope. The token is signed, **not encrypted**. Treat it
as a credential, use TLS, rotate secrets and limit token lifetimes.

Remaining limitations: no identity provider, no per-role permissions, no
revocation, no distributed rate limits, and no formal multi-tenant security
review. Do not publicly expose this prototype.
