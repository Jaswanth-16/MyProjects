# Run and test locally

Prerequisites: Python 3.11, Java 17 and internet access for Python packages and
the first Maven download of Delta JARs. This uses real Apache Spark and Delta
Lake; it does not emulate Databricks services or Unity Catalog permissions.

## macOS or Linux

```bash
git clone https://github.com/Jaswanth-16/MyProjects.git
cd MyProjects/caselake
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-local.txt
python -m pytest tests -q
python -m caselake.local_demo --workspace demo-output
```

## Windows PowerShell

```powershell
git clone https://github.com/Jaswanth-16/MyProjects.git
cd MyProjects/caselake
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-local.txt
python -m pytest tests -q
python -m caselake.local_demo --workspace demo-output
```

Java must be available on PATH; set JAVA_HOME to your Java 17 installation if
Spark cannot find it. On Windows, filesystem/Hadoop compatibility may require
WSL2: use the Linux instructions there if native Spark cannot initialize.

The demo creates Delta tables in its workspace, performs ingestion twice,
checks replay counts, trains and reloads the classifier, scores 120 records,
then writes `demo-output/report.json`. It logs a real local MLflow run under
`demo-output/mlruns`, including the classifier artifact. No credentials needed.
The CLI refuses an existing output directory: pick `demo-output-2` for another
run. Do not load untrusted `.joblib` files; this code only loads its own output.

If Maven access is blocked, obtain the official matching Delta 3.2.1 artifacts
and pass their absolute paths (comma separated) to `--jars`. For tests set
`CASELAKE_DELTA_JARS` to the same value. Required Maven coordinates:

```text
io.delta:delta-spark_2.12:3.2.1
io.delta:delta-storage:3.2.1
```

Do not treat a Python-only model test as a passed Delta integration test.

## What to inspect

- `first_run` equals `replay` in the report.
- Silver retains version 2 of `access-0000`, despite replaying version 1 later.
- Invalid events are present in quarantine rather than disappearing silently.
- Training and test ticket IDs do not overlap; test templates differ from train.
- Metrics are for a deliberately simple synthetic classification problem only.
- `databricks_workspace_run` remains `not_executed` in local evidence.
