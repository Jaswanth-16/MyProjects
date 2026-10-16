# Run CaseLake on Databricks

## Requirements

- Databricks Free Edition or an existing authorized workspace.
- An existing Unity Catalog catalog where you may create a dedicated schema
  and managed volume. `workspace` is a default, not a guarantee; use the catalog
  shown in your Catalog Explorer.
- Serverless notebooks/jobs and workspace MLflow experiment access.
- Package installation access for scikit-learn 1.5.2 and mlflow-skinny 2.22.0.
  Never install local PySpark or delta-spark into Databricks.

Free Edition is serverless-only, quota-limited and has no service-level guarantee.
This bundle uses four **sequential** tasks, no classic cluster and no external
API. Availability of Git folders, CLI deployment or package downloads can vary
by account policy. A paid workspace may incur compute/storage charges. No
deployment is automatic when this repository is cloned or its CI executes.

## Option A — CLI deployment

Install the official Databricks CLI from its documentation (not the obsolete
`pip install databricks-cli` package), then run these commands in a terminal:

```bash
git clone https://github.com/Jaswanth-16/MyProjects.git
cd MyProjects/caselake
databricks auth login --host https://YOUR-WORKSPACE-HOST --profile CASELAKE
databricks bundle validate -t dev --profile CASELAKE
databricks bundle deploy -t dev --profile CASELAKE
databricks bundle run -t dev --profile CASELAKE caselake
```

If your catalog is different, pass `--var catalog=YOUR_CATALOG` to **all three**
bundle commands. Likewise `--var schema=YOUR_DEDICATED_SCHEMA` isolates another
demo. The schema and catalog must be simple identifiers: letters, numbers and
underscores, with a letter/underscore first. Do not use an existing production
schema or point this demonstration at customer tables.

The job creates `assets` in the dedicated schema. Run ingest → curate → train →
score in order. The two AI tasks install their pinned Python dependencies and
restart Python before importing the shared project package.

## Option B — Workspace Git folder and job UI

1. Create a Git folder from the public MyProjects repository.
2. Open `caselake/notebooks/01_ingest.py` in the notebook editor. Preserve the
   whole `caselake` folder: notebooks import shared code from its parent folder.
3. Under Jobs & Pipelines, create a serverless job with four notebook tasks:
   `ingest`, `curate`, `train`, `score`. Select the matching notebook for each.
4. Configure dependencies as a chain in that order, and set maximum concurrent
   runs to 1. Add job parameters `catalog` and `schema` with your dedicated values, plus
   `project_root` set to the absolute `/Workspace/.../MyProjects/caselake` folder.
5. Run the entire job. `train` sets task values that `score` requires; running
   score alone intentionally fails rather than silently choosing an old model.

If Git folders are unavailable, upload the entire folder tree or deploy using
the CLI. The bundle sets `project_root` to its absolute workspace files path. For UI
jobs set that parameter yourself. Serverless current directories are not
guaranteed, so notebooks use the explicit absolute path, never relative imports.

## Verify in Catalog Explorer and SQL

Replace the catalog/schema in `sql/analytics.sql` first. Expected tables:

| Table | Default expectation |
|---|---|
| bronze_ticket_events | 127 unique events |
| silver_tickets | 120 current valid tickets |
| quarantine_events | 6 rejected events |
| gold_ticket_metrics | Aggregated counts total 120 |
| gold_ai_suggestions | 120 rows, each with model run ID and source Delta version |

The training experiment is `/Users/<current_user>/CaseLake`. Check training/test
counts, macro F1, accuracy and saved model artifact. Score uses the exact Silver
Delta version read during training. Confidence is an uncalibrated model score,
not a probability of business correctness. All-OOV and low-score messages route
to `human_review`. Suggestions do not update source labels.

Run the whole job again. Bronze/Silver/quarantine counts must remain unchanged.
Model run IDs and model artifacts will be new; table-overwrite versions will
advance. This is content idempotence, not “no new Delta versions.”

## Failure recovery

- Permission error: verify catalog, `USE CATALOG`, schema/table/volume creation
  and write permissions with your workspace administrator.
- Import error: confirm all shared files were deployed and `project_root` points to
  the folder containing the `caselake` Python package; preserve repository layout.
- Package failure or Free Edition quota: fix access or wait for quota reset;
  do not silently substitute successful local execution for workspace proof.
- Model quality gate: inspect input, labels and split before changing the gate.
- Ingest succeeds but curate fails: rerun the job; Bronze MERGE deduplicates.
- Partial curated publication: tables are committed separately, not as a
  multi-table transaction. Downstream tasks execute only after curate succeeds.
  Manual SQL consumers should wait for a successful full job before reading.

## Cleanup

`databricks bundle destroy -t dev --profile CASELAKE` removes deployed job assets
after confirmation. **It does not remove tables, volumes or MLflow experiments.**
Inspect Catalog Explorer and delete only the dedicated demo schema/data you
created. Inspect/delete old model artifacts and experiment runs separately.
Do not run a broad catalog/schema deletion command against shared data.

## Official references

- https://docs.databricks.com/aws/en/getting-started/free-edition-limitations
- https://docs.databricks.com/aws/en/dev-tools/bundles/examples
- https://docs.databricks.com/aws/en/dev-tools/cli/install
- https://docs.databricks.com/aws/en/delta/merge
- https://docs.databricks.com/aws/en/volumes/
