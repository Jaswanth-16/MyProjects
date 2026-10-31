# SentinelForge AI

Evidence-driven, **defensive** cloud security investigation platform — foundation v0.1.

## Current functionality

- FastAPI service with health endpoint and interactive OpenAPI documentation.
- Validated ingestion of findings from *authorized* scanners or synthetic fixtures.
- Deterministic severity-based risk scores and duplicate suppression.
- Read-only investigation reports with evidence and remediation guidance.
- In-memory, thread-safe development store and isolated API tests.
- No exploitation, automatic cloud changes, or external AI calls.

> **Status:** Foundation only. Hinoki HO1 integration, scanner adapters, persistent PostgreSQL storage, authentication, Azure integration, React dashboard, and Power BI are **not implemented yet**. No Hinoki API credentials or undocumented endpoints are assumed.

## Quick start

Requires Python 3.11+.

```bash
cd SentinelForge-AI
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\\Scripts\\activate
pip install -e ".[dev]"
pytest -q
uvicorn sentinelforge.main:app --reload
```

Open http://127.0.0.1:8000/docs to try the API.

## Example

```bash
curl -X POST http://127.0.0.1:8000/findings \
  -H 'Content-Type: application/json' \
  -d '{"source":"checkov","rule_id":"CKV_AZURE_SAMPLE","resource":"fixtures/storage.tf","severity":"high","title":"Storage configuration needs review","evidence":"Synthetic fixture: public access enabled","recommendation":"Disable public access and review policy","authorized_scope":"local-fixtures"}'
```

GET /findings lists prioritized results; GET /findings/{id}/investigation returns a deterministic evidence-grounded explanation.

## Architecture

```text
Authorized scanner JSON / synthetic fixtures
                  |
             FastAPI validation
                  |
          Finding store + risk score
                  |
       Deterministic investigator
                  |
         REST / OpenAPI consumers
```

Planned: scanner adapters -> persistent storage -> provider-independent AI interface -> optional documented Hinoki provider -> dashboard and CI feedback.

## Safety and limitations

Only scan assets you own or are explicitly authorized to assess. Do not ingest production secrets, personal data, or confidential code. The API currently has **no authentication**, so bind to localhost only and never expose it publicly. Evidence is stored in process memory and lost on restart. Risk scores are illustrative severity weights, not a validated exploitability model. Human approval is required for any future remediation.

## Tests

`pytest -q` checks health, ingestion, duplicate handling, invalid payloads, investigation, and prioritization. CI runs tests on pull requests.

## Roadmap

1. Add authenticated access, PostgreSQL, migrations, and tenant isolation.
2. Build safe Semgrep/Trivy/Checkov/Gitleaks JSON importers.
3. Add a provider-neutral LLM interface; integrate Hinoki only after verifying official access and terms.
4. Build React dashboard, Power BI export, Azure read-only audit integration, and GitHub PR checks.
5. Add threat modeling, structured audit events, security tests, and deployment hardening.
