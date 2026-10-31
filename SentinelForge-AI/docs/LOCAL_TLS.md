# Local HTTPS deployment example (Caddy)

The API is not suitable for public exposure. This configuration demonstrates
local TLS termination only, using Caddy's local certificate authority.

1. Install Caddy on the host.
2. Keep Docker Compose bound to `127.0.0.1:8000`.
3. Start the API with a strong `SENTINELFORGE_API_TOKEN`.
4. Run `caddy run --config Caddyfile.local` from this directory.
5. Trust Caddy's local root CA on your own machine only, if required.

This is **not** a production reverse proxy configuration. Public deployment
needs OIDC, access policy, rate limiting at the edge, a domain certificate,
monitoring and a security review.
