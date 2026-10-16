# Databricks notebook source
# MAGIC %md
# MAGIC # CaseLake 1 — Unity Catalog, synthetic landing data and Delta Bronze
# MAGIC Run only in a dedicated demo schema. No customer data is required.

# COMMAND ----------
import os
import sys
import json
dbutils.widgets.text("project_root", "")
project_root = dbutils.widgets.get("project_root")
if not project_root.startswith("/Workspace/") or not os.path.isfile(
    os.path.join(project_root, "caselake", "__init__.py")
):
    raise ValueError("Set project_root to the absolute /Workspace/.../caselake folder")
sys.path.insert(0, project_root)
from caselake.transforms import identifier, parse_lines
from caselake.sample_data import sample_events
from caselake.lakehouse import table_name, merge_bronze

dbutils.widgets.text("catalog", "workspace")
dbutils.widgets.text("schema", "caselake_demo")
catalog = identifier(dbutils.widgets.get("catalog"))
schema = identifier(dbutils.widgets.get("schema"))
spark.sql(f"CREATE SCHEMA IF NOT EXISTS {catalog}.{schema}")
spark.sql(f"CREATE VOLUME IF NOT EXISTS {catalog}.{schema}.assets")
root = f"/Volumes/{catalog}/{schema}/assets"
dbutils.fs.mkdirs(root + "/landing")
dbutils.fs.put(root + "/landing/tickets.jsonl", "\n".join(
    json.dumps(r, sort_keys=True) for r in sample_events()) + "\n", True)
raw = parse_lines(spark.read.text(root + "/landing/tickets.jsonl"))
merge_bronze(spark, raw, table_name(catalog, schema, "bronze_ticket_events"))
display(spark.table(table_name(catalog, schema, "bronze_ticket_events")))
