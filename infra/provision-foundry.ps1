param(
    [string]$ResourceGroup = "foundry-hackathon-rg-0c39e178",
    [string]$Location = "swedencentral",
    [string]$FoundryResource = "mamalink-ai-258f106f5903",
    [string]$ProjectName = "mama-link",
    [string]$DeploymentName = "gpt-4.1",
    [string]$ModelName = "gpt-4.1",
    [string]$ModelVersion = "2025-04-14",
    [int]$Capacity = 10
)

$ErrorActionPreference = "Stop"

function Invoke-AzChecked {
    param([Parameter(ValueFromRemainingArguments = $true)][string[]]$Arguments)
    & az @Arguments
    if ($LASTEXITCODE -ne 0) { throw "Azure CLI command failed: az $($Arguments -join ' ')" }
}

if (-not (Get-Command az -ErrorAction SilentlyContinue)) { throw "Azure CLI is not installed or is not on PATH." }
$versionResult = az version -o json
if ($LASTEXITCODE -ne 0) { throw "Azure CLI could not run. Try 'az account show' in this terminal." }
$cliVersion = ($versionResult | ConvertFrom-Json).'azure-cli'
if (-not $cliVersion) { throw "Azure CLI version could not be determined." }
if ([version]$cliVersion -lt [version]"2.80.0") { throw "Azure CLI 2.80.0 or later is required; installed: $cliVersion." }

$subscription = az account show --query "{id:id,name:name,state:state}" -o json | ConvertFrom-Json
if ($LASTEXITCODE -ne 0 -or $subscription.state -ne "Enabled") { throw "No enabled Azure subscription is selected." }
if ((az group exists --name $ResourceGroup) -ne "true") { throw "Resource group '$ResourceGroup' does not exist." }

$existingName = az cognitiveservices account list --resource-group $ResourceGroup --query "[?name=='$FoundryResource'].name | [0]" -o tsv
if ($LASTEXITCODE -ne 0) { throw "Could not inspect resources in '$ResourceGroup'." }
if (-not $existingName) {
    Invoke-AzChecked cognitiveservices account create --name $FoundryResource --resource-group $ResourceGroup --kind AIServices --sku S0 --location $Location --custom-domain $FoundryResource --assign-identity --allow-project-management true --yes
} else {
    $existingKind = az cognitiveservices account show --name $FoundryResource --resource-group $ResourceGroup --query kind -o tsv
    if ($existingKind -ne "AIServices") { throw "'$FoundryResource' exists but is not an AIServices resource." }
    Write-Host "Using existing Foundry resource '$FoundryResource'."
}

$projectState = az cognitiveservices account project list --name $FoundryResource --resource-group $ResourceGroup --query "[?name=='$ProjectName'].properties.provisioningState | [0]" -o tsv
if ($LASTEXITCODE -ne 0) { throw "Could not inspect projects under '$FoundryResource'." }
if (-not $projectState) {
    Invoke-AzChecked cognitiveservices account project create --name $FoundryResource --resource-group $ResourceGroup --project-name $ProjectName --location $Location
} elseif ($projectState -ne "Succeeded") { throw "Project provisioning state is '$projectState'." }
else { Write-Host "Using existing Foundry project '$ProjectName'." }

$deploymentState = az cognitiveservices account deployment list --name $FoundryResource --resource-group $ResourceGroup --query "[?name=='$DeploymentName'].properties.provisioningState | [0]" -o tsv
if ($LASTEXITCODE -ne 0) { throw "Could not inspect model deployments under '$FoundryResource'." }
if (-not $deploymentState) {
    $supported = az cognitiveservices model list --location $Location --query "[?model.name=='$ModelName' && model.version=='$ModelVersion'].model.skus[].name" -o tsv
    if ($LASTEXITCODE -ne 0 -or -not ($supported -split "`n" | Where-Object { $_ -eq "GlobalStandard" })) { throw "$ModelName $ModelVersion with GlobalStandard is unavailable in $Location. No deployment was created." }
    Invoke-AzChecked cognitiveservices account deployment create --name $FoundryResource --resource-group $ResourceGroup --deployment-name $DeploymentName --model-name $ModelName --model-version $ModelVersion --model-format OpenAI --sku-capacity $Capacity --sku-name GlobalStandard
} elseif ($deploymentState -ne "Succeeded") { throw "Deployment provisioning state is '$deploymentState'." }
else { Write-Host "Using existing deployment '$DeploymentName'." }

$projectJson = az cognitiveservices account project show --name $FoundryResource --resource-group $ResourceGroup --project-name $ProjectName -o json
if ($LASTEXITCODE -ne 0) { throw "Could not read the project." }
$endpoint = ($projectJson | ConvertFrom-Json).properties.endpoints.'AI Foundry API'
if (-not $endpoint) { throw "Could not obtain the project endpoint." }

$envPath = Join-Path (Split-Path $PSScriptRoot -Parent) ".env"
if (Test-Path -LiteralPath $envPath) { throw ".env already exists and was not overwritten. Add the endpoint and deployment manually." }
@("AZURE_AI_PROJECT_ENDPOINT=$endpoint", "AZURE_AI_MODEL_DEPLOYMENT_NAME=$DeploymentName", "APPLICATIONINSIGHTS_CONNECTION_STRING=") | Set-Content -LiteralPath $envPath -Encoding utf8

Write-Host "Foundry setup completed in $($subscription.name)."
Write-Host "Project endpoint: $endpoint"
Write-Host "Deployment: $DeploymentName"
Write-Host "Next: .\.venv\Scripts\python.exe -m mama_link.foundry bootstrap"
