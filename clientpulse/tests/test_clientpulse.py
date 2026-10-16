import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import pandas as pd
import pytest
from clientpulse.data import generate, load_and_join
from clientpulse.analysis import train, run, FEATURES


@pytest.fixture
def data(tmp_path):
    folder = tmp_path / "input"
    generate(folder)
    return folder


def test_clean_join_quality_and_snapshot(data):
    frame, rejected, _, bad = load_and_join(data)
    assert len(frame) == 600 and frame.customer_id.nunique() == 600
    assert rejected == {"customer_rows": 0, "usage_rows": 1}
    assert bad.usage_id.tolist() == ["bad-activity"]
    assert frame.active_days.between(0, 31).all()


def test_future_data_excluded(data):
    path = data / "usage.csv"
    usage = pd.read_csv(path)
    future = usage.iloc[[2]].assign(usage_id="future", period="2026-01", active_days=0)
    pd.concat([usage, future]).to_csv(path, index=False)
    _, rejected, _, bad = load_and_join(data)
    assert rejected["usage_rows"] == 2 and "future" in bad.usage_id.tolist()


def test_model_split_baseline_and_no_target_features(data):
    frame, *_ = load_and_join(data)
    model, metrics, split = train(frame)
    assert not (set(split["train"]) & set(split["test"]))
    assert metrics["train_customers"] == 450 and metrics["test_customers"] == 150
    assert metrics["roc_auc"] > metrics["baseline_roc_auc"]
    assert "churned_next_month" not in FEATURES and "customer_id" not in FEATURES
    assert list(model.feature_names_in_) == FEATURES


def test_missing_values_and_unknown_segment_at_inference(data):
    frame, *_ = load_and_join(data)
    model, *_ = train(frame)
    inputs = frame[FEATURES].iloc[:2].copy()
    inputs.loc[inputs.index[0], "active_days"] = float("nan")
    inputs.loc[inputs.index[1], "segment"] = "unseen"
    assert len(model.predict_proba(inputs)) == 2


def test_conflicting_customer_duplicate_fails(data):
    path = data / "customers.csv"
    frame = pd.read_csv(path)
    changed = frame.iloc[[0]].assign(tenure_months=119)
    pd.concat([frame, changed]).to_csv(path, index=False)
    with pytest.raises(ValueError, match="Conflicting duplicate"):
        load_and_join(data)


def test_schema_and_insufficient_data_fail(data):
    path = data / "customers.csv"
    frame = pd.read_csv(path)
    frame.drop(columns=["segment"]).to_csv(path, index=False)
    with pytest.raises(ValueError, match="Expected columns"):
        load_and_join(data)
    with pytest.raises(ValueError, match="at least 100"):
        generate(data, count=3)


def test_full_report_outputs_and_no_overwrite(data, tmp_path):
    output = tmp_path / "report"
    result = run(data, output)
    assert result["customers"] == 600
    assert (output / "analysis.png").stat().st_size > 1000
    assert json.loads((output / "metrics.json").read_text())["quality"]["usage_rows"] == 1
    assert "synthetic" in (output / "business-findings.md").read_text()
    with pytest.raises(ValueError, match="fresh output"):
        run(data, output)
