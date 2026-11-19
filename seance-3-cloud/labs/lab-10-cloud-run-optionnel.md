# Lab 10 (optionnel) · Déployer l'API sur Google Cloud Run

**Durée** : 25 min · **Objectif** : la même API, déployée sur Google Cloud avec Cloud Build, Artifact Registry et Cloud Run. Comparer avec Azure.

Ce lab demande un projet Google Cloud **avec facturation activée** (essai gratuit avec carte bancaire, ou coupon de crédits fourni par l'enseignant). Sans projet, suivez la démonstration et lisez les commandes : elles sont le miroir de celles d'Azure. Script de référence : [projet-fil-rouge/deploy/gcp/deploy.sh](../../projet-fil-rouge/deploy/gcp/deploy.sh).

## ★ Parcours

### 1. Installer et se connecter

[gcloud CLI](https://cloud.google.com/sdk/docs/install), puis :

```bash
gcloud auth login
gcloud config set project <PROJECT_ID>
gcloud services enable run.googleapis.com artifactregistry.googleapis.com cloudbuild.googleapis.com
```

### 2. Un dépôt d'images

```bash
gcloud artifacts repositories create diabetes-ml --repository-format docker --location europe-west1
```

Artifact Registry est l'équivalent d'Azure Container Registry ou de ghcr.io.

### 3. Construire dans le cloud

```bash
IMAGE=europe-west1-docker.pkg.dev/<PROJECT_ID>/diabetes-ml/api:latest
gcloud builds submit . --config deploy/gcp/cloudbuild.yaml --substitutions _IMAGE=$IMAGE
```

Cloud Build envoie votre dossier (sans ce que `.gcloudignore` ou `.dockerignore` excluent), exécute `docker build -f docker/api.Dockerfile` et pousse l'image. Pas de Docker local nécessaire : comme `az acr build`.

### 4. Déployer

```bash
gcloud run deploy diabetes-api \
  --image $IMAGE \
  --region europe-west1 \
  --allow-unauthenticated \
  --port 8000 \
  --cpu 1 --memory 1Gi \
  --min-instances 0 --max-instances 1 \
  --set-env-vars MODEL_PATH=/app/models/model.joblib,THRESHOLD=0.5
gcloud run services describe diabetes-api --region europe-west1 --format 'value(status.url)'
```

Ouvrez `<url>/docs`. Cloud Run injecte la variable `PORT` ; notre Dockerfile lance `uvicorn … --port ${PORT}` précisément pour cela.

### 5. Comparer

| | Azure Container Apps | Cloud Run |
|---|---|---|
| Unité | Container App dans un Environment | Service dans un projet |
| Construire sans Docker | `az acr build` | `gcloud builds submit` |
| Registre | ACR, ou ghcr.io | Artifact Registry |
| Port | `--target-port` | variable `PORT` imposée |
| Échelle à zéro | `--min-replicas 0` | `--min-instances 0` |
| Journaux | `az containerapp logs show` | `gcloud run services logs read` |
| Tout supprimer | `az group delete` | supprimer le service, le dépôt, ou le projet |

Les concepts sont identiques ; seuls les noms changent. C'est la raison d'apprendre la chaîne générique (image Docker + variables d'environnement) plutôt qu'un fournisseur.

### 6. Nettoyer

```bash
gcloud run services delete diabetes-api --region europe-west1 --quiet
gcloud artifacts repositories delete diabetes-ml --location europe-west1 --quiet
```

## ★★ Aller plus loin

- **Vertex AI** : dans la console, *Model Registry → Import* avec un conteneur de prédiction personnalisé : votre image d'API peut devenir un modèle Vertex, servi par un *Endpoint* avec autoscaling et monitoring. Lisez les prérequis (routes `/health` et `/predict` configurables, port 8080) : notre API les respecte presque.
- **Service authentifié** : retirez `--allow-unauthenticated` et appelez l'API avec `curl -H "Authorization: Bearer $(gcloud auth print-identity-token)"`.
- **Coût** : *Billing → Reports* après quelques appels. Combien a coûté ce lab ?

## Dépannage

| Symptôme | Cause | Solution |
|---|---|---|
| `Billing account … is not enabled` | projet sans facturation | activer l'essai ou appliquer le coupon |
| `PERMISSION_DENIED` sur Cloud Build | API pas activée ou rôle manquant | relancer `gcloud services enable …` ; être *Owner* du projet |
| Le conteneur ne démarre pas (« failed to start and listen on the port ») | l'application n'écoute pas `PORT` | vérifier la commande du Dockerfile |
| Image introuvable au déploiement | région ou nom du dépôt différents entre build et deploy | réutiliser exactement la variable `IMAGE` |

Solution : publiée après la séance.
