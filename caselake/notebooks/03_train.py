# Databricks notebook source
# MAGIC %md
# MAGIC # CaseLake 3 — Train a real text classifier and track it with MLflow
# MAGIC Small synthetic experiment. Scores do not measure real support accuracy.

# COMMAND ----------
# MAGIC %pip install scikit-learn==1.5.2 mlflow-skinny==2.22.0

# COMMAND ----------
dbutils.library.restartPython()

# COMMAND ----------
import os
import sys
import json
import joblib
import mlflow
dbutils.widgets.text("project_root", "")
project_root = dbutils.widgets.get("project_root")
if not project_root.startswith("/Workspace/") or not os.path.isfile(
    os.path.join(project_root, "caselake", "__init__.py")
):
    raise ValueError("Set project_root to the absolute /Workspace/.../caselake folder")
sys.path.insert(0, project_root)
from caselake.transforms import identifier
from caselake.lakehouse import table_name
from caselake.model import fit_model

dbutils.widgets.text("catalog", "workspace")
dbutils.widgets.text("schema", "caselake_demo")
catalog = identifier(dbutils.widgets.get("catalog"))
schema = identifier(dbutils.widgets.get("schema"))
silver_name = table_name(catalog, schema, "silver_tickets")
source_version = int(spark.sql(f"DESCRIBE HISTORY {silver_name} LIMIT 1").first().version)
silver = spark.read.option("versionAsOf", source_version).table(silver_name)
# Bounded driver training is deliberate. Use distributed training for bigger data.
if silver.count() > 5000:
    raise ValueError("Demo training limit exceeded")
rows = [r.asDict() for r in silver.select("ticket_id", "event_id", "text", "category", "split").collect()]
model, metrics = fit_model(rows)
user = spark.sql("SELECT current_user()").first()[0]
mlflow.set_experiment(f"/Users/{user}/CaseLake")
root = f"/Volumes/{catalog}/{schema}/assets"
os.makedirs(root + "/models", exist_ok=True)
with mlflow.start_run() as run:
    mlflow.log_params({"algorithm": "tfidf_logistic_regression", "dataset": "synthetic_v1",
                       "source_table": silver_name, "source_version": source_version})
    mlflow.log_metrics({k: v for k, v in metrics.items() if isinstance(v, (int, float))})
    # The run ID binds scoring to this exact model; do not load untrusted joblib files.
    artifact = root + f"/models/{run.info.run_id}.joblib"
    joblib.dump(model, artifact)
    mlflow.log_artifact(artifact)
    mlflow.log_dict(metrics, "evaluation.json")
    dbutils.jobs.taskValues.set(key="model_path", value=artifact)
    dbutils.jobs.taskValues.set(key="model_run_id", value=run.info.run_id)
    dbutils.jobs.taskValues.set(key="source_version", value=source_version)
print(json.dumps(metrics, indent=2))
