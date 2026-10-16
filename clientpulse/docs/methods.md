# Methods and validation

## Analysis contract

Customer attributes describe an end-of-December snapshot. Historical usage
from November/December supplies features; the binary outcome describes synthetic
churn in the next month. The contract is explicit and deliberately fixed for the
demo; adapting it to real data requires actual observation/label timestamps.

SQLite performs the left join and historical per-customer aggregation. Customers
without valid usage can retain missing features: the training pipeline imputes
these, rather than silently discarding customers. Nonunique conflicting source
keys fail instead of arbitrarily selecting a record.

Data quality rules are deterministic and run before modelling. The generator
adds one exact customer duplicate and one invalid usage row to exercise those
paths. Invalid rows are retained in separate quarantine files. No private data
is required or shipped.

## Statistical modelling

The synthetic label generator uses prior engagement, support-call count and
tenure with random noise. This known relationship makes the exercise
inspectable but also makes synthetic evaluation optimistic. No production
accuracy inference is justified.

The test set contains 25% of unique customers, stratified by label. Imputation,
scaling and one-hot encoding are fitted inside a scikit-learn pipeline after
the split. Unknown inference categories are ignored safely. Identifiers and
future outcomes never enter the feature list.

A prior-probability DummyClassifier provides a ranking baseline. The fixed 0.5
classification threshold is not tuned on the test set. Permutation importance
and the exploratory chi-square segment test describe association, not causes.
Two hundred bootstrap resamples estimate a held-out AUC interval, excluding
single-class resamples. No hyperparameter search is performed.

## Testing

Automated tests exercise source/schema validation, duplicate handling, temporal
exclusion, customer split isolation, feature leakage prevention, inference with
missing values/unseen categories, statistical/report outputs and refusal to
overwrite reports. GitHub Actions executes both tests and CLI commands.

## Mapping to the PwC role

Multi-source data preparation, SQL, exploratory analysis, statistical methods,
machine-learning pipelines, data visualisation and documented findings directly
support the responsibilities in the supplied GenAI Engineer Associate posting.
This project is personal work, separate from employment experience.
