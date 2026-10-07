# Optional Azure deployment

**Status:** implementation and configuration assets are included; live Azure deployment
has not been performed during project creation. The local demo is complete and costs
nothing in Azure. The commands below create billable resources only when you run them.

## Prerequisites

- An Azure subscription and permissions to create resources and assign RBAC roles.
- Azure CLI with Bicep, Azure Functions Core Tools v4, Python 3.11, Git.
- A region supporting Linux Consumption Functions and Data Factory, and available quota.
- An interactive user identity. The Bicep `operatorObjectId` parameter is assigned User roles;
  adapt it before using a service principal for deployment.

Commands below use Bash and are run from the `transitpulse` directory. Review resource
names and subscription first. No schedule, Event Hubs namespace, Synapse workspace or
Power BI Service publication is created automatically.

## 1. Validate and create the infrastructure

```bash
az login
az account set --subscription 'YOUR_SUBSCRIPTION_ID'
az account show --query '{name:name,id:id}'
az bicep build --file azure/main.bicep

project_group='rg-transitpulse-demo'
project_region='centralindia'
operator_id=$(az ad signed-in-user show --query id -o tsv)
az group create --name "$project_group" --location "$project_region"
az deployment group what-if --resource-group "$project_group" \
  --template-file azure/main.bicep --parameters operatorObjectId="$operator_id"
az deployment group create --name transitpulse --resource-group "$project_group" \
  --template-file azure/main.bicep --parameters operatorObjectId="$operator_id"
```

Bicep creates ADLS Gen2, a private container, separate Function runtime storage, a Linux
Consumption Function App, ADF, Key Vault and scoped data/secret RBAC assignments.
Here “private container” means anonymous blob access is disabled; service endpoints are
public and authenticated. Private networking is not configured.

## 2. Publish the Function code

```bash
function_name=$(az deployment group show -g "$project_group" -n transitpulse \
  --query properties.outputs.functionAppName.value -o tsv)
func azure functionapp publish "$function_name" --python
python scripts/configure_adf.py --resource-group "$project_group"
```

The configuration script reads deployment outputs, captures the Function host key without
printing it, stores it in Key Vault, and creates the ADF linked services/dataset/pipeline.
It uses a restricted temporary file for the secret and deletes it immediately after upload.
Do not run Azure CLI with debug logging around secret operations. RBAC propagation can
take time; if configuration fails with a permission error, wait and rerun the script.

The Function route is POST `/api/process`, protected by a Function key. ADF reads that key
from Key Vault. Lake access uses managed identities. The Function adapter uses the same
Python pipeline and publishes snapshots with conditional ETag writes.

## 3. Upload and process the demo batches

```bash
python -m transitpulse generate --output workspace-cloud/input
storage_name=$(az deployment group show -g "$project_group" -n transitpulse \
  --query properties.outputs.storageAccount.value -o tsv)
factory_name=$(az deployment group show -g "$project_group" -n transitpulse \
  --query properties.outputs.factoryName.value -o tsv)

az storage blob upload --account-name "$storage_name" --auth-mode login \
  --container-name transitpulse --name landing/initial.jsonl \
  --file workspace-cloud/input/initial.jsonl --overwrite false
az storage blob upload --account-name "$storage_name" --auth-mode login \
  --container-name transitpulse --name landing/delta.jsonl \
  --file workspace-cloud/input/delta.jsonl --overwrite false

az datafactory pipeline create-run --resource-group "$project_group" \
  --factory-name "$factory_name" --name pl_transitpulse \
  --parameters '{"batchFile":"initial.jsonl"}'
```

In ADF Monitor, wait for the initial run to succeed. Then run the same create-run command
with `delta.jsonl`. Run delta once more to verify the Function reports `skipped`. The CLI
may offer to install its Data Factory extension on first use.

The `batchFile` parameter must contain only letters, digits, underscores or hyphens with a
`.jsonl` suffix. ADF archives to `bronze/<pipeline-run-id>/<batchFile>`, then invokes the Function.

## 4. Inspect the committed snapshot

```bash
az storage blob download --account-name "$storage_name" --auth-mode login \
  --container-name transitpulse --name state/HEAD.json --file workspace-cloud/HEAD.json
```

HEAD contains `outputs_prefix`, `database_blob`, ingestion metrics and KPIs. Download the
files under that exact outputs_prefix to a local directory for Power BI import. Every
snapshot contains the full current state: never combine all snapshot folders.
Azure Cloud Shell and local download commands may require explicitly allowing overwrite
if downloading into an existing file; choose a new destination for each inspection.

## 5. Optional Synapse serverless serving

If you already have a Synapse workspace, assign its managed identity Storage Blob Data
Reader on the container. In a user database, run [serve_snapshot.sql](../azure/synapse/serve_snapshot.sql)
after replacing the account and snapshot placeholders. Run the credential/data-source
creation once; on later snapshots update only the view definition. The SQL administrator
must grant the appropriate database permissions. This step is not automated or live-tested.

Connect Power BI to that view or use the local CSV imports. The project does not update
the view or refresh Power BI automatically after each batch.

## Troubleshooting and limits

| Symptom | Check |
|---|---|
| 401 from Function | Publish completed; host key exists; Key Vault secret and ADF reference match |
| 403 on storage/Key Vault | Managed identity RBAC scope and propagation |
| Function 409 | Another snapshot committed first; retry reads the latest state |
| Function 422 | Batch exceeds the 5% quality threshold; inspect audit/failure.json |
| Function 400 | Blob path, JSON body, input size, state integrity or source presence |
| Timeout | Reduce input/state size; use asynchronous orchestration for larger workloads |

Input is capped at 10 MiB; restored warehouse snapshots at 50 MiB. The HTTP handler is
synchronous. Monitor ADF activity runs, Function logs and the audit objects. Infrastructure
does not configure alerts or automatic orphan-snapshot cleanup. Confirm runtime/quota
availability and estimate costs in your chosen region before a longer-running deployment.

## Cleanup

After verifying the dedicated resource group contains only this demo, remove it:

```bash
az group delete --name "$project_group"
```

The CLI prompts for confirmation. Key Vault soft deletion can retain the vault name
temporarily. Do not run this command against a group containing other projects.

## Official references

- [Python Functions programming model](https://learn.microsoft.com/en-us/azure/azure-functions/functions-reference-python)
- [ADF Azure Function activity](https://learn.microsoft.com/en-us/azure/data-factory/control-flow-azure-function-activity)
- [ADLS Gen2 connector authentication](https://learn.microsoft.com/en-us/azure/data-factory/connector-azure-data-lake-storage)
- [Synapse serverless CSV queries](https://learn.microsoft.com/en-us/azure/synapse-analytics/sql/query-single-csv-file)
