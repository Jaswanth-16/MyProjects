# Explain CaseLake in an interview

## Two-minute explanation

“I built a Databricks-first lakehouse for support operations. It ingests
synthetic ticket events into a Delta Bronze log and produces current Silver
tickets, quarantine records and Gold metrics. Exact event replays are ignored,
late versions cannot undo corrections and ambiguous same-version changes are
quarantined. A trained text classifier consumes curated text to suggest one of
three routing categories. Low-confidence or unknown-language inputs go to human
review. The four-step Databricks job tracks training in MLflow and retains
source event, Delta version and model run references in the AI output.”

Describe workspace deployment as completed only after you run the bundle in
your own workspace and retain its successful run evidence.

## Five-minute demonstration

1. Show `databricks.yml`: serverless job, four tasks, explicit dependencies.
2. Show Bronze/Silver/quarantine counts and SQL aggregates.
3. Replay input: counts stay unchanged; the correction remains current.
4. Show `test_delta.py`: conflicting newer versions fall back to a known version.
5. Show model metrics, training/test split, MLflow artifact and human-review rule.
6. Explain the synthetic-data limitation and bounded driver training.

## Questions worth preparing

- Why use a logical immutable Bronze log instead of overwriting raw events?
- Why must source duplicates be removed before MERGE?
- What happens if a conflict arrives after an earlier version was published?
- Why is a high synthetic F1 not evidence of customer-level accuracy?
- Why separate the recorded human category from the suggested AI category?
- What changes for 100 million tickets, CDC deletes or structured streaming?
- What does Delta ACID guarantee, and what does it not guarantee across tables?
- What would you add for drift, calibrated confidence, RBAC and real PII?

The best answers describe actual code and measured results, including the parts
not yet deployed. Do not recast this personal project as employment experience.
