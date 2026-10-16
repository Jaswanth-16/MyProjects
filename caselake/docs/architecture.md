# Architecture and engineering decisions

## Databricks is the main component

Lakeflow Jobs orchestrates ingestion, curation, training and scoring. Unity
Catalog manages the namespace and input/model volume; Delta stores Bronze,
Silver, quarantine, Gold and AI tables. PySpark performs transformations and SQL
exposes reporting data. MLflow tracks the model experiment. There is no external
AI service and no key to acquire or rotate.

This implements bounded batch processing, **not real-time streaming**. The event
log models corrections and late arrival; it makes no Kafka or streaming claims.

## Data integrity

The schema is explicit. JSON parsing preserves malformed input for rejection.
SHA-256 over canonical field values provides event identity, so formatting-only
changes do not generate duplicate business events. Invalid JSON hashes its raw
payload. Bronze uses Delta MERGE with deduplicated source rows, avoiding Delta's
ambiguous multi-match merge behavior.

Silver selects the highest valid version per ticket. Two distinct valid events
with the same ticket/version are a conflict: both enter quarantine. Silver may
fall back to an earlier unambiguous version, rather than presenting an arbitrary
winner. Version numbers, not arrival order, resolve late updates. There are no
delete events in this version; a production system must define tombstones.

Silver, quarantine and Gold are rebuilt from all Bronze data. This prioritizes
correctness and inspectability at portfolio scale. It is **not** an optimized
large-volume incremental implementation. A production extension could use
Auto Loader plus Lakeflow CDC, incremental conflict indexes and checkpoints.

Tables commit individually. Delta ACID does not provide an atomic transaction
over all four tables. The chained job prevents its own training task from
running after failed curation; independent SQL readers still need a publication
protocol. Use a dedicated schema with this job as its only writer.

## AI lifecycle

The classifier learns TF-IDF text features and logistic regression weights.
Labels, ticket IDs, priorities and split markers are not fed as features. Before
vectorization, email-like strings and long numbers are redacted. This is basic
masking, not comprehensive PII detection. Real data needs explicit governance.

The synthetic fixture assigns separate text templates to held-out test tickets.
Ticket IDs are checked for leakage. Labels must exist in all three categories
on both sides of the split. A macro F1 quality gate fails training below 0.65.
Dataset templates share domain vocabulary, so the scores are still optimistic
and cannot establish performance on independent real tickets.

Driver-side training/scoring is capped at 5,000 records. For large data use
appropriate distributed training/inference, a held-out operational dataset and
calibration/drift measurement. Confidence here is uncalibrated; human review is
mandatory for low scores and all-OOV input. High confidence is not a safety
guarantee. No automatic customer action or change to ticket category occurs.

The successful MLflow run writes an immutable run-specific model file and passes
its exact path, run ID and source Delta version to scoring through task values.
Scoring validates the path and reads the same Silver snapshot. Model artifacts
remain trusted-code artifacts: never load a joblib file from an untrusted source.

## Deliberate omissions

No live workspace run, Unity Catalog permission test, model registry deployment,
GenAI/RAG endpoint, polished Databricks dashboard, real customer dataset or
enterprise scale claim is implied by local tests. SQL queries are provided for
building a Databricks dashboard manually. Free Edition availability is subject
to its current quotas and feature restrictions.
