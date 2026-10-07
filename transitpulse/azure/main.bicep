targetScope = 'resourceGroup'

@description('Region supporting Linux Consumption Functions and Data Factory.')
param location string = resourceGroup().location

@description('Object ID of the operator who will set the Function key in Key Vault. Obtain with az ad signed-in-user show.')
param operatorObjectId string

var suffix = uniqueString(resourceGroup().id)
var blobContributor = subscriptionResourceId('Microsoft.Authorization/roleDefinitions', 'ba92f5b4-2d11-453d-a403-e96b0029c9fe')
var secretReader = subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '4633458b-17de-408a-b874-0445c86b69e6')
var secretOfficer = subscriptionResourceId('Microsoft.Authorization/roleDefinitions', 'b86a8fe4-44ce-4948-aee5-eccb2c155cd7')

resource lake 'Microsoft.Storage/storageAccounts@2023-05-01' = {
  name: 'tpd${suffix}'
  location: location
  sku: { name: 'Standard_LRS' }
  kind: 'StorageV2'
  properties: {
    isHnsEnabled: true
    allowBlobPublicAccess: false
    allowSharedKeyAccess: false
    minimumTlsVersion: 'TLS1_2'
    supportsHttpsTrafficOnly: true
  }
}
resource blobService 'Microsoft.Storage/storageAccounts/blobServices@2023-05-01' = {
  parent: lake
  name: 'default'
}
resource container 'Microsoft.Storage/storageAccounts/blobServices/containers@2023-05-01' = {
  parent: blobService
  name: 'transitpulse'
  properties: { publicAccess: 'None' }
}
resource hostStorage 'Microsoft.Storage/storageAccounts@2023-05-01' = {
  name: 'tph${suffix}'
  location: location
  sku: { name: 'Standard_LRS' }
  kind: 'StorageV2'
  properties: {
    allowBlobPublicAccess: false
    minimumTlsVersion: 'TLS1_2'
    supportsHttpsTrafficOnly: true
  }
}
resource plan 'Microsoft.Web/serverfarms@2023-12-01' = {
  name: 'tp-plan-${suffix}'
  location: location
  kind: 'linux'
  sku: { name: 'Y1', tier: 'Dynamic' }
  properties: { reserved: true }
}
resource functionApp 'Microsoft.Web/sites@2023-12-01' = {
  name: 'tp-fn-${suffix}'
  location: location
  kind: 'functionapp,linux'
  identity: { type: 'SystemAssigned' }
  properties: {
    serverFarmId: plan.id
    httpsOnly: true
    siteConfig: {
      linuxFxVersion: 'Python|3.11'
      minTlsVersion: '1.2'
      ftpsState: 'Disabled'
      appSettings: [
        { name: 'AzureWebJobsStorage', value: 'DefaultEndpointsProtocol=https;AccountName=${hostStorage.name};AccountKey=${hostStorage.listKeys().keys[0].value};EndpointSuffix=${environment().suffixes.storage}' }
        { name: 'FUNCTIONS_EXTENSION_VERSION', value: '~4' }
        { name: 'FUNCTIONS_WORKER_RUNTIME', value: 'python' }
        { name: 'SCM_DO_BUILD_DURING_DEPLOYMENT', value: 'true' }
        { name: 'ENABLE_ORYX_BUILD', value: 'true' }
        { name: 'TRANSITPULSE_STORAGE_URL', value: lake.properties.primaryEndpoints.blob }
        { name: 'TRANSITPULSE_CONTAINER', value: container.name }
      ]
    }
  }
}
resource factory 'Microsoft.DataFactory/factories@2018-06-01' = {
  name: 'tp-adf-${suffix}'
  location: location
  identity: { type: 'SystemAssigned' }
  properties: {}
}
resource vault 'Microsoft.KeyVault/vaults@2023-07-01' = {
  name: 'tp-kv-${suffix}'
  location: location
  properties: {
    tenantId: tenant().tenantId
    sku: { family: 'A', name: 'standard' }
    enableRbacAuthorization: true
    enableSoftDelete: true
    softDeleteRetentionInDays: 7
    accessPolicies: []
  }
}
resource functionDataRole 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(container.id, functionApp.id, blobContributor)
  scope: container
  properties: { principalId: functionApp.identity.principalId, principalType: 'ServicePrincipal', roleDefinitionId: blobContributor }
}
resource factoryDataRole 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(container.id, factory.id, blobContributor)
  scope: container
  properties: { principalId: factory.identity.principalId, principalType: 'ServicePrincipal', roleDefinitionId: blobContributor }
}
resource operatorDataRole 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(container.id, operatorObjectId, blobContributor)
  scope: container
  properties: { principalId: operatorObjectId, principalType: 'User', roleDefinitionId: blobContributor }
}
resource factorySecretRole 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(vault.id, factory.id, secretReader)
  scope: vault
  properties: { principalId: factory.identity.principalId, principalType: 'ServicePrincipal', roleDefinitionId: secretReader }
}
resource operatorSecretRole 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(vault.id, operatorObjectId, secretOfficer)
  scope: vault
  properties: { principalId: operatorObjectId, principalType: 'User', roleDefinitionId: secretOfficer }
}

output storageAccount string = lake.name
output functionAppName string = functionApp.name
output factoryName string = factory.name
output keyVaultName string = vault.name
output storageUrl string = lake.properties.primaryEndpoints.blob
output storageDfsUrl string = lake.properties.primaryEndpoints.dfs
output functionUrl string = 'https://${functionApp.properties.defaultHostName}'
output keyVaultUrl string = vault.properties.vaultUri
