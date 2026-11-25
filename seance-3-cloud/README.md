# Séance 3 · Mise en production dans le cloud

**Durée** : 3 h · **Slides** : [slides.html](slides.html) · **Labs** : [8 Streamlit Cloud](labs/lab-08-streamlit-cloud.md) · [9 Azure Container Apps](labs/lab-09-azure-container-apps.md) · [10 Cloud Run (optionnel)](labs/lab-10-cloud-run-optionnel.md) · [11 Gemini](labs/lab-11-gemini-ai-studio.md) · **Mémo** : [toutes les commandes de la séance](memo.md)

**Terminal** : Git Bash sous Windows, Terminal sous macOS et Linux. **Point de départ** : le projet `diabete-lab` poussé sur GitHub, avec sa CI verte et son image publique (séance 2).

À la fin de la séance, chaque étudiant a une application publique en ligne, une API conteneurisée déployée sur Azure, une vue d'ensemble de ce que proposent Azure ML et Vertex AI, et une brique d'IA générative branchée proprement dans son application.

> Les offres gratuites et étudiantes changent souvent. Les informations ci-dessous ont été vérifiées en novembre 2026 ; le formateur revérifie les pages de tarification la veille de la séance (voir [ressources/comparatif-cloud.md](../ressources/comparatif-cloud.md)).

## Déroulé

| Temps | Contenu | Support |
|---|---|---|
| 0:00 – 0:40 | Panorama : modèles de service, coûts, comparatif Azure / GCP / gratuit, Azure ML et Vertex AI, AI Studio | §1, §2 |
| 0:40 – 1:15 | Streamlit Community Cloud : chaque étudiant déploie son application | §3, Lab 8 |
| 1:15 – 2:00 | Azure : Container Apps depuis l'image de la CI ; tour d'Azure ML Studio | §4, Lab 9 |
| 2:00 – 2:25 | Google Cloud : Cloud Run en démonstration ; tour de Vertex AI | §5, Lab 10 |
| 2:25 – 2:50 | Google AI Studio : Gemini dans l'application, gestion des secrets | §6, Lab 11 |
| 2:50 – 3:00 | Supervision, coûts, checklist de mise en production | §7 |

## 1. Panorama : ce que vous gérez, ce que le cloud gère

![IaaS, PaaS, serverless](../assets/diagrams/cloud-modeles.svg)

| Modèle | Vous gérez | Exemples | Quand |
|---|---|---|---|
| **IaaS** (machine virtuelle) | tout, du système à l'application | Azure VM, Compute Engine | besoin de contrôle total, logiciels particuliers |
| **PaaS / conteneurs managés** | votre image Docker et sa configuration | Azure Container Apps, App Service, Cloud Run | une API ou un site web conteneurisé : notre cas |
| **Serverless / managé** | votre code ou votre modèle | Azure Functions, Cloud Functions, endpoints Azure ML et Vertex AI | fonctions courtes, modèles servis clé en main |

Trois notions qui reviennent partout :

- **Scale-to-zero** : aucune instance quand personne n'appelle le service, donc presque aucun coût, au prix d'un démarrage à froid de quelques secondes.
- **Région** : où tournent les serveurs. Pour Madagascar, `southafricanorth` (Johannesburg) est la plus proche ; `francecentral` ou `westeurope` sont souvent mieux dotées en services.
- **Facturation à l'usage** : CPU-secondes, Go-secondes, requêtes. Les offres gratuites couvrent largement une application de démonstration ; ce qui coûte, ce sont les ressources oubliées. Supprimez le groupe de ressources en fin de projet.

### Les cibles de la formation

| Cible | Quoi | Coût | Qui le fait |
|---|---|---|---|
| **Streamlit Community Cloud** | l'application Streamlit, depuis GitHub | gratuit, sans carte | tous (Lab 8) |
| **Azure Container Apps** | l'API conteneurisée, image de la CI | crédit Azure for Students, allocation gratuite mensuelle | tous (Lab 9) |
| **Google Cloud Run** | l'API conteneurisée | essai gratuit ou crédits enseignant | démonstration, Lab 10 optionnel |
| **Google AI Studio** | une clé Gemini pour l'application | gratuit (palier limité) | tous (Lab 11) |
| Render | l'API, alternative gratuite | plan gratuit avec mise en veille | documenté : `deploy/render.yaml` |

