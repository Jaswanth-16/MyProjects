import json
import pytest
from caselake.sample_data import sample_events
from caselake.transforms import identifier, parse_lines, prepare, curate, gold_metrics, raw_schema


def frame(spark, records):
    return spark.createDataFrame(records, raw_schema())


@pytest.mark.parametrize("name", ["a.b", "x;DROP", "a-b", "", "a`b"])
def test_reject_unsafe_identifier(name):
    with pytest.raises(ValueError):
        identifier(name)


def test_replay_latest_version_quarantine_and_gold(spark):
    bronze = prepare(frame(spark, sample_events())).cache()
    silver, quarantine = curate(bronze)
    assert bronze.count() == 127
    assert silver.count() == 120
    assert quarantine.count() == 6
    assert silver.filter("ticket_id = 'access-0000'").first().version_number == 2
    assert sum(r.ticket_count for r in gold_metrics(silver).collect()) == 120
    assert {r.quality_errors for r in quarantine.collect()} == {
        "invalid_text", "invalid_priority", "invalid_version", "invalid_timestamp",
        "missing_ticket_id", "invalid_category"}
    bronze.unpersist()


def test_conflicting_version_is_not_arbitrarily_selected(spark):
    base = sample_events()[0]
    conflicting = dict(base, text="Different payload for the same ticket and version")
    silver, quarantine = curate(prepare(frame(spark, [base, conflicting])))
    assert silver.count() == 0
    assert quarantine.count() == 2
    assert quarantine.select("quality_errors").distinct().first()[0] == "conflicting_version"


def test_corrupt_json_is_quarantined_and_formatting_does_not_duplicate(spark):
    base = sample_events()[0]
    lines = spark.createDataFrame([
        (json.dumps(base),), (json.dumps(base, separators=(",", ":")),), ("not-json",)
    ], ["value"])
    silver, quarantine = curate(prepare(parse_lines(lines)))
    assert silver.count() == 1
    assert quarantine.count() == 1
    assert "malformed_json" in quarantine.first().quality_errors


def test_blank_priority_missing_split_and_negative_version(spark):
    rows = [dict(sample_events()[0], priority=None, split=None, version="-1")]
    errors = prepare(frame(spark, rows)).first().quality_errors
    assert {"invalid_priority", "invalid_split", "invalid_version"} <= set(errors.split(";"))
