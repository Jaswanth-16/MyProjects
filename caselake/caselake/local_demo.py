"""Run the actual Delta/Spark pipeline locally with an embedded metastore."""

import argparse
import json
from pathlib import Path
from caselake.sample_data import sample_events, write_jsonl
from caselake.transforms import parse_lines
from caselake.lakehouse import merge_bronze, refresh_curated
from caselake.model import fit_model, score


def local_spark(workspace, jars=None):
    from pyspark.sql import SparkSession
    builder = (SparkSession.builder.master("local[2]").appName("caselake")
               .config("spark.driver.bindAddress", "127.0.0.1")
               .config("spark.driver.host", "127.0.0.1")
               .config("spark.sql.session.timeZone", "UTC")
               .config("spark.sql.shuffle.partitions", "2")
               .config("spark.ui.enabled", "false")
               .config("spark.sql.warehouse.dir", str(Path(workspace).resolve() / "warehouse"))
               .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension")
               .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog"))
    if jars:
        builder = builder.config("spark.jars", jars)
    else:
        from delta import configure_spark_with_delta_pip
        builder = configure_spark_with_delta_pip(builder)
    session = builder.getOrCreate()
    session.sparkContext.setLogLevel("ERROR")
    return session


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--workspace", required=True)
    parser.add_argument("--jars", help="Optional comma-separated pre-downloaded Delta jars")
    args = parser.parse_args()
    path = Path(args.workspace).resolve()
    if path.exists():
        raise SystemExit("Use a fresh workspace; the demo never deletes an existing directory")
    path.mkdir(parents=True)
    raw_path = path / "events.jsonl"
    write_jsonl(raw_path, sample_events())
    spark = local_spark(path, args.jars)
    try:
        spark.sql("CREATE DATABASE IF NOT EXISTS caselake_demo")
        names = [f"caselake_demo.{name}" for name in ["bronze", "silver", "quarantine", "gold"]]
        raw = parse_lines(spark.read.text(str(raw_path)))
        merge_bronze(spark, raw, names[0])
        first = refresh_curated(spark, *names)
        merge_bronze(spark, raw, names[0])
        replay = refresh_curated(spark, *names)
        if first != replay:
            raise AssertionError("Replay changed row counts")
        rows = [r.asDict() for r in spark.table(names[1]).select(
            "ticket_id", "event_id", "text", "category", "split").collect()]
        model, metrics = fit_model(rows)
        import joblib
        joblib.dump(model, path / "model.joblib")
        loaded = joblib.load(path / "model.joblib")
        predictions = score(loaded, rows)
        # This is real local MLflow execution, not a fabricated tracking record.
        import mlflow
        mlflow.set_tracking_uri((path / "mlruns").as_uri())
        mlflow.set_experiment("caselake-local")
        with mlflow.start_run() as run:
            mlflow.log_params({"algorithm": "tfidf_logistic_regression", "dataset": "synthetic_v1"})
            mlflow.log_metrics({k: v for k, v in metrics.items() if isinstance(v, (int, float))})
            mlflow.log_artifact(str(path / "model.joblib"))
            run_id = run.info.run_id
        from pyspark.sql import functions as F
        source_version = int(spark.sql(f"DESCRIBE HISTORY {names[1]} LIMIT 1").first().version)
        ai_table = "caselake_demo.ai_suggestions"
        (spark.createDataFrame(predictions)
         .withColumn("model_run_id", F.lit(run_id))
         .withColumn("source_delta_version", F.lit(source_version))
         .write.format("delta").mode("errorifexists").saveAsTable(ai_table))
        gold_ai_rows = spark.table(ai_table).count()
        assert gold_ai_rows == len(rows)
        report = {"mode": "local_spark_delta", "input_events": len(sample_events()),
                  "dataset_scope": "synthetic_only_not_customer_accuracy",
                  "first_run": first, "replay": replay, "replay_passed": first == replay,
                  "model": metrics, "mlflow_run_id": run_id,
                  "predictions": len(predictions),
                  "gold_ai_delta_rows": gold_ai_rows,
                  "human_review": sum(r["needs_review"] for r in predictions),
                  "databricks_workspace_run": "not_executed"}
        (path / "report.json").write_text(json.dumps(report, indent=2) + "\n")
        print(json.dumps(report, indent=2))
    finally:
        spark.stop()


if __name__ == "__main__":
    main()
