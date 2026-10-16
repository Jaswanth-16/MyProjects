"""Shared PySpark transforms used both locally and on Databricks."""

import re


def identifier(value):
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", value):
        raise ValueError(f"Unsafe SQL identifier: {value!r}")
    return value


def raw_schema():
    from pyspark.sql.types import StructType, StructField, StringType
    from caselake.sample_data import FIELDS
    return StructType([StructField(c, StringType(), True) for c in FIELDS])


def parse_lines(lines):
    """Keep malformed JSON as a quarantinable row instead of silently dropping."""
    from pyspark.sql import functions as F
    schema = raw_schema().add("_corrupt_record", "string")
    return lines.select(
        F.col("value").alias("raw_payload"),
        F.from_json("value", schema, {"mode": "PERMISSIVE"}).alias("parsed"),
    ).select("raw_payload", "parsed.*")


def prepare(raw):
    from pyspark.sql import functions as F
    from caselake.sample_data import FIELDS
    # Hash includes the original payload for invalid input. A replay gets the
    # same event ID. Valid event conflicts are handled separately below.
    payload = F.to_json(F.struct(*[F.col(c) for c in FIELDS]), {"ignoreNullFields": "false"})
    hash_input = payload
    if "_corrupt_record" in raw.columns:
        hash_input = F.when(F.col("_corrupt_record").isNotNull(), F.col("raw_payload")).otherwise(payload)
    df = raw.withColumn("event_id", F.sha2(hash_input, 256))
    df = df.withColumn("version_number", F.expr("try_cast(version as bigint)"))
    df = df.withColumn("priority_number", F.expr("try_cast(priority as int)"))
    df = df.withColumn("created_ts", F.expr("try_cast(created_at as timestamp)"))
    checks = [
        (F.col("ticket_id").isNull() | (F.length(F.trim("ticket_id")) == 0), "missing_ticket_id"),
        (F.col("text").isNull() | (F.length(F.trim("text")) < 5), "invalid_text"),
        (F.col("version_number").isNull() | (F.col("version_number") < 1), "invalid_version"),
        (F.col("priority_number").isNull() | ~F.col("priority_number").isin(1, 2, 3), "invalid_priority"),
        (F.col("created_ts").isNull(), "invalid_timestamp"),
        (~F.coalesce(F.col("category").isin("access", "billing", "delivery"), F.lit(False)), "invalid_category"),
        (~F.coalesce(F.col("split").isin("train", "test", "inference"), F.lit(False)), "invalid_split"),
    ]
    if "_corrupt_record" in df.columns:
        checks.append((F.col("_corrupt_record").isNotNull(), "malformed_json"))
    return df.withColumn("quality_errors", F.concat_ws(";", *[
        F.when(condition, F.lit(reason)) for condition, reason in checks
    ])).dropDuplicates(["event_id"])


def curate(bronze):
    """Rebuild current state from the complete Bronze log; deterministic replay.

    Ambiguous same-ticket/same-version events quarantine that version, rather
    than arbitrarily choosing one. An older unambiguous version can remain.
    """
    from pyspark.sql import Window, functions as F
    invalid = bronze.filter(F.col("quality_errors") != "")
    valid = bronze.filter(F.col("quality_errors") == "")
    conflicts = valid.groupBy("ticket_id", "version_number").count().filter("count > 1").drop("count")
    ambiguous = valid.join(conflicts, ["ticket_id", "version_number"], "inner").withColumn(
        "quality_errors", F.lit("conflicting_version"))
    valid = valid.join(conflicts, ["ticket_id", "version_number"], "left_anti")
    current = valid.withColumn("_rank", F.row_number().over(
        Window.partitionBy("ticket_id").orderBy(F.desc("version_number"))
    )).filter("_rank = 1").drop("_rank")
    quarantine = invalid.unionByName(ambiguous)
    return current, quarantine


def gold_metrics(silver):
    from pyspark.sql import functions as F
    return silver.groupBy("category", "priority_number").agg(
        F.count("*").alias("ticket_count"), F.max("version_number").alias("max_version"))
