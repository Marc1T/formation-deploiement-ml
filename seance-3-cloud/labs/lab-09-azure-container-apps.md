# Lab 9 · Déployer l'API sur Azure Container Apps

**Durée** : 45 min · **Objectif** : votre API FastAPI, telle que construite par la CI, répond en HTTPS depuis Azure ; votre application Streamlit Cloud l'utilise en mode API.

**Terminal** : Git Bash sous Windows, Terminal sous macOS et Linux.

**Point de départ** :

- un compte **Azure for Students** vérifié ([portal.azure.com](https://portal.azure.com) affiche l'abonnement « Azure for Students ») ;
- [Azure CLI](https://learn.microsoft.com/cli/azure/install-azure-cli) installé : `az --version` ;
- l'image du lab 7, **publique** : `ghcr.io/<votre-compte-en-minuscules>/diabete-lab/api:latest` ;
- l'application du lab 8 en ligne sur Streamlit Cloud.

Scripts de référence : [projet-fil-rouge/deploy/azure](../../projet-fil-rouge/deploy/azure).

Dans tout le lab, remplacez `<image>` par le nom complet de votre image, **en minuscules**. Pour éviter de le retaper :

```bash
IMAGE=ghcr.io/<votre-compte-en-minuscules>/diabete-lab/api:latest
```

## ★ Parcours de base

### 1. Se connecter et préparer l'abonnement

```bash
az login
az account show --query "{abonnement:name, etat:state}" -o table
az extension add --name containerapp --upgrade
az provider register --namespace Microsoft.App --wait
az provider register --namespace Microsoft.OperationalInsights --wait
```

`az login` ouvre le navigateur. Les deux `provider register` activent les services la première fois (une à deux minutes).

> **Point de contrôle** : l'abonnement affiché est « Azure for Students », état `Enabled`.

### 2. Un groupe de ressources

```bash
az group create --name rg-diabetes-ml --location francecentral
```

Un groupe de ressources est un dossier : tout le projet dedans, et un seul `az group delete` efface tout. La région `francecentral` est bien dotée ; `southafricanorth` est la plus proche de Madagascar.

### 3. L'environnement Container Apps

```bash
az containerapp env create --name cae-diabetes-ml --resource-group rg-diabetes-ml --location francecentral
```

Il porte le réseau et les journaux (Log Analytics) de vos applications. Comptez deux à trois minutes.

### 4. L'application

```bash
az containerapp create \
  --name diabetes-api \
  --resource-group rg-diabetes-ml \
  --environment cae-diabetes-ml \
  --image "$IMAGE" \
  --target-port 8000 \
  --ingress external \
  --min-replicas 0 --max-replicas 1 \
  --cpu 0.5 --memory 1.0Gi \
  --env-vars THRESHOLD=0.5
```

Lisez chaque option : le port qu'écoute votre conteneur, l'exposition publique, la mise à l'échelle de 0 à 1 réplique, les ressources, la configuration par variables d'environnement. Le chemin du modèle n'est pas passé ici : `MODEL_PATH` est déjà défini dans l'image (lab 6).

### 5. Tester

```bash
FQDN=$(az containerapp show --name diabetes-api --resource-group rg-diabetes-ml --query properties.configuration.ingress.fqdn -o tsv)
echo "https://$FQDN/docs"
curl "https://$FQDN/health"
curl -X POST "https://$FQDN/predict" -H "Content-Type: application/json" \
  -d '{"pregnancies":2,"glucose":138,"blood_pressure":72,"skin_thickness":35,"insulin":120,"bmi":33.6,"diabetes_pedigree":0.62,"age":45}'
az containerapp logs show --name diabetes-api --resource-group rg-diabetes-ml --tail 30
```

La première requête met quelques secondes : l'application remonte de zéro réplique (démarrage à froid). Les suivantes sont immédiates.

> **Point de contrôle** : `{"status":"ok"}` puis `{"prediction":1,"probability":0.5838}` : exactement la valeur obtenue sur votre machine au lab 4, depuis un serveur à Paris.

### 6. Brancher l'application Streamlit Cloud sur l'API

Sur [share.streamlit.io](https://share.streamlit.io) : votre application → **Settings** → **Secrets**, collez :

```toml
API_URL = "https://<votre-fqdn>"
```

Enregistrez : l'application redémarre.

> **Point de contrôle** : l'estimation affiche `58%` et « Mode API · https://diabetes-api… », sans avertissement de démonstration. L'interface tourne chez Streamlit, l'API chez Microsoft, et le modèle est celui que votre CI a construit.

### 7. Mettre à jour, puis nettoyer

Après un nouveau push, la CI publie une nouvelle image. Déployez-la avec un **tag immuable** (le SHA court du commit, visible dans l'onglet *Packages*) :

```bash
az containerapp update --name diabetes-api --resource-group rg-diabetes-ml --image ghcr.io/<compte>/diabete-lab/api:<sha>
az containerapp revision list --name diabetes-api --resource-group rg-diabetes-ml -o table
```

Chaque mise à jour crée une *révision* : on peut revenir à la précédente en une commande.

Quand le projet est terminé (pas aujourd'hui si vous voulez garder la démonstration) :

```bash
az group delete --name rg-diabetes-ml --yes --no-wait
```

## ★★ Aller plus loin

- **Sans Docker local ni ghcr** : `az acr create` puis `az acr build` construisent l'image dans Azure Container Registry (voir `-UseAcr` dans [deploy.ps1](../../projet-fil-rouge/deploy/azure/deploy.ps1)). Quelles options de `containerapp create` changent ?
- **Image privée** : gardez le package ghcr privé et ajoutez `--registry-server ghcr.io --registry-username <compte> --registry-password <jeton read:packages>`. Où Azure stocke-t-il ce mot de passe ? (`az containerapp show … --query properties.configuration.secrets`)
- **Déploiement continu** : le workflow [deploy-azure.yml](../../projet-fil-rouge/.github/workflows/deploy-azure.yml) du fil rouge, avec un principal de service dans le secret `AZURE_CREDENTIALS`.
- **Remote DVC sur Azure Blob** : un compte de stockage dans le même groupe, `uv add --group mlops "dvc[azure]"`, `dvc remote add -d azure azure://dvc/diabetes`, la chaîne de connexion avec `dvc remote modify --local`, puis `dvc push`. Dans la CI, un `dvc pull` remplace alors le téléchargement des données publiques.
- **Tour d'Azure ML** (démonstration du formateur) : créez un workspace dans le même groupe et chargez `diabetes.csv` comme *Data asset*. Qu'est-ce qui ressemble à DVC ? À MLflow ?

## Dépannage

| Symptôme | Cause | Solution |
|---|---|---|
| `az: command not found` | Azure CLI non installé, ou terminal ouvert avant l'installation | installer, rouvrir le terminal |
| `SubscriptionNotFound`, aucun abonnement | compte Azure for Students pas encore validé | vérifier sur portal.azure.com ; voir le formateur |
| `MANIFEST_UNKNOWN` ou `unauthorized` au téléchargement de l'image | package ghcr privé, ou nom d'image faux | le rendre public ; copier le nom exact de l'onglet *Packages* |
| `invalid reference format: repository name must be lowercase` | majuscule dans le nom de l'image | tout en minuscules |
| L'application démarre puis s'arrête en boucle | le conteneur n'écoute pas `--target-port` | `--target-port 8000`, comme `EXPOSE` dans l'image |
| `/health` répond `degraded` | modèle absent de l'image | vérifier que la CI lance `dvc repro` avant `docker build` |
| Première requête très lente | démarrage à froid depuis 0 réplique | normal ; `--min-replicas 1` l'évite mais consomme du crédit en continu |
| Une variable contient `C:/Program Files/Git/…` | Git Bash convertit les valeurs qui commencent par `/` | ne pas passer de chemin absolu en argument, ou préfixer la commande par `MSYS_NO_PATHCONV=1` |

## À retenir

- **Trois objets suffisent** : un groupe de ressources, un environnement, une application ; et l'image de votre CI tourne sur Internet avec HTTPS, journaux et scale-to-zero.
- **On déploie une image, on la configure par des variables** : jamais une image différente par environnement.
- **Un tag immuable par déploiement** (SHA) et des révisions : on sait ce qui tourne et on peut revenir en arrière.
- **Ce qui est créé se paie** : `min-replicas 0` en démonstration, et `az group delete` en fin de projet.

## Solution

Solution complète : publiée après la séance.
