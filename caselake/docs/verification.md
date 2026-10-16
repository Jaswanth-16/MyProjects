# Verification status

Updated 2026-10-16. Personal project using deterministic synthetic data only.

## Executed locally

The 16-test suite passed using real Apache Spark 3.5.3 and Delta Lake 3.2.1
JARs on Java 17. Model dependencies are pinned to scikit-learn 1.5.2 and MLflow
2.22.0. The default code supports Python 3.11; this build was also exercised on
Python 3.12.14. No provider key or external customer data was used.

| Area | Checks |
|---|---|
| Identifier safety | Five invalid SQL identifier cases rejected |
| Quality/current state | Duplicate/stale replay, correction winner, six rejection reasons, Gold total |
| Conflicts | Same-ticket/version ambiguity quarantines both payloads |
| JSON | Corrupt JSON retained; whitespace-only formatting does not duplicate events |
| Invalid fields | Null priority, missing split and negative version rejected |
| Delta integration | Actual MERGE, repeated ingestion, late correction and later conflict fallback |
| AI | Train/evaluate, save/load identity, OOV/threshold abstention, no-op empty scoring |
| Failure gates | Missing class, train/test overlap, inverted labels, training cap |
| Bundle | Notebook Python syntax, four-task dependency chain and no classic clusters |

The test count is not a performance or enterprise-scale benchmark.

The local Spark driver initially could not bind to the container hostname;
the local-only runner now binds to loopback. This fix does not alter Databricks
network settings. No tests were skipped to hide that failure.

## End-to-end demo result

[Retained local verification JSON](local-verification.json) records the actual run:
130 input events, 127 unique Bronze events, 120 Silver tickets, six quarantined
records, identical replay counts and 120 AI rows persisted in Delta. The trained
classifier was saved/reloaded and its artifact tracked in a real local MLflow run.
It sent 30 low-confidence suggestions to human review at the default threshold.

The template-separated synthetic test set had 30 tickets and scored macro F1
1.0. This intentionally simple fixture is not an independent benchmark, is not
real customer data, and does not establish real-world model accuracy.

## Still requires a Databricks workspace

- CLI bundle validation with workspace authentication, deployment and job execution.
- Unity Catalog permissions, volume access and serverless package installation.
- Workspace MLflow experiment and task-value handoff between notebooks.
- Successful workspace replay, SQL queries and retained job-run evidence.
- Real cost/quota monitoring and cleanup.

The bundle was written against the current Databricks documentation and its
configuration received local structural checks, **not authenticated CLI validation**.
Local Spark/Delta/MLflow execution cannot establish that an account's workspace
policies permit this deployment. A Free Edition account is a possible execution
route, not an executed test or an unlimited compute promise.

## CI

`.github/workflows/caselake-ci.yml` installs the pinned dependencies, runs all
tests and the full local demo, and uploads test XML plus the demo JSON report.
It uses no secrets and deploys nothing to Databricks. See GitHub Actions for the
actual status of each commit; do not infer a passed CI run from the presence of
the workflow file.
