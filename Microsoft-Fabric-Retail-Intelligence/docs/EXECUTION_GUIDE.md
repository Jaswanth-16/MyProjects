# Step-by-step Fabric execution guide

## Prerequisites
A Microsoft Fabric-enabled tenant/workspace with sufficient capacity or an eligible trial, permission to create Lakehouses and Data Pipelines, and Power BI access. Actual cloud execution is required to validate Fabric behavior.

## 1. Generate data locally
Install Python 3 and run `python datasets/generate.py`. This creates deterministic CSVs for 2,000 sales, 30 products and 200 customers. No private data is needed.

## 2. Create Fabric workspace and Lakehouse
In app.fabric.microsoft.com create a Fabric-enabled workspace named `Retail-Intelligence-Dev`. Create a Lakehouse named `RetailLakehouse`. Open Lakehouse > Files, create `raw`, upload `sales.csv`, `products.csv`, `customers.csv`.

## 3. Build notebooks
Create four PySpark notebooks, copying each numbered file in `notebooks/` into its respective notebook. Attach all notebooks to `RetailLakehouse`. Execute them in numeric order. The first writes Bronze Delta tables, second Silver, third validation log and assertion, fourth Gold daily summary.

## 4. Configure Data Factory orchestration
Create a Data Pipeline named `pl_retail_daily`. Add a Copy activity that copies the CSV source into Lakehouse Files/raw (if using external storage), or omit the Copy step when files are manually uploaded. Add Notebook activities in Bronze > Silver > Quality > Gold order. Configure success dependencies, sensible retries and notifications; schedule only after a successful manual run. The provided `pipelines/pipeline-spec.json` is a blueprint, **not** an importable Fabric pipeline export.

## 5. Validate tables and quality
In Lakehouse, inspect `bronze_sales`, `silver_sales`, `gold_daily_sales`, and `quality_results`. Check that all quality checks passed. For repeatable full-refresh demonstrations, rerun notebooks 01, 02 and 04. Quality log appends by design.

## 6. Serve SQL
Open the Lakehouse SQL analytics endpoint. Execute `sql/analytics.sql`. Confirm revenue by category and city. Note that SQL endpoint is read-only for Lakehouse Delta tables; use Spark for writes.

## 7. Build Power BI
Create a report from the Gold table using the supported semantic model workflow for your Fabric environment. Add the four measures from `powerbi/measures.dax`, cards for revenue/units/transactions/AOV, a line chart by sale_date, bar charts by category and city, and date/category slicers. Validate aggregates against SQL. Save report `Retail Sales Overview`.

## 8. Governance and security
Grant least-privilege workspace roles; review OneLake data permissions and the Power BI semantic model security configuration. For production, use Microsoft Purview lineage/classification and workspace deployment controls. Do not commit credentials or tenant IDs.

## 9. Monitoring and deployment
Inspect pipeline run history, notebook errors, data quality results and Fabric capacity metrics. Set failure notifications in your own tenant. Connect workspace Git integration where supported; use dev/test/prod workspaces and deployment pipelines according to tenant capabilities.

## 10. Production improvements
Replace overwrite full refreshes with watermark-based incremental ingestion and Delta MERGE, add late-arriving event handling, source contract tests, quarantine tables, secrets management and real-time Eventstream. Those features are **not implemented** in this starter.
