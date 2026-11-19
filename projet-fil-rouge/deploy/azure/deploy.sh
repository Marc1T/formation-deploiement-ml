#!/usr/bin/env bash
# Déploie l'API sur Azure Container Apps (équivalent bash de deploy.ps1).
#
# Usage :
#   deploy/azure/deploy.sh ghcr.io/monlogin/diabetes-ml/api:latest
#   USE_ACR=1 deploy/azure/deploy.sh                 # construit l'image dans Azure Container Registry
# Variables facultatives : RESOURCE_GROUP, LOCATION, ENV_NAME, APP_NAME, ACR_NAME,
#   REGISTRY_SERVER / REGISTRY_USER / REGISTRY_PASSWORD (image privée)
# Nettoyage : az group delete --name "$RESOURCE_GROUP" --yes --no-wait
set -euo pipefail

IMAGE="${1:-}"
RESOURCE_GROUP="${RESOURCE_GROUP:-rg-diabetes-ml}"
LOCATION="${LOCATION:-francecentral}"
ENV_NAME="${ENV_NAME:-cae-diabetes-ml}"
APP_NAME="${APP_NAME:-diabetes-api}"
USE_ACR="${USE_ACR:-0}"
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"

step() { printf '\n==> %s\n' "$*"; }

if [[ "$USE_ACR" != "1" && -z "$IMAGE" ]]; then
  echo "Indiquez une image publiée en argument, ou USE_ACR=1." >&2; exit 1
fi

step "Connexion Azure"
az account show --only-show-errors >/dev/null 2>&1 || az login --only-show-errors >/dev/null
az account show --query "{abonnement:name, id:id}" -o table

step "Extension containerapp et fournisseurs"
az extension add --name containerapp --upgrade --only-show-errors
az provider register --namespace Microsoft.App --wait --only-show-errors
az provider register --namespace Microsoft.OperationalInsights --wait --only-show-errors

step "Groupe de ressources $RESOURCE_GROUP ($LOCATION)"
az group create --name "$RESOURCE_GROUP" --location "$LOCATION" --output none

REGISTRY_ARGS=()
if [[ "$USE_ACR" == "1" ]]; then
  ACR_NAME="${ACR_NAME:-acrdiabetes$RANDOM}"
  step "Registre ACR $ACR_NAME et construction de l'image dans Azure"
  az acr create --name "$ACR_NAME" --resource-group "$RESOURCE_GROUP" --sku Basic --admin-enabled true --output none
  az acr build --registry "$ACR_NAME" --image diabetes-api:latest --file docker/api.Dockerfile "$ROOT"
  REGISTRY_SERVER="$ACR_NAME.azurecr.io"
  REGISTRY_USER="$(az acr credential show --name "$ACR_NAME" --query username -o tsv)"
  REGISTRY_PASSWORD="$(az acr credential show --name "$ACR_NAME" --query 'passwords[0].value' -o tsv)"
  IMAGE="$REGISTRY_SERVER/diabetes-api:latest"
fi
if [[ -n "${REGISTRY_SERVER:-}" ]]; then
  REGISTRY_ARGS=(--registry-server "$REGISTRY_SERVER" --registry-username "$REGISTRY_USER" --registry-password "$REGISTRY_PASSWORD")
fi

step "Environnement Container Apps $ENV_NAME"
if ! az containerapp env show --name "$ENV_NAME" --resource-group "$RESOURCE_GROUP" --query name -o tsv >/dev/null 2>&1; then
  az containerapp env create --name "$ENV_NAME" --resource-group "$RESOURCE_GROUP" --location "$LOCATION" --output none
fi

step "Container App $APP_NAME avec l'image $IMAGE"
if az containerapp show --name "$APP_NAME" --resource-group "$RESOURCE_GROUP" --query name -o tsv >/dev/null 2>&1; then
  az containerapp update --name "$APP_NAME" --resource-group "$RESOURCE_GROUP" --image "$IMAGE" --output none
else
  az containerapp create \
    --name "$APP_NAME" --resource-group "$RESOURCE_GROUP" --environment "$ENV_NAME" \
    --image "$IMAGE" --target-port 8000 --ingress external \
    --min-replicas 0 --max-replicas 1 --cpu 0.5 --memory 1.0Gi \
    --env-vars MODEL_PATH=/app/models/model.joblib THRESHOLD=0.5 \
    "${REGISTRY_ARGS[@]}" --output none
fi

FQDN="$(az containerapp show --name "$APP_NAME" --resource-group "$RESOURCE_GROUP" --query properties.configuration.ingress.fqdn -o tsv)"
printf '\nAPI déployée :\n  https://%s/docs\n  https://%s/health\n' "$FQDN" "$FQDN"
printf '\nJournaux :  az containerapp logs show -n %s -g %s --follow\n' "$APP_NAME" "$RESOURCE_GROUP"
printf 'Supprimer : az group delete --name %s --yes --no-wait\n' "$RESOURCE_GROUP"
