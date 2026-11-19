#!/usr/bin/env bash
# Déploie l'API sur Google Cloud Run (démonstration / parcours optionnel).
#
# L'image est construite par Cloud Build (pas de Docker local), stockée dans
# Artifact Registry, puis déployée sur Cloud Run avec mise à l'échelle à zéro.
#
# Usage :  deploy/gcp/deploy.sh <PROJECT_ID> [REGION]
# Prérequis : gcloud installé, facturation activée sur le projet (essai gratuit ou crédits).
# Nettoyage : gcloud run services delete diabetes-api --region "$REGION"
#             gcloud artifacts repositories delete diabetes-ml --location "$REGION"
set -euo pipefail

PROJECT_ID="${1:?Usage : deploy/gcp/deploy.sh <PROJECT_ID> [REGION]}"
REGION="${2:-europe-west1}"
SERVICE="diabetes-api"
REPO="diabetes-ml"
IMAGE="$REGION-docker.pkg.dev/$PROJECT_ID/$REPO/api:latest"
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"

step() { printf '\n==> %s\n' "$*"; }

step "Projet $PROJECT_ID, région $REGION"
gcloud config set project "$PROJECT_ID" --quiet

step "Activation des API (Cloud Run, Artifact Registry, Cloud Build)"
gcloud services enable run.googleapis.com artifactregistry.googleapis.com cloudbuild.googleapis.com --quiet

step "Dépôt d'images $REPO"
gcloud artifacts repositories describe "$REPO" --location "$REGION" >/dev/null 2>&1 || \
  gcloud artifacts repositories create "$REPO" --repository-format docker --location "$REGION" --quiet

step "Construction de l'image avec Cloud Build"
gcloud builds submit "$ROOT" --config "$ROOT/deploy/gcp/cloudbuild.yaml" --substitutions "_IMAGE=$IMAGE" --quiet

step "Déploiement sur Cloud Run"
gcloud run deploy "$SERVICE" \
  --image "$IMAGE" \
  --region "$REGION" \
  --platform managed \
  --allow-unauthenticated \
  --port 8000 \
  --cpu 1 --memory 1Gi \
  --min-instances 0 --max-instances 1 \
  --set-env-vars MODEL_PATH=/app/models/model.joblib,THRESHOLD=0.5 \
  --quiet

URL="$(gcloud run services describe "$SERVICE" --region "$REGION" --format 'value(status.url)')"
printf '\nAPI déployée :\n  %s/docs\n  %s/health\n' "$URL" "$URL"
printf '\nJournaux :  gcloud run services logs read %s --region %s --limit 50\n' "$SERVICE" "$REGION"
