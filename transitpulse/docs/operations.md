# Azure operations and deployment evidence

Live Azure deployment remains unverified. The status collector has fixture tests but has not authenticated to Azure. Bicep compilation is not runtime evidence.

Follow [azure-deployment.md](azure-deployment.md). Set `enableMonitoring=true` in both what-if and deployment commands to add Log Analytics, workspace-based Application Insights, the Function connection string and ADF diagnostics. Monitoring defaults to false. Review charges first: the 0.1 GB workspace daily cap and 30-day retention are not a hard billing guarantee. No alert or email recipient is created automatically.

Use [monitoring.kql](../azure/monitoring.kql) after tables receive records; confirm schemas in your workspace. Investigate failures by pipeline/activity and Function duration. Protect logs from secrets.

## Acceptance procedure

1. Follow the deployment guide in a dedicated demo resource group. Upload initial and delta; wait for each execution to finish, then replay delta.
2. Inspect ArchiveBronze and ValidateMergePublish. Initial/delta should commit, replay should skip. Download HEAD, follow its exact snapshot prefix and verify 10,200 trips for the default fixture, 200 delta inserts and 100 updates. ADF status alone does not prove reconciliation or replay.
3. From transitpulse, capture existing run statuses:

```powershell
python scripts/collect_azure_evidence.py --resource-group YOUR_DEMO_GROUP --factory YOUR_FACTORY --run-id INITIAL_RUN_ID --run-id DELTA_RUN_ID --run-id REPLAY_RUN_ID --output azure-status.json
```

The collector only reads status, pipeline and timestamps. Reports exclude parameters, raw errors and resource/run IDs. Exit 0 means all requested runs succeeded for pl_transitpulse, 1 means queried runs failed those checks, 2 means collection was blocked. Azure CLI must already be authenticated and authorized. Its Data Factory extension may install on first use.

4. Save sanitised screenshots of activity success, reconciliation and replay with date and commit. Review identifiers and secrets before sharing.
5. Follow the reviewed cleanup command after checking the group contains only this demo.

For storage/Key Vault 403, check managed identity, scoped RBAC and propagation. For writer 409, verify HEAD stays readable and retry against the new state. For bad-batch 422, inspect quarantine and verify the prior snapshot. Larger workloads need asynchronous orchestration.

Explain why consumers follow HEAD, why ADF serialisation alone does not cover every writer, and how conditional ETag publication prevents lost commits. Distinguish local, emulator, CI and Azure evidence.

References: [Bicep monitoring](https://learn.microsoft.com/en-us/azure/azure-resource-manager/bicep/scenarios-monitoring), [Application Insights](https://learn.microsoft.com/en-us/azure/azure-monitor/app/create-workspace-resource), [ADF run CLI](https://learn.microsoft.com/en-us/cli/azure/datafactory/pipeline-run).
