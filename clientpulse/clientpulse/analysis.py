import json
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.stats import chi2_contingency
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LogisticRegression
from sklearn.dummy import DummyClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score, f1_score, confusion_matrix
from sklearn.inspection import permutation_importance
from clientpulse.data import load_and_join

FEATURES = ["segment", "tenure_months", "active_days", "support_calls", "monthly_spend"]
NUMERIC = FEATURES[1:]


def train(frame):
    if frame.customer_id.duplicated().any():
        raise ValueError("Customer IDs must be unique before splitting")
    train_ids, test_ids = train_test_split(frame.index, test_size=0.25, random_state=42,
                                          stratify=frame.churned_next_month)
    x_train, x_test = frame.loc[train_ids, FEATURES], frame.loc[test_ids, FEATURES]
    y_train = frame.loc[train_ids, "churned_next_month"].astype(int)
    y_test = frame.loc[test_ids, "churned_next_month"].astype(int)
    numeric = Pipeline([("impute", SimpleImputer(strategy="median")), ("scale", StandardScaler())])
    categorical = Pipeline([("impute", SimpleImputer(strategy="most_frequent")),
                            ("encode", OneHotEncoder(handle_unknown="ignore"))])
    pipeline = Pipeline([
        ("prepare", ColumnTransformer([("numeric", numeric, NUMERIC),
                                        ("categorical", categorical, ["segment"])])),
        ("model", LogisticRegression(max_iter=500, class_weight="balanced", random_state=42)),
    ])
    pipeline.fit(x_train, y_train)
    probability = pipeline.predict_proba(x_test)[:, 1]
    predicted = (probability >= 0.5).astype(int)
    dummy = DummyClassifier(strategy="prior").fit(x_train, y_train)
    rng, bootstrap = np.random.default_rng(42), []
    actual = y_test.to_numpy()
    for _ in range(200):
        indices = rng.integers(0, len(actual), len(actual))
        if len(set(actual[indices])) == 2:
            bootstrap.append(roc_auc_score(actual[indices], probability[indices]))
    importance = permutation_importance(pipeline, x_test, y_test, scoring="roc_auc",
                                         n_repeats=5, random_state=42)
    metrics = {"roc_auc": float(roc_auc_score(y_test, probability)),
               "baseline_roc_auc": float(roc_auc_score(y_test, dummy.predict_proba(x_test)[:, 1])),
               "f1": float(f1_score(y_test, predicted, zero_division=0)),
               "roc_auc_bootstrap_95_interval": np.quantile(bootstrap, [0.025, 0.975]).tolist(),
               "confusion_matrix": confusion_matrix(y_test, predicted).tolist(),
               "train_customers": len(train_ids), "test_customers": len(test_ids),
               "feature_importance": dict(zip(FEATURES, importance.importances_mean.tolist()))}
    split = {"train": frame.loc[train_ids, "customer_id"].tolist(),
             "test": frame.loc[test_ids, "customer_id"].tolist()}
    return pipeline, metrics, split


def run(input_dir, output_dir):
    output = Path(output_dir)
    if output.exists():
        raise ValueError("Use a fresh output directory; existing reports are never overwritten")
    frame, quality, bad_c, bad_u = load_and_join(input_dir)
    model, metrics, split = train(frame)
    output.mkdir(parents=True)
    bad_c.to_csv(output / "quarantine-customers.csv", index=False)
    bad_u.to_csv(output / "quarantine-usage.csv", index=False)
    frame.to_csv(output / "curated.csv", index=False)
    summary = (frame.groupby("segment").churned_next_month.agg(["count", "mean"])
               .reset_index().rename(columns={"mean": "churn_rate"}))
    table = pd.crosstab(frame.segment, frame.churned_next_month)
    statistic, p_value, _, expected = chi2_contingency(table)
    statistics = {"test": "chi_square_segment_churn", "statistic": float(statistic),
                  "p_value": float(p_value), "minimum_expected_cell_count": float(expected.min()),
                  "interpretation": "Exploratory association only; not causation or a confirmatory test"}
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(1, 2, figsize=(11, 4), layout="constrained")
    axes[0].bar(summary.segment, summary.churn_rate, color="#203864")
    axes[0].set(title="Synthetic churn rate by segment", ylabel="Observed churn fraction")
    axes[1].barh(list(metrics["feature_importance"]), list(metrics["feature_importance"].values()), color="#287c8e")
    axes[1].set(title="Held-out permutation importance", xlabel="Decrease in ROC AUC")
    fig.savefig(output / "analysis.png", dpi=160)
    plt.close(fig)
    result = {"dataset": "synthetic_client_retention_v1", "customers": len(frame),
              "quality": quality, "model": metrics, "statistics": statistics,
              "segment_summary": summary.to_dict(orient="records")}
    (output / "metrics.json").write_text(json.dumps(result, indent=2) + "\n")
    (output / "split.json").write_text(json.dumps(split, indent=2) + "\n")
    # EvidenceBrief can ingest these exact documented sentences as source material.
    facts = [f"The analysis contains {len(frame)} synthetic customers.",
             f"The held-out test set contains {metrics['test_customers']} customers.",
             f"The model ROC AUC is {metrics['roc_auc']:.3f} on the synthetic held-out set.",
             f"The majority-prior baseline ROC AUC is {metrics['baseline_roc_auc']:.3f}.",
             f"Rejected usage rows total {quality['usage_rows']}.",
             "Associations in these synthetic data do not establish causal effects or real client performance."]
    (output / "business-findings.md").write_text("# ClientPulse findings\n\n" + "\n\n".join(facts) + "\n")
    (output / "report.md").write_text(
        "# ClientPulse analysis\n\n" + "\n\n".join(facts) +
        "\n\nReview data provenance, check segment effects on independent data, and run an approved "
        "experiment before making retention interventions. No individual decisions are automated.\n")
    return result