Hugging Face Spaces, longtemps la cible gratuite de référence pour les démonstrations ML, a restreint ses Spaces Docker et Gradio aux comptes payants courant 2026 : il n'est plus retenu ici. Les Spaces statiques restent gratuits.

## 2. Azure ML et Vertex AI : les plateformes ML managées

Déployer une API dans un conteneur, c'est le chemin générique. Les deux grands clouds proposent aussi des plateformes dédiées au cycle de vie du ML, qui reprennent exactement les étapes de la formation :

![Azure ML et Vertex AI](../assets/diagrams/azure-ml-vs-vertex.svg)

| Étape | Ce que vous avez fait | Azure ML | Vertex AI |
|---|---|---|---|
| Données | CSV + DVC | Data assets, datastores | Cloud Storage, BigQuery |
| Exploration | notebook local | Compute instance | Workbench, Colab Enterprise |
| Entraînement | `dvc repro` | Jobs (script, AutoML, pipelines) | Training (custom, AutoML, pipelines) |
| Suivi | MLflow local | MLflow intégré nativement | Experiments |
| Registre | `models/` + MLflow Registry | Model Registry (format MLflow) | Model Registry |
| Déploiement | FastAPI + Container Apps | Managed online endpoint | Endpoint |
| Supervision | `/health`, journaux | Monitoring, dérive des données | Model Monitoring |

Ce qu'il faut en retenir :

- Les deux **acceptent votre conteneur Docker** tel quel : le travail des séances 1 et 2 n'est pas perdu, il est la condition pour en profiter.
- Azure ML parle **MLflow nativement** : un `mlflow.log_model` dans un job Azure ML alimente son registre sans rien changer.
- Ces plateformes coûtent plus cher qu'un conteneur nu (calcul managé facturé à la minute) ; elles se justifient quand l'équipe a plusieurs modèles, des réentraînements réguliers et des besoins de gouvernance.
- En formation, nous les visitons en **démonstration** : le formateur montre un workspace Azure ML et un projet Vertex AI ; les étudiants pratiquent sur Container Apps.

## 3. Streamlit Community Cloud : le déploiement garanti

Gratuit, sans carte bancaire, connecté à GitHub : Streamlit clone votre dépôt, installe les dépendances, lance `streamlit run` et vous donne une URL `https://<nom>.streamlit.app`. Le guide complet est dans le fil rouge : [deploy/streamlit-cloud.md](../projet-fil-rouge/deploy/streamlit-cloud.md).

Déployer, c'est rendre explicite tout ce que votre machine fournissait en silence. Trois choses sont à régler.

**Les dépendances.** Streamlit Cloud cherche un fichier de dépendances d'abord dans le dossier du fichier principal, puis à la racine du dépôt ; dans un même dossier, `uv.lock` passe avant `requirements.txt` ([documentation](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/app-dependencies)). À la racine de votre projet, il prendrait donc `uv.lock` et installerait tous les groupes, MLflow et DVC compris. On génère un `app/requirements.txt`, à côté de `app/streamlit_app.py`, réduit au groupe `app` :

```bash
uv export --format requirements-txt --no-default-groups --group app --no-hashes --no-emit-project -o app/requirements.txt
```

À regénérer après chaque `uv add --group app …` ; choisissez Python 3.11 dans *Advanced settings* (3.12 par défaut).

**La configuration.** Pas de `.env` sur Streamlit Cloud : les réglages arrivent par ses *Secrets* et se lisent avec `st.secrets`. Une petite fonction `setting(nom)` lit la variable d'environnement si elle existe, sinon le secret, sinon une valeur par défaut : le même code marche partout.

**Le modèle.** Il n'est pas dans Git (DVC le gère, dans un remote local). Trois options, de la plus propre à la plus pratique :

