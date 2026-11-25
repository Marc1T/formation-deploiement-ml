# Lab 10 (optionnel) · Déployer l'API sur Google Cloud Run

**Durée** : 25 min · **Objectif** : la même API, déployée sur Google Cloud avec Cloud Build, Artifact Registry et Cloud Run ; comparer avec Azure.

**Terminal** : Git Bash sous Windows, Terminal sous macOS et Linux.

**Point de départ** : le projet `diabete-lab`, avec un modèle entraîné (`uv run dvc repro`), et un projet Google Cloud **avec facturation activée** (essai gratuit avec carte bancaire, ou coupon de crédits fourni par l'enseignant). Sans projet, suivez la démonstration : les commandes sont le miroir de celles d'Azure. Script de référence : [projet-fil-rouge/deploy/gcp/deploy.sh](../../projet-fil-rouge/deploy/gcp/deploy.sh).

## ★ Parcours

### 1. Installer et se connecter

[gcloud CLI](https://cloud.google.com/sdk/docs/install), puis :

```bash
gcloud auth login
PROJECT_ID=<votre-projet>
REGION=europe-west1
gcloud config set project "$PROJECT_ID"
gcloud services enable run.googleapis.com artifactregistry.googleapis.com cloudbuild.googleapis.com
```

### 2. Un dépôt d'images

```bash
gcloud artifacts repositories create diabete-lab --repository-format docker --location "$REGION"
IMAGE="$REGION-docker.pkg.dev/$PROJECT_ID/diabete-lab/api:latest"
```

Artifact Registry joue le rôle de ghcr.io ou d'Azure Container Registry.

### 3. Dire à Cloud Build quoi envoyer et quoi construire

Sans fichier `.gcloudignore`, `gcloud` reprend votre `.gitignore`… qui exclut `models/`. L'image serait construite sans modèle. Créez `.gcloudignore` à la racine, calqué sur `.dockerignore` :

```
.git
.venv
.dvc/cache
data
mlflow.db
mlruns
mlartifacts
tests
.env
```

Votre Dockerfile n'est pas à la racine (`docker/api.Dockerfile`) : créez `cloudbuild.yaml` pour l'indiquer à Cloud Build.

```yaml
steps:
  - name: gcr.io/cloud-builders/docker
    args: ["build", "-f", "docker/api.Dockerfile", "-t", "${_IMAGE}", "."]
images:
  - "${_IMAGE}"
options:
  logging: CLOUD_LOGGING_ONLY
```

### 4. Construire dans le cloud

```bash
gcloud builds submit . --config cloudbuild.yaml --substitutions "_IMAGE=$IMAGE"
```

Cloud Build envoie votre dossier (moins ce que `.gcloudignore` exclut), exécute `docker build` et pousse l'image : pas de Docker local nécessaire, comme `az acr build`.

### 5. Déployer

```bash
gcloud run deploy diabetes-api \
  --image "$IMAGE" \
  --region "$REGION" \
  --allow-unauthenticated \
  --port 8000 \
  --cpu 1 --memory 1Gi \
  --min-instances 0 --max-instances 1 \
  --set-env-vars THRESHOLD=0.5
URL=$(gcloud run services describe diabetes-api --region "$REGION" --format 'value(status.url)')
curl "$URL/health"
```

> **Point de contrôle** : `{"status":"ok"}`, et `$URL/predict` renvoie `0.5838` pour le patient d'exemple, comme sur Azure.

Cloud Run transmet le port à l'application par la variable `PORT` : c'est pour cela que la commande du Dockerfile lance `uvicorn … --port ${PORT}`.

### 6. Comparer

| | Azure Container Apps | Cloud Run |
|---|---|---|
| Unité | Container App dans un Environment | Service dans un projet |
| Construire sans Docker | `az acr build` | `gcloud builds submit` |
| Registre | ACR, ou ghcr.io | Artifact Registry |
| Port | `--target-port` | variable `PORT`, ou `--port` |
| Échelle à zéro | `--min-replicas 0` | `--min-instances 0` |
| Journaux | `az containerapp logs show` | `gcloud run services logs read` |
| Tout supprimer | `az group delete` | supprimer le service et le dépôt, ou le projet |

Les concepts sont identiques, seuls les noms changent : c'est pour cela qu'on apprend la chaîne générique (une image Docker configurée par des variables) plutôt qu'un fournisseur.

### 7. Nettoyer

```bash
gcloud run services delete diabetes-api --region "$REGION" --quiet
gcloud artifacts repositories delete diabete-lab --location "$REGION" --quiet
```

## ★★ Aller plus loin

- **Vertex AI** : *Model Registry → Import* avec un conteneur de prédiction personnalisé. Lisez ses exigences (port `AIP_HTTP_PORT`, routes de santé et de prédiction, format `{"instances": [...]}`) : que faudrait-il ajouter à votre API ?
- **Service authentifié** : redéployez avec `--no-allow-unauthenticated` et appelez l'API avec `curl -H "Authorization: Bearer $(gcloud auth print-identity-token)" "$URL/health"`.
- **Coût** : *Billing → Reports* après quelques appels. Combien a coûté ce lab ?

## Dépannage

| Symptôme | Cause | Solution |
|---|---|---|
| `Billing account … is not enabled` | projet sans facturation | activer l'essai ou appliquer le coupon |
| Cloud Build : `COPY failed: … models` | `models/` exclu par le `.gitignore` repris par défaut | créer le `.gcloudignore` de l'étape 3 |
| `PERMISSION_DENIED` sur Cloud Build | API non activée, ou rôle manquant | relancer `gcloud services enable …` ; être *Owner* du projet |
| `failed to start and listen on the port` | l'application n'écoute pas le port attendu | `--port 8000` et la commande du Dockerfile avec `${PORT}` |
| Image introuvable au déploiement | région ou nom de dépôt différents entre build et deploy | réutiliser exactement la variable `IMAGE` |

## À retenir

- **Même image, autre nuage** : le travail des séances 1 et 2 se déploie tel quel sur Google Cloud.
- **Ce que l'outil envoie compte autant que ce qu'il construit** : `.gcloudignore` et `.dockerignore` décident de ce qui entre dans l'image.
- **Les plateformes se ressemblent** : registre, service, port, échelle à zéro, journaux ; seuls les noms changent.

## Solution

Solution complète : publiée après la séance.
