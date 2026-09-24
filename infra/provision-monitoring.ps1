param(
    [string]$ResourceGroup = "foundry-hackathon-rg-0c39e178",
    [string]$Location = "swedencentral",
    [string]$WorkspaceName = "mamalink-logs-258f106f5903",
    [string]$InsightsName = "mamalink-insights-258f106f5903"
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
Write-Host "Telemetry policy: aggregate operation count, status, and duration only; automatic HTTP/Azure SDK instrumentation disabled."