1. **Mode API** : secret `API_URL` vers votre API Azure (Lab 9). L'application ne porte aucun modèle.
2. **Modèle téléchargé** : secret `MODEL_URL` vers un fichier `model.joblib` publié (asset d'une *release* GitHub, blob public). On sert exactement l'artefact validé.
3. **Repli de démonstration** : sans modèle, l'application s'entraîne au démarrage sur les données publiques du jeu Pima, avec un avertissement visible. Pratique pour réussir le déploiement en séance, à proscrire en vrai projet.

## 4. Azure : Container Apps et Azure ML

### Azure for Students

Avec un e-mail académique : 100 $ de crédit, pas de carte bancaire, services gratuits pendant 12 mois renouvelables. La vérification peut prendre du temps : c'est pour cela qu'elle figure dans les prérequis. Azure Container Apps dispose en plus d'une allocation gratuite mensuelle (CPU-secondes, Go-secondes, requêtes) largement suffisante pour une API de démonstration.

### Déployer l'API

![Déployer sur Azure Container Apps](../assets/diagrams/azure-deploy-flow.svg)

Les objets Azure, du plus large au plus précis :

| Objet | Rôle |
|---|---|
| **Abonnement** | votre compte Azure for Students et son crédit |
| **Groupe de ressources** `rg-diabetes-ml` | un dossier : tout ce qui concerne le projet ; le supprimer efface tout |
| **Environnement Container Apps** | le réseau et les journaux partagés par les applications |
| **Container App** `diabetes-api` | votre image, ses variables, son ingress HTTPS, ses règles de mise à l'échelle |
| **Azure Container Registry** (optionnel) | un registre privé ; `az acr build` construit l'image dans Azure, sans Docker local |

Le script du fil rouge fait tout cela : [deploy/azure/deploy.ps1](../projet-fil-rouge/deploy/azure/deploy.ps1) (ou `deploy.sh`). Son cœur :

```bash
az group create --name rg-diabetes-ml --location francecentral
az containerapp env create --name cae-diabetes-ml --resource-group rg-diabetes-ml --location francecentral
az containerapp create \
  --name diabetes-api --resource-group rg-diabetes-ml --environment cae-diabetes-ml \
  --image ghcr.io/<vous-en-minuscules>/<depot>/api:latest \
  --target-port 8000 --ingress external \
  --min-replicas 0 --max-replicas 1 --cpu 0.5 --memory 1.0Gi \
  --env-vars THRESHOLD=0.5
az containerapp show --name diabetes-api --resource-group rg-diabetes-ml --query properties.configuration.ingress.fqdn -o tsv
```

Toutes ces commandes et leurs options ont été vérifiées avec Azure CLI 2.93 et l'extension `containerapp` (novembre 2026). Le chemin du modèle n'est pas passé : `MODEL_PATH` est défini dans l'image. C'est aussi une précaution sous Git Bash, qui convertit en chemin Windows toute valeur d'argument commençant par `/` (`MSYS_NO_PATHCONV=1` désactive cette conversion).

Puis `https://<fqdn>/docs`. Mise à jour après un nouveau push : `az containerapp update --image …:<nouveau tag>`, ou le workflow [deploy-azure.yml](../projet-fil-rouge/.github/workflows/deploy-azure.yml) (★★).

Points d'attention :

- **Image privée** : par défaut un package ghcr.io est privé ; rendez-le public, ou passez `--registry-server ghcr.io --registry-username … --registry-password <PAT>`.
- **Pas de Docker local ?** `deploy.ps1 -UseAcr` construit l'image dans Azure Container Registry.
- **Journaux** : `az containerapp logs show -n diabetes-api -g rg-diabetes-ml --follow`.
- **Nettoyage** : `az group delete --name rg-diabetes-ml --yes --no-wait`.

### Tour d'Azure ML Studio (démonstration)

Dans [ml.azure.com](https://ml.azure.com) : un *workspace*, ses *Data assets*, une *Compute instance* avec VS Code, un *Job* lancé depuis un script (le même `train.py`, avec `mlflow.log_*` qui alimente directement l'onglet *Jobs*), le *Model registry*, et un *Managed online endpoint* qui expose le modèle avec une clé. Le formateur montre un endpoint déjà déployé et l'appelle depuis l'interface Streamlit en changeant `API_URL`.

## 5. Google Cloud : Cloud Run et Vertex AI

### Cloud Run

![Déployer sur Cloud Run](../assets/diagrams/gcp-cloud-run.svg)

Même logique qu'Azure Container Apps avec d'autres noms : **Cloud Build** construit l'image à partir du Dockerfile, **Artifact Registry** la stocke, **Cloud Run** la sert en HTTPS avec mise à l'échelle à zéro. Le script [deploy/gcp/deploy.sh](../projet-fil-rouge/deploy/gcp/deploy.sh) enchaîne les trois ; son cœur :

```bash
gcloud builds submit . --config deploy/gcp/cloudbuild.yaml --substitutions _IMAGE=$IMAGE
gcloud run deploy diabetes-api --image $IMAGE --region europe-west1 --allow-unauthenticated --port 8000 --min-instances 0
```

Cloud Run impose le port par la variable `PORT` : c'est pour cela que le Dockerfile lance `uvicorn … --port ${PORT}`.

Un piège : sans fichier `.gcloudignore`, `gcloud builds submit` reprend le `.gitignore`, qui exclut `models/`. L'image serait construite sans modèle. Le fil rouge et le lab 10 fournissent un `.gcloudignore` calqué sur `.dockerignore`.

Les crédits Google Cloud pour étudiants passent par l'enseignant (programme *Google Cloud for Education*, *Teaching credits*) ; l'essai gratuit individuel demande une carte bancaire. Le Lab 10 est donc optionnel : ceux qui ont un projet avec facturation le font, les autres suivent la démonstration.

### Tour de Vertex AI (démonstration)

![Vertex AI](../assets/diagrams/vertex-pipeline.svg)

Dans la console : *Workbench* (notebooks managés), *Training* (un job qui exécute votre conteneur ou AutoML), *Experiments*, *Model Registry*, *Endpoints* (prédiction en ligne, facturée au nœud-heure), *Model Monitoring*. Et, dans la même console, *Vertex AI Studio* donne accès aux modèles Gemini pour les entreprises, avec la facturation et la gouvernance du projet Google Cloud ; **Google AI Studio** en est la version légère et gratuite pour les développeurs individuels.

## 6. Google AI Studio : Gemini dans votre application

![De Google AI Studio à votre application](../assets/diagrams/ai-studio-flow.svg)

1. Dans [aistudio.google.com](https://aistudio.google.com), prototypez le prompt dans l'interface : vous voyez la réponse, vous ajustez.
2. *Get API key* : une clé par projet. Le palier gratuit suffit pour la formation ; ses limites de débit (requêtes par minute et par jour) changent régulièrement : consultez-les dans AI Studio.
3. La clé va dans un **secret** (`.env`, secrets Streamlit, variables Container Apps), jamais dans le code.
4. Le SDK `google-genai` l'utilise :

```python
from google import genai

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
response = client.models.generate_content(model="gemini-flash-latest", contents=prompt)
print(response.text)
```

`gemini-flash-latest` désigne toujours le modèle Flash le plus récent ; les noms de version changent souvent, copiez celui qu'affiche AI Studio si vous préférez figer une version.

Dans Streamlit, le bouton « Expliquer » doit être placé dans le bloc qui affiche le résultat gardé dans `st.session_state`, pas sous le bouton « Estimer » : un clic réexécute le script, et le premier bouton repasse à `False`. Et la bibliothèque `google-genai` doit figurer dans `app/requirements.txt`, sinon l'application déployée échoue à l'import.

Le fil rouge ajoute un bouton « Expliquer cette estimation » : le prompt contient les mesures du patient et la probabilité, Gemini rédige quatre phrases d'explication pédagogique. Deux garde-fous : le prompt rappelle qu'il s'agit d'un exercice, pas d'un avis médical ; et sur le palier gratuit, **Google peut utiliser vos requêtes pour améliorer ses modèles**, donc aucune donnée personnelle n'y transite.

### Les secrets, une bonne fois pour toutes

![Les secrets](../assets/diagrams/secrets-flow.svg)

Le code lit `os.environ["GEMINI_API_KEY"]`. Ce qui change d'une plateforme à l'autre, c'est la façon de fournir la valeur : `.env` en local, *Secrets* sur Streamlit Cloud, `--secrets` et `--env-vars` sur Container Apps, *Secrets* du dépôt pour GitHub Actions. Une clé commitée est compromise : révoquez-la dans AI Studio et créez-en une autre.

## 7. Après le déploiement

![Checklist avant déploiement](../assets/diagrams/checklist-prod.svg)

- **Supervision minimale** : `/health` interrogé par la plateforme, journaux centralisés (`az containerapp logs`, Cloud Logging), une alerte si le service ne répond plus.
- **Coûts** : scale-to-zero, une seule réplique maximum en démonstration, suppression du groupe de ressources en fin de projet, budget avec alerte dans le portail.
- **Dérive** : les données réelles finissent par ne plus ressembler aux données d'entraînement ; surveiller la distribution des entrées et les retours terrain, puis réentraîner. C'est la boucle complète :

![La boucle MLOps](../assets/diagrams/boucle-mlops.svg)

La [checklist de mise en production](../ressources/checklist-mise-en-production.md) résume les huit vérifications en une page.

## Auto-évaluation

Répondez sans regarder le cours ; les réponses sont publiées avec les solutions des labs.

1. Quelle différence entre IaaS, PaaS et serverless, et dans quelle catégorie tombent Azure Container Apps et Cloud Run ?
2. Pourquoi Streamlit Cloud installerait-il MLflow et DVC si l'on ne crée pas `app/requirements.txt` ?
3. Votre application lit `API_URL` avec `os.getenv` ; elle marche en local mais ignore le secret saisi sur Streamlit Cloud. Pourquoi, et que faire ?
4. Pourquoi déploie-t-on l'image avec `--min-replicas 0`, et quel en est le prix ?
5. Pourquoi déployer un tag SHA plutôt que `latest` ?
6. Le lab 9 ne passe pas `MODEL_PATH=/app/models/model.joblib` à `az containerapp create`. Donnez deux raisons.
7. Sans `.gcloudignore`, l'image construite par Cloud Build démarre mais `/health` répond `degraded`. Pourquoi ?
8. Où ranger la clé Gemini en local, sur Streamlit Cloud, sur Azure ? Que faire si elle a été commitée ?
9. Quelle différence entre Google AI Studio et Vertex AI Studio pour un projet qui manipule des données de patients réelles ?

## Récapitulatif de la formation

| Séance | Vous savez maintenant |
|---|---|
| 1 | rendre un projet reproductible : uv, DVC, MLflow |
| 2 | en faire un service : FastAPI, Streamlit, Docker, CI |
| 3 | le mettre en ligne : Streamlit Cloud, Azure Container Apps, Cloud Run ; situer Azure ML, Vertex AI et AI Studio ; brancher Gemini sans exposer de clé |

Pour continuer : [ressources/liens.md](../ressources/liens.md).

## Pour aller plus loin (★★)

- **Déploiement continu** : le workflow `deploy-azure.yml` du fil rouge, déclenché à la main puis automatiquement sur un tag.
- **Remote DVC sur Azure Blob** : un compte de stockage dans le même groupe de ressources, `dvc remote add -d azure azure://dvc/diabetes`, et la CI fait `dvc pull` au lieu de réentraîner.
- **Endpoint Azure ML** : déployer le même modèle MLflow comme *managed online endpoint* et comparer latence, coût et effort avec Container Apps.
- **Authentification** : protéger l'API (clé d'API dans un en-tête, puis OAuth), restreindre CORS à l'origine de l'interface.
- **Observabilité** : OpenTelemetry dans FastAPI, Application Insights ou Cloud Trace.
