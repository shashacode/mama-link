param(
    [string]$ResourceGroup = "foundry-hackathon-rg-0c39e178",
    [string]$FoundryResource = "mamalink-ai-258f106f5903",
    [string]$ProjectName = "mama-link",
    [string]$DeploymentName = "gpt-4.1-mini"
)

$ErrorActionPreference = "Stop"
az account show --query "{subscription:name,id:id,state:state}" -o table
if ($LASTEXITCODE -ne 0) { throw "Azure login or subscription lookup failed." }

$resourceName = az cognitiveservices account list --resource-group $ResourceGroup --query "[?name=='$FoundryResource'].name | [0]" -o tsv
if ($LASTEXITCODE -ne 0) { throw "Could not inspect resource group '$ResourceGroup'." }
if (-not $resourceName) {
    Write-Host "Foundry resource '$FoundryResource' has not been created yet."
    Write-Host "Run: .\infra\provision-foundry.ps1"
    exit 2
}

az cognitiveservices account show --name $FoundryResource --resource-group $ResourceGroup --query "{name:name,kind:kind,location:location,state:properties.provisioningState,projectManagement:properties.allowProjectManagement}" -o table
if ($LASTEXITCODE -ne 0) { throw "Foundry resource lookup failed." }

$projectJson = az cognitiveservices account project show --name $FoundryResource --resource-group $ResourceGroup --project-name $ProjectName -o json 2>$null
if ($LASTEXITCODE -ne 0) { throw "Foundry project '$ProjectName' was not found." }
$project = $projectJson | ConvertFrom-Json
$endpoint = $project.properties.endpoints.'AI Foundry API'
Write-Host "Project: $ProjectName"
Write-Host "Project state: $($project.properties.provisioningState)"
Write-Host "Project endpoint: $endpoint"

az cognitiveservices account deployment show --name $FoundryResource --resource-group $ResourceGroup --deployment-name $DeploymentName --query "{name:name,state:properties.provisioningState,model:properties.model.name,version:properties.model.version,sku:sku.name,capacity:sku.capacity}" -o table
if ($LASTEXITCODE -ne 0) { throw "Model deployment '$DeploymentName' was not found." }
