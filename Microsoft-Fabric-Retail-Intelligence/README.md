# Microsoft Fabric Retail Intelligence | DP-700 Portfolio Project

A reproducible **starter implementation** of a retail analytics Medallion Architecture: CSV → Fabric Lakehouse Bronze → PySpark Silver → data-quality checks → Gold Delta table → SQL endpoint → Power BI.

## Quick start
1. Run `python datasets/generate.py` locally.
2. Follow [the execution guide](docs/EXECUTION_GUIDE.md).
3. Upload CSVs to Fabric Lakehouse `Files/raw/`.
4. Create Fabric notebooks from `notebooks/` and execute 01 → 02 → 03 → 04.
5. Query `sql/analytics.sql` and build a Power BI report using `powerbi/measures.dax`.

## Architecture
`Sources → Data Factory Copy → OneLake Files → Bronze Delta → Silver Delta → Data Quality → Gold Delta → SQL endpoint → Power BI`

Cross-cutting: Data Factory orchestration, monitoring, least-privilege permissions, and Git version control.

## Repository contents
- `datasets/generate.py`: deterministic synthetic CSV generator
- `notebooks/`: Fabric PySpark transformations and quality assertions
- `pipelines/pipeline-spec.json`: orchestration **blueprint**, not deployable export
- `sql/analytics.sql`: analytical SQL queries
- `powerbi/measures.dax`: DAX measure definitions
- `docs/EXECUTION_GUIDE.md`: detailed manual build and execution steps

## Scope and limitations
The local dataset generator is runnable without Fabric. PySpark notebooks require a Fabric Spark session and attached Lakehouse. No claim is made that pipelines, Power BI reports, streaming, Purview or cloud deployment have been executed. This is a documented starter, not a complete production system. For large/production loads replace full refresh with incremental patterns.

## Resume description (after you actually execute it)
Built a Microsoft Fabric retail analytics pipeline using OneLake, Delta Lake, PySpark, data quality validation, SQL analytics and Power BI, orchestrated through Fabric Data Factory.
