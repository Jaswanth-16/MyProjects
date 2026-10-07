# Portfolio walkthrough

## Five-minute demonstration

1. Run the demo and show initial, correction, rejection and replay counts.
2. Open the dashboard and filter by depot/date. Explain why on-time percentage uses
   completed trips while cancellation percentage uses scheduled trips.
3. Inspect `fact_trip`, `ingested_batch`, `run_audit` and `quarantine` in the SQLite database.
4. Run the tests. Show quality-gate rollback, older-version handling and snapshot conflict tests.
5. Explain the optional Azure architecture and distinguish tested code from live service validation.

## Interview discussion points

- Why do both file hashes and per-record versions matter?
- Why can a global timestamp watermark lose an unseen late trip?
- What happens after the warehouse commits but an export fails?
- How do you avoid publishing half of a cloud snapshot?
- What happens if two Functions read the same HEAD?
- Why are percentages recalculated from additive counts after filtering?
- When would you replace SQLite snapshots with a shared warehouse and asynchronous workers?

## Resume wording after running and understanding the project

**TransitPulse — Transit Operations Analytics | Python, SQL, Azure architecture, Power BI assets**

- Implemented an incremental Python/SQL pipeline for 10,000 synthetic transit records,
  handling 100 corrections, duplicate/stale events and invalid-row quarantine; reconciled
  10,200 unique trips after the incremental load and verified idempotent replay.
- Added transactional quality gates, audit logging, an interactive offline dashboard and
  automated recovery/concurrency tests; prepared Azure Data Factory/Functions deployment
  assets and Power BI import queries, DAX measures and depot-level RLS logic.

These figures describe the provided synthetic demonstration. After you deploy Azure
and build the Power BI report, replace “prepared ... assets” with the precise activities
you personally completed and verified. Do not present synthetic metrics as employer
production results or imply that the cloud/report deployment has already been tested.

## Next useful extensions

Add a source adapter for a documented public transport dataset, add deletion/tombstone
semantics, create a PBIX report and validate role access, then measure a live Azure run.
Keep source data permissions and dataset limitations documented in the repository.
