"""Delta persistence and safe table naming; no local imitation of Delta."""

from caselake.transforms import identifier, prepare, curate, gold_metrics


def table_name(catalog, schema, name):
    return ".".join(identifier(x) for x in (catalog, schema, name))


def merge_bronze(spark, incoming, table):
    from delta.tables import DeltaTable
    incoming = prepare(incoming)
    if not spark.catalog.tableExists(table):
        incoming.write.format("delta").mode("errorifexists").saveAsTable(table)
    else:
        (DeltaTable.forName(spark, table).alias("target")
         .merge(incoming.alias("source"), "target.event_id = source.event_id")
         .whenNotMatchedInsertAll().execute())


def refresh_curated(spark, bronze_table, silver_table, quarantine_table, gold_table):
    silver, quarantine = curate(spark.table(bronze_table))
    # Demo uses full materialization to make late corrections and discovered
    # conflicts deterministic. This is not a streaming/large-scale CDC claim.
    for frame, table in [(quarantine, quarantine_table), (silver, silver_table)]:
        frame.write.format("delta").mode("overwrite").option("overwriteSchema", "true").saveAsTable(table)
    gold_metrics(spark.table(silver_table)).write.format("delta").mode("overwrite").saveAsTable(gold_table)
    return {"bronze": spark.table(bronze_table).count(),
            "silver": spark.table(silver_table).count(),
            "quarantine": spark.table(quarantine_table).count()}
