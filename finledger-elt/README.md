# FinLedger ELT — Snowflake + dbt Financial Data Engineering

Independent **synthetic-data portfolio project** for the State Street ETL Developer skill set. Not an employer production deployment.

## Flow
CSV → Snowflake RAW_TRANSACTIONS → dbt staging/deduplication → incremental ledger fact → daily settlement reconciliation → dbt quality tests.

## Run locally
```bash
python -m pip install pytest
pytest -q finledger-elt/scripts/test_sample.py
```
No Snowflake account is required for this local test.

## Run on Snowflake
1. Create a database and schema in Snowflake, and set their context.
2. Execute `scripts/bootstrap.sql` to create the raw table, CSV format and internal stage.
3. Upload `seeds/transactions.csv` to the stage via Snowsight, or use SnowSQL `PUT file:///absolute/path/to/transactions.csv @FINLEDGER_STAGE AUTO_COMPRESS=TRUE;`.
4. Run the `COPY INTO` statement in `scripts/bootstrap.sql` **after** uploading.
5. Install `dbt-snowflake`; copy `profiles.example.yml` to `~/.dbt/profiles.yml`; set the listed `SNOWFLAKE_*` environment variables.
6. From `finledger-elt/`, run `dbt debug && dbt run && dbt test`.
7. Re-run `dbt run && dbt test` to check repeatability. Modify a raw transaction with a newer `updated_at` to simulate corrections.

## Tests and limitations
- Source transaction IDs must be unique after staging deduplication.
- Required account/transaction IDs, accepted statuses, and daily reconciliation totals are checked.
- The incremental merge scans the deduplicated source so late corrections are not skipped.
- GitHub Actions runs only the credential-free synthetic data test. A Snowflake/dbt cloud run has **not** been verified.
- Never commit passwords, tokens, or private financial records.
