# Databricks notebook source
# MAGIC %md
# MAGIC # CaseLake 2 — Silver current state, quarantine and Gold aggregates
# MAGIC Late corrections win by version. Ambiguous versions are quarantined.

# COMMAND ----------
import os
import sys
dbutils.widgets.text("project_root", "")
project_root = dbutils.widgets.get("project_root")
if not project_root.startswith("/Workspace/") or not os.path.isfile(
    os.path.join(project_root, "caselake", "__init__.py")
):
    raise ValueError("Set project_root to the absolute /Workspace/.../caselake folder")
sys.path.insert(0, project_root)
from caselake.transforms import identifier
from caselake.lakehouse import table_name, refresh_curated
dbutils.widgets.text("catalog", "workspace")
dbutils.widgets.text("schema", "caselake_demo")
catalog = identifier(dbutils.widgets.get("catalog"))
schema = identifier(dbutils.widgets.get("schema"))
names = [table_name(catalog, schema, name) for name in [
    "bronze_ticket_events", "silver_tickets", "quarantine_events", "gold_ticket_metrics"]]
counts = refresh_curated(spark, *names)
assert counts["silver"] == 120, counts
assert counts["quarantine"] == 6, counts
print(counts)
display(spark.table(names[-1]))
