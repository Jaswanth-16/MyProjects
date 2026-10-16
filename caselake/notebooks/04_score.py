# Databricks notebook source
# MAGIC %md
# MAGIC # CaseLake 4 — AI suggestions, human review and SQL reporting
# MAGIC Suggestions never automatically change a ticket's assigned category.

# COMMAND ----------
# MAGIC %pip install scikit-learn==1.5.2 mlflow-skinny==2.22.0

# COMMAND ----------
dbutils.library.restartPython()

# COMMAND ----------
import os
import sys
import joblib
dbutils.widgets.text("project_root", "")
project_root = dbutils.widgets.get("project_root")
if not project_root.startswith("/Workspace/") or not os.path.isfile(
    os.path.join(project_root, "caselake", "__init__.py")
):
    raise ValueError("Set project_root to the absolute /Workspace/.../caselake folder")
sys.path.insert(0, project_root)
from caselake.transforms import identifier
from caselake.lakehouse import table_name
from caselake.model import score
dbutils.widgets.text("catalog", "workspace")
dbutils.widgets.text("schema", "caselake_demo")
catalog = identifier(dbutils.widgets.get("catalog"))
schema = identifier(dbutils.widgets.get("schema"))
path = dbutils.jobs.taskValues.get(taskKey="train", key="model_path")
run_id = dbutils.jobs.taskValues.get(taskKey="train", key="model_run_id")
source_version = int(dbutils.jobs.taskValues.get(taskKey="train", key="source_version"))
expected = f"/Volumes/{catalog}/{schema}/assets/models/{run_id}.joblib"
if path != expected:
    raise ValueError("Model path does not match the successful training task")
model = joblib.load(path)
silver = spark.read.option("versionAsOf", source_version).table(
    table_name(catalog, schema, "silver_tickets"))
if silver.count() > 5000:
    raise ValueError("Demo scoring limit exceeded")
rows = [r.asDict() for r in silver.select("ticket_id", "event_id", "text").collect()]
predictions = spark.createDataFrame(score(model, rows))
from pyspark.sql import functions as F
predictions = predictions.withColumn("model_run_id", F.lit(run_id))
predictions = predictions.withColumn("source_delta_version", F.lit(source_version))
predictions.write.format("delta").mode("overwrite").option("overwriteSchema", "true").saveAsTable(
    table_name(catalog, schema, "gold_ai_suggestions"))
display(predictions.groupBy("suggested_category", "needs_review").count())
