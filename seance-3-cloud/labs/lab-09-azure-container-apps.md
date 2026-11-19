# Lab 9 · Déployer l'API sur Azure Container Apps

**Durée** : 45 min · **Objectif** : votre API FastAPI, telle que construite par la CI, répond en HTTPS depuis Azure ; votre application Streamlit Cloud l'utilise en mode API.

Prérequis : un compte **Azure for Students** vérifié, [Azure CLI](https://learn.microsoft.com/cli/azure/install-azure-cli) installé (`az --version`), l'image `ghcr.io/<vous>/<depot>/api:latest` publiée par le lab 7 et rendue **publique** (page du package → *Package settings* → *Change visibility*). Scripts de référence : [projet-fil-rouge/deploy/azure](../../projet-fil-rouge/deploy/azure).

## ★ Parcours de base

### 1. Se connecter et choisir l'abonnement

```bash
az login                                   # ouvre le navigateur
az account show --query "{abonnement:name, id:id}" -o table
az extension add --name containerapp --upgrade
az provider register --namespace Microsoft.App --wait
az provider register --namespace Microsoft.OperationalInsights --wait
```

L'abonnement doit être « Azure for Students ». Les deux `provider register` activent les services la première fois (une à deux minutes).

### 2. Un groupe de ressources

```bash
az group create --name rg-diabetes-ml --location francecentral
```

Un groupe de ressources est un dossier : tout le projet dedans, et `az group delete` efface tout d'un coup. Choisissez la région une fois pour toutes (`francecentral`, `westeurope`, ou `southafricanorth`).

### 3. L'environnement Container Apps

```bash
az containerapp env create --name cae-diabetes-ml --resource-group rg-diabetes-ml --location francecentral
```

Il porte le réseau et les journaux (Log Analytics) de vos applications. Comptez deux minutes.

### 4. L'application

```bash
az containerapp create \
  --name diabetes-api \
  --resource-group rg-diabetes-ml \
  --environment cae-diabetes-ml \
  --image ghcr.io/<vous>/<depot>/api:latest \
  --target-port 8000 \
  --ingress external \
  --min-replicas 0 --max-replicas 1 \
  --cpu 0.5 --memory 1.0Gi \
  --env-vars MODEL_PATH=/app/models/model.joblib THRESHOLD=0.5
```

(PowerShell : remplacez les `\` de fin de ligne par des accents graves `` ` ``, ou mettez tout sur une ligne.)

Lisez chaque option : le port que votre conteneur écoute, l'exposition publique, la mise à l'échelle de 0 à 1 réplique, les ressources, la configuration par variables d'environnement.

### 5. Tester

```bash
az containerapp show --name diabetes-api --resource-group rg-diabetes-ml \
  --query properties.configuration.ingress.fqdn -o tsv
```

Ouvrez `https://<fqdn>/docs` : la première requête met quelques secondes (démarrage à froid depuis zéro réplique), les suivantes sont immédiates. Puis :

```bash
curl https://<fqdn>/health
curl -X POST https://<fqdn>/predict -H "Content-Type: application/json" \
  -d '{"pregnancies":2,"glucose":138,"blood_pressure":72,"skin_thickness":35,"insulin":120,"bmi":33.6,"diabetes_pedigree":0.62,"age":45}'
az containerapp logs show --name diabetes-api --resource-group rg-diabetes-ml --tail 30
```

### 6. Brancher l'application Streamlit Cloud

Sur [share.streamlit.io](https://share.streamlit.io) : *Manage app → Settings → Secrets*, ajoutez `API_URL = "https://<fqdn>"`, enregistrez. L'application redémarre en mode API : la barre latérale indique l'API et sa version du modèle. Vous avez une interface sur Streamlit Cloud qui parle à une API sur Azure.

### 7. Mettre à jour, puis nettoyer

Après un nouveau push (nouvelle image) :

```bash
az containerapp update --name diabetes-api --resource-group rg-diabetes-ml --image ghcr.io/<vous>/<depot>/api:latest
```

Avec `latest`, forcez une nouvelle révision si l'image a le même tag : `--revision-suffix v2`. Mieux : déployez un tag immuable (SHA du commit).

Quand vous avez fini le projet (pas aujourd'hui si vous voulez garder la démo) :

```bash
az group delete --name rg-diabetes-ml --yes --no-wait
```

## ★★ Aller plus loin

- **Sans Docker local, sans ghcr** : `.\deploy\azure\deploy.ps1 -UseAcr` construit l'image dans Azure Container Registry avec `az acr build` et la déploie. Regardez le script : quelles options changent ?
- **Image privée** : gardez le package ghcr privé et passez `--registry-server ghcr.io --registry-username <vous> --registry-password <PAT read:packages>`. Où Azure stocke-t-il ce mot de passe ? (`az containerapp show … --query properties.configuration.secrets`)
- **Déploiement continu** : configurez `AZURE_CREDENTIALS` (voir l'en-tête de [deploy-azure.yml](../../projet-fil-rouge/.github/workflows/deploy-azure.yml)) et lancez le workflow depuis l'onglet Actions.
- **Remote DVC sur Azure Blob** : `az storage account create`, un conteneur `dvc`, puis `uv add "dvc[azure]"`, `dvc remote add -d azure azure://dvc/diabetes`, `dvc remote modify --local azure connection_string "$(az storage account show-connection-string …)"`, `dvc push`.
- **Tour d'Azure ML** (démonstration du formateur) : créez un workspace dans le même groupe de ressources et uploadez `data/raw/diabetes.csv` comme *Data asset*. Qu'est-ce qui ressemble à DVC ? À MLflow ?

## Dépannage

| Symptôme | Cause | Solution |
|---|---|---|
| `az: command not found` | Azure CLI non installé ou terminal non rouvert | installer, rouvrir le terminal |
| `(SubscriptionNotFound)` ou pas d'abonnement | compte Azure for Students pas encore validé | vérifier sur portal.azure.com ; voir le formateur |
| `MANIFEST_UNKNOWN` ou `unauthorized` au pull de l'image | package ghcr privé ou nom d'image faux | rendre public ; vérifier le nom exact dans l'onglet Packages |
| L'application démarre puis s'arrête | le conteneur écoute un autre port que `--target-port` | `PORT=8000` dans l'image et `--target-port 8000` |
| `/health` dit `degraded` | `MODEL_PATH` faux | `/app/models/model.joblib` (chemin dans l'image, pas sur votre machine) |
| Première requête très lente | démarrage à froid (0 réplique) | normal ; `--min-replicas 1` pour l'éviter, mais ça consomme du crédit en continu |

## Ce qu'il faut retenir

Un groupe de ressources, un environnement, une application : trois commandes, et l'image de votre CI tourne sur Internet avec HTTPS, journaux et scale-to-zero. La configuration passe par des variables, jamais par une image différente. Solution : publiée après la séance.
