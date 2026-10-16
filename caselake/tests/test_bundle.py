from pathlib import Path
import ast
import yaml


def test_bundle_task_dependencies_and_notebook_sources():
    root = Path(__file__).resolve().parents[1]
    bundle = yaml.safe_load((root / "databricks.yml").read_text())
    tasks = bundle["resources"]["jobs"]["caselake"]["tasks"]
    assert [t["task_key"] for t in tasks] == ["ingest", "curate", "train", "score"]
    for i, task in enumerate(tasks):
        path = root / task["notebook_task"]["notebook_path"]
        source = path.read_text()
        assert source.startswith("# Databricks notebook source")
        ast.parse(source)
        assert "new_cluster" not in task and "existing_cluster_id" not in task
        if i:
            assert task["depends_on"] == [{"task_key": tasks[i - 1]["task_key"]}]
