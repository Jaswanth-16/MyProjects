from caselake.sample_data import sample_events
from caselake.transforms import raw_schema
from caselake.lakehouse import merge_bronze, refresh_curated


def test_delta_merge_replay_and_late_correction(spark):
    import uuid
    namespace = "test_" + uuid.uuid4().hex[:12]
    spark.sql(f"CREATE DATABASE {namespace}")
    names = [f"{namespace}.{n}" for n in ["bronze", "silver", "quarantine", "gold"]]
    try:
        events = sample_events()
        raw = spark.createDataFrame(events, raw_schema())
        merge_bronze(spark, raw, names[0])
        first = refresh_curated(spark, *names)
        assert first == {"bronze": 127, "silver": 120, "quarantine": 6}
        merge_bronze(spark, raw, names[0])
        assert refresh_curated(spark, *names) == first
        correction = dict(events[0], version="3", priority="2")
        merge_bronze(spark, spark.createDataFrame([correction], raw_schema()), names[0])
        refresh_curated(spark, *names)
        current = spark.table(names[1]).filter("ticket_id = 'access-0000'").first()
        assert current.version_number == 3 and current.priority_number == 2
        # A later-arriving ambiguous payload for version 3 invalidates that
        # version; full Bronze recomputation restores unambiguous version 2.
        conflict = dict(correction, text="Conflicting correction at the same version")
        merge_bronze(spark, spark.createDataFrame([conflict], raw_schema()), names[0])
        counts = refresh_curated(spark, *names)
        assert counts["quarantine"] == 8
        assert spark.table(names[1]).filter("ticket_id = 'access-0000'").first().version_number == 2
    finally:
        spark.sql(f"DROP DATABASE {namespace} CASCADE")
