<#
.SYNOPSIS
  Déploie l'API sur Azure Container Apps (compatible Azure for Students).

.DESCRIPTION
  Crée (ou met à jour) : un groupe de ressources, un environnement Container Apps
  et une Container App exposée publiquement sur le port 8000.
  Deux façons de fournir l'image :
    - -Image : une image déjà publiée (ex. ghcr.io/monlogin/diabetes-ml/api:latest) ;
    - -UseAcr : construit l'image dans Azure Container Registry depuis ce dossier
      (aucun Docker local nécessaire, pratique pour les petites machines).

.EXAMPLE
  .\deploy\azure\deploy.ps1 -Image ghcr.io/monlogin/diabetes-ml/api:latest
.EXAMPLE
  .\deploy\azure\deploy.ps1 -UseAcr -AcrName acrdiabetes1234
.EXAMPLE
  .\deploy\azure\deploy.ps1 -Image ghcr.io/monlogin/diabetes-ml/api:latest `
     -RegistryServer ghcr.io -RegistryUser monlogin -RegistryPassword <PAT read:packages>

.NOTES
  Nettoyage complet quand vous avez fini (évite de consommer le crédit) :
    az group delete --name rg-diabetes-ml --yes --no-wait
#>
[CmdletBinding()]
param(
  [string]$ResourceGroup = "rg-diabetes-ml",
  [string]$Location = "francecentral",      # ou southafricanorth, westeurope...
  [string]$EnvironmentName = "cae-diabetes-ml",
  [string]$AppName = "diabetes-api",
  [string]$Image = "",
  [switch]$UseAcr,
  [string]$AcrName = "",
  [string]$RegistryServer = "",
  [string]$RegistryUser = "",
  [string]$RegistryPassword = ""
)

$ErrorActionPreference = "Stop"
$root = Resolve-Path (Join-Path $PSScriptRoot "..\..")

function Step($msg) { Write-Host "`n==> $msg" -ForegroundColor Cyan }

if (-not $UseAcr -and -not $Image) {
  throw "Indiquez -Image <image publiée> ou -UseAcr (construction dans Azure Container Registry)."
}

Step "Connexion Azure"
az account show --only-show-errors *> $null
if ($LASTEXITCODE -ne 0) { az login --only-show-errors | Out-Null }
az account show --query "{abonnement:name, id:id}" -o table

Step "Extension containerapp et fournisseurs de ressources"
az extension add --name containerapp --upgrade --only-show-errors
az provider register --namespace Microsoft.App --wait --only-show-errors
az provider register --namespace Microsoft.OperationalInsights --wait --only-show-errors
az provider register --namespace Microsoft.ContainerRegistry --wait --only-show-errors

Step "Groupe de ressources $ResourceGroup ($Location)"
az group create --name $ResourceGroup --location $Location --output none

if ($UseAcr) {
  if (-not $AcrName) { $AcrName = "acrdiabetes" + (Get-Random -Minimum 1000 -Maximum 9999) }
  Step "Registre ACR $AcrName (SKU Basic) et construction de l'image dans Azure"
  az acr create --name $AcrName --resource-group $ResourceGroup --sku Basic --admin-enabled true --output none
  az acr build --registry $AcrName --image "diabetes-api:latest" --file "docker/api.Dockerfile" "$root"
  $RegistryServer = "$AcrName.azurecr.io"
  $RegistryUser = az acr credential show --name $AcrName --query username -o tsv
  $RegistryPassword = az acr credential show --name $AcrName --query "passwords[0].value" -o tsv
  $Image = "$RegistryServer/diabetes-api:latest"
}

Step "Environnement Container Apps $EnvironmentName"
$envExists = az containerapp env show --name $EnvironmentName --resource-group $ResourceGroup --query name -o tsv 2>$null
if (-not $envExists) {
  az containerapp env create --name $EnvironmentName --resource-group $ResourceGroup --location $Location --output none
}

$registryArgs = @()
if ($RegistryServer) {
  $registryArgs = @("--registry-server", $RegistryServer, "--registry-username", $RegistryUser, "--registry-password", $RegistryPassword)
}

Step "Container App $AppName avec l'image $Image"
$appExists = az containerapp show --name $AppName --resource-group $ResourceGroup --query name -o tsv 2>$null
if ($appExists) {
  az containerapp update --name $AppName --resource-group $ResourceGroup --image $Image --output none
} else {
  az containerapp create `
    --name $AppName `
    --resource-group $ResourceGroup `
    --environment $EnvironmentName `
    --image $Image `
    --target-port 8000 `
    --ingress external `
    --min-replicas 0 `
    --max-replicas 1 `
    --cpu 0.5 --memory 1.0Gi `
    --env-vars THRESHOLD=0.5 `
    @registryArgs `
    --output none
}

$fqdn = az containerapp show --name $AppName --resource-group $ResourceGroup --query properties.configuration.ingress.fqdn -o tsv
Write-Host "`nAPI déployée :" -ForegroundColor Green
Write-Host "  https://$fqdn/docs"
Write-Host "  https://$fqdn/health"
Write-Host "`nJournaux en direct :  az containerapp logs show -n $AppName -g $ResourceGroup --follow"
Write-Host "Supprimer tout :      az group delete --name $ResourceGroup --yes --no-wait"
