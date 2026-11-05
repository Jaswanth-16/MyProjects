# Local scanner ingestion (Phase 2)

SentinelForge now supports **offline parsing** of Semgrep, Trivy and Checkov JSON reports. No scanner is launched, no network target is contacted, and no cloud credentials are required.

## Usage

From `SentinelForge-AI` after `pip install -e ".[dev]"`:

```bash
python -m sentinelforge.import_cli semgrep path/to/semgrep.json --scope local-fixtures
python -m sentinelforge.import_cli trivy path/to/trivy.json --scope local-fixtures
python -m sentinelforge.import_cli checkov path/to/checkov.json --scope local-fixtures
```

The CLI prints normalized JSON. Findings can be reviewed and individually submitted to the existing POST /findings endpoint. Automated persistence/import into the API is a future milestone.

## Schema

Each finding contains source, rule_id, resource, severity, title, evidence, recommendation, and authorized_scope.

## Current limitations

- Checkov failed checks default to **medium** because its JSON check records do not always supply a standardized severity. Do not interpret this as a CVSS rating.
- Semgrep's ERROR/WARNING/INFO are mapped to high/medium/info; these are heuristic classifications.
- The importer handles common report shapes, not every version of each scanner.
- Never upload real secrets or confidential scanner reports to an unauthenticated API.
- Reports are capped at 5 MB for the CLI. This is not a hardened untrusted-input sandbox.
- All integrations remain defensive and restricted to authorized scope.
