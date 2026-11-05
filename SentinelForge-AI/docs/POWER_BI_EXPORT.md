# CSV export for Power BI

The authenticated endpoint `GET /findings/export.csv` returns a CSV of findings
with risk scores, severity, scope, evidence, recommendations and timestamps.

When `SENTINELFORGE_SIGNING_SECRET` is enabled, the export includes **only**
the scope authorized by the signed bearer token. The legacy single shared
token does not provide scope isolation and should only be used locally.

The response is marked `Cache-Control: no-store` and prefixes spreadsheet
formula-like values with a single quote to reduce CSV formula injection risk.
Treat the CSV as sensitive because it may include scanner evidence.

For Power BI Desktop, use **Get Data > Web** or download the CSV locally
with an authorized request. Do not embed a long-lived token in a shared
report or publish the raw evidence dataset without access controls.

This is a prototype export: pagination, streaming from PostgreSQL, row-level
database authorization, scheduled refresh credentials and data retention
policies remain future work.
