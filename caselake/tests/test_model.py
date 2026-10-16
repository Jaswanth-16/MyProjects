import pytest
import joblib
from caselake.sample_data import sample_events
from caselake.model import fit_model, score, redact


def model_rows():
    # Training tests use the generated current-ticket fixture without invalids
    # or replays. Real pipeline tests exercise the Spark/Delta path separately.
    return [dict(r, event_id=f"event-{i}") for i, r in enumerate(sample_events()[:120])]


def test_model_trains_evaluates_and_roundtrips(tmp_path):
    rows = model_rows()
    model, metrics = fit_model(rows)
    assert metrics["train_rows"] == 90
    assert metrics["test_rows"] == 30
    assert metrics["macro_f1"] >= 0.65
    target = tmp_path / "model.joblib"
    joblib.dump(model, target)
    loaded = joblib.load(target)
    assert score(model, rows) == score(loaded, rows)
    assert len(score(loaded, rows)) == 120


def test_oov_and_high_threshold_abstain():
    model, _ = fit_model(model_rows())
    novel = [{"ticket_id": "novel", "event_id": "new", "text": "zyzzyva quokka ultraviolet"}]
    assert score(model, novel)[0]["suggested_category"] == "human_review"
    assert score(model, model_rows()[:1], threshold=1)[0]["needs_review"]
    assert score(model, []) == []
    with pytest.raises(ValueError):
        score(model, novel, threshold=2)


def test_missing_class_and_overlapping_ticket_ids_fail():
    rows = model_rows()
    with pytest.raises(ValueError, match="Every category"):
        fit_model([r for r in rows if r["category"] != "delivery"])
    rows[-1]["ticket_id"] = rows[0]["ticket_id"]
    with pytest.raises(ValueError, match="leakage"):
        fit_model(rows)


def test_quality_gate_fails_on_inverted_test_labels():
    rows = model_rows()
    for r in rows:
        if r["split"] == "test":
            r["category"] = {"access": "billing", "billing": "delivery", "delivery": "access"}[r["category"]]
    with pytest.raises(ValueError, match="quality gate"):
        fit_model(rows)


def test_redaction_and_training_cap():
    text = redact("Email user@example.com ref 123456789")
    assert "user@example.com" not in text and "123456789" not in text
    with pytest.raises(ValueError, match="capped"):
        fit_model(model_rows() * 50)
