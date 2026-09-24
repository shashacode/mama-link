param(
    [string]$ResourceGroup = "foundry-hackathon-rg-0c39e178",
    [string]$Location = "swedencentral",
    [string]$WorkspaceName = "mamalink-logs-258f106f5903",
    [string]$InsightsName = "mamalink-insights-258f106f5903",
    [string]$FoundryResource = "mamalink-ai-258f106f5903",
    [string]$ProjectName = "mama-link",
    [string]$ConnectionName = "mamalink-appinsights"
)
$ErrorActionPreference = "Stop"

if (-not (Get-Command az -ErrorAction SilentlyContinue)) { throw "Azure CLI is unavailable." }
az account show --output none
if ($LASTEXITCODE -ne 0) { throw "Run 'az login' before provisioning monitoring." }

$workspaceId = az monitor log-analytics workspace list --resource-group $ResourceGroup --query "[?name=='$WorkspaceName'].id | [0]" -o tsv
if ($LASTEXITCODE -ne 0) { throw "Could not inspect Log Analytics workspaces." }
if (-not $workspaceId) {
    az monitor log-analytics workspace create --resource-group $ResourceGroup --workspace-name $WorkspaceName --location $Location --retention-time 30 --output none
    if ($LASTEXITCODE -ne 0) { throw "Log Analytics workspace creation failed." }
    $workspaceId = az monitor log-analytics workspace show --resource-group $ResourceGroup --workspace-name $WorkspaceName --query id -o tsv
}

$insightsId = az resource list --resource-group $ResourceGroup --resource-type Microsoft.Insights/components --query "[?name=='$InsightsName'].id | [0]" -o tsv
if ($LASTEXITCODE -ne 0) { throw "Could not inspect Application Insights resources." }
if (-not $insightsId) {
    az monitor app-insights component create --app $InsightsName --location $Location --resource-group $ResourceGroup --workspace $workspaceId --output none
    if ($LASTEXITCODE -ne 0) { throw "Application Insights creation failed." }
}

$connection = az monitor app-insights component show --app $InsightsName --resource-group $ResourceGroup --query connectionString -o tsv
if ($LASTEXITCODE -ne 0 -or -not $connection) { throw "Could not read the Application Insights connection string." }

$subscriptionId = az account show --query id -o tsv
if ($LASTEXITCODE -ne 0 -or -not $subscriptionId) { throw "Could not read the active Azure subscription." }

$existingConnection = az cognitiveservices account project connection list `
    --resource-group $ResourceGroup `
    --name $FoundryResource `
    --project-name $ProjectName `
    --query "[?name=='$ConnectionName'].name | [0]" `
    --output tsv
if ($LASTEXITCODE -ne 0) { throw "Could not inspect Foundry project connections." }

if (-not $existingConnection) {
    $managementToken = az account get-access-token --resource https://management.azure.com/ --query accessToken -o tsv
    if ($LASTEXITCODE -ne 0 -or -not $managementToken) { throw "Could not acquire an Azure management token." }

    $connectionUri = "https://management.azure.com/subscriptions/$subscriptionId/resourceGroups/$ResourceGroup/providers/Microsoft.CognitiveServices/accounts/$FoundryResource/projects/$ProjectName/connections/$ConnectionName`?api-version=2025-06-01"
    $connectionBody = @{
        properties = @{
            category = "AppInsights"
            target = $insightsId
            authType = "ApiKey"
            credentials = @{
                key = $connection
            }
            isSharedToAll = $false
            metadata = @{
                ApiType = "Azure"
                ResourceId = $insightsId
            }
        }
    } | ConvertTo-Json -Depth 6
    Invoke-RestMethod `
        -Method Put `
        -Uri $connectionUri `
        -Headers @{ Authorization = "Bearer $managementToken" } `
        -ContentType "application/json" `
        -Body $connectionBody | Out-Null
}

$envPath = Join-Path $PSScriptRoot "..\.env"
$lines = if (Test-Path $envPath) { Get-Content $envPath } else { @() }
$replacement = "APPLICATIONINSIGHTS_CONNECTION_STRING=$connection"
if ($lines -match '^APPLICATIONINSIGHTS_CONNECTION_STRING=') {
    $lines = $lines | ForEach-Object { if ($_ -match '^APPLICATIONINSIGHTS_CONNECTION_STRING=') { $replacement } else { $_ } }
} else {
    $lines += $replacement
}
Set-Content -Path $envPath -Value $lines -Encoding utf8
Write-Host "Monitoring provisioned. The connection string was written to .env and was not printed."
Write-Host "Foundry project connection '$ConnectionName' is available."
Write-Host "Telemetry policy: aggregate operation count, status, and duration only; automatic HTTP/Azure SDK instrumentation disabled."
Write-Warning "Trace-filtered service-side evaluations also require the project's managed identity to have Log Analytics Reader on Application Insights and its workspace. An Azure RBAC administrator must grant that role if it is absent."
