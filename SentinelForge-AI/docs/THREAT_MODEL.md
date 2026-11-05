# SentinelForge AI threat model (local prototype)

## Trust boundaries

1. **Operator -> API:** Bearer token is required when configured. A shared token is not
   a substitute for user identities or RBAC. The default local run without a token
   must not be exposed to untrusted networks.
2. **Scanner JSON -> parser:** Treat all fields as untrusted. Pydantic enforces
   field lengths and severity enums; ingestion limits report finding count to 1000.
   Reverse proxy/body-size limits remain required.
3. **API -> PostgreSQL:** SQL queries use bound parameters. Migration execution
   requires database DDL permissions; production should use a separate migration role.
4. **Finding evidence -> investigator:** Evidence may contain prompt injection.
   AI output is advisory and cannot execute remediation commands.
5. **API -> browser:** Dashboard inserts text with `textContent`, not `innerHTML`.
   Browser token is kept in page memory; do not serve the dashboard over public HTTP.
6. **Audit log:** Stores event names, IDs and source only; never raw evidence or tokens.

## Known risks and mitigations

| Risk | Existing mitigation | Remaining gap |
|---|---|---|
| Unauthorized reads | Optional bearer token | Real OIDC identity and role/tenant scoping |
| Brute force/abuse | Local per-IP request limiter | Shared distributed limiter and proxy enforcement |
| Data loss | PostgreSQL volume | Backups and restore drills |
| Secret exposure | Environment variables | Secret manager, rotation and TLS |
| Large malicious reports | Finding count and field validation | Request body size cap and strict parser schemas |
| Supply-chain vulnerabilities | pip-audit in CI | Image scanning, pinned dependencies, SBOM |
| Prompt injection | Read-only investigator | Adversarial evaluation and output policy |
| Malicious scanner output | Escaped DOM text | Browser CSP and external security review |

## Deployment decision

**Do not deploy publicly** until authentication, TLS, body limits, backups,
observability, independent security testing and a documented response plan are complete.
