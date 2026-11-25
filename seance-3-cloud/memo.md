# Mémo · Séance 3 · Streamlit Cloud, Azure, Google Cloud, Gemini

Toutes les commandes de la séance sur une page. Terminal : Git Bash sous Windows, Terminal sous macOS et Linux. Les commandes Azure ont été vérifiées avec Azure CLI 2.93 (extension `containerapp`).

## Streamlit Community Cloud

| Étape | Commande ou réglage |
|---|---|
| Dépendances, à côté du fichier principal | `uv export --format requirements-txt --no-default-groups --group app --no-hashes --no-emit-project -o app/requirements.txt` |
| Créer l'application | share.streamlit.io → *Create app* → dépôt, branche `main`, `app/streamlit_app.py` |
| Version de Python | *Advanced settings* → 3.11 |
| Configuration | *Settings* → *Secrets* (TOML) : `API_URL = "https://…"` |
| Redéployer | `git push` sur `main` ; ou *Manage app* → *Reboot* |

```python
def setting(name, default=""):
    if os.getenv(name):
        return os.environ[name]
    try:
        return str(st.secrets.get(name, default))
    except FileNotFoundError:      # pas de secrets en local
        return default
```

## Azure Container Apps

```bash
az login
az extension add --name containerapp --upgrade
az provider register --namespace Microsoft.App --wait
az provider register --namespace Microsoft.OperationalInsights --wait
az group create --name rg-diabetes-ml --location francecentral
az containerapp env create --name cae-diabetes-ml --resource-group rg-diabetes-ml --location francecentral
az containerapp create --name diabetes-api --resource-group rg-diabetes-ml --environment cae-diabetes-ml \
  --image ghcr.io/<compte-en-minuscules>/diabete-lab/api:latest --target-port 8000 --ingress external \
  --min-replicas 0 --max-replicas 1 --cpu 0.5 --memory 1.0Gi --env-vars THRESHOLD=0.5
```

| Commande | Effet |
|---|---|
| `az containerapp show -n diabetes-api -g rg-diabetes-ml --query properties.configuration.ingress.fqdn -o tsv` | Adresse publique |
| `az containerapp logs show -n diabetes-api -g rg-diabetes-ml --tail 30` (ou `--follow`) | Journaux |
| `az containerapp update -n diabetes-api -g rg-diabetes-ml --image <image:sha>` | Nouvelle version |
| `az containerapp revision list -n diabetes-api -g rg-diabetes-ml -o table` | Historique des révisions |
| `az containerapp secret set -n diabetes-api -g rg-diabetes-ml --secrets gemini=<clé>` | Secret (puis `--set-env-vars GEMINI_API_KEY=secretref:gemini`) |
| `az acr create … --sku Basic --admin-enabled true` puis `az acr build --registry … --image … --file docker/api.Dockerfile .` | Construire l'image dans Azure |
| `az group delete --name rg-diabetes-ml --yes --no-wait` | Tout supprimer |

Sous Git Bash, une valeur d'argument qui commence par `/` est convertie en chemin Windows : préfixer par `MSYS_NO_PATHCONV=1` si besoin.

## Google Cloud Run (optionnel)

```bash
gcloud auth login
gcloud config set project <PROJECT_ID>
gcloud services enable run.googleapis.com artifactregistry.googleapis.com cloudbuild.googleapis.com
gcloud artifacts repositories create diabete-lab --repository-format docker --location europe-west1
gcloud builds submit . --config cloudbuild.yaml --substitutions "_IMAGE=$IMAGE"
gcloud run deploy diabetes-api --image "$IMAGE" --region europe-west1 --allow-unauthenticated --port 8000 \
  --min-instances 0 --max-instances 1 --set-env-vars THRESHOLD=0.5
gcloud run services describe diabetes-api --region europe-west1 --format 'value(status.url)'
gcloud run services delete diabetes-api --region europe-west1 --quiet
```

Un `.gcloudignore` est indispensable : sans lui, `gcloud` reprend le `.gitignore`, qui exclut `models/`.

## Google AI Studio et Gemini

```python
from google import genai

client = genai.Client(api_key=GEMINI_API_KEY)
response = client.models.generate_content(model="gemini-flash-latest", contents=prompt)
print(response.text)
```

| Où ranger la clé | Comment |
|---|---|
| En local | `.env` : `GEMINI_API_KEY=…` (ignoré par Git) |
| Streamlit Cloud | *Secrets* : `GEMINI_API_KEY = "…"` |
| Azure Container Apps | `az containerapp secret set` + `secretref:` |
| GitHub Actions | *Settings* → *Secrets and variables* → *Actions* |

Avant chaque push : `git grep -n "AIza"` ne doit rien trouver. Une clé commitée se révoque dans AI Studio.

| Erreur | Sens |
|---|---|
| `400 … API key not valid` | clé fausse ou révoquée |
| `404 … model not found` | nom de modèle inconnu : copier celui d'AI Studio |
| `429 RESOURCE_EXHAUSTED` | quota de l'offre gratuite atteint |
