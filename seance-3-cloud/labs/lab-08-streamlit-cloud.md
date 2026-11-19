# Lab 8 · Déployer l'application sur Streamlit Community Cloud

**Durée** : 30 min · **Objectif** : une URL publique `https://<nom>.streamlit.app` qui sert votre application, gratuitement et sans carte bancaire.

Prérequis : un dépôt GitHub **public** contenant votre projet (lab 7), un compte sur [share.streamlit.io](https://share.streamlit.io) connecté à GitHub. Guide de référence : [projet-fil-rouge/deploy/streamlit-cloud.md](../../projet-fil-rouge/deploy/streamlit-cloud.md).

## ★ Parcours de base

### 1. Préparer le dépôt

Streamlit Cloud installe les dépendances depuis `requirements.txt`. Générez-le depuis `uv.lock` pour qu'il corresponde exactement à votre environnement :

```bash
uv export --format requirements-txt --no-dev --no-default-groups --group app --no-hashes --no-emit-project -o requirements.txt
git add requirements.txt && git commit -m "requirements.txt pour Streamlit Cloud" && git push
```

(Si vous n'avez pas de groupe `app` : `uv export --format requirements-txt --no-dev --no-hashes --no-emit-project -o requirements.txt`, puis retirez à la main `mlflow` et `dvc`, inutiles pour l'application et lourds à installer.)

Vérifiez que `app/streamlit_app.py` ajoute `src/` au chemin Python (voir le lab 5) : sur Streamlit Cloud, votre package n'est pas installé.

### 2. Le modèle

`models/model.joblib` n'est pas dans Git (DVC le gère). Choisissez :

- **Mode API** (si votre API est déjà en ligne) : vous donnerez `API_URL` en secret à l'étape 4.
- **Repli de démonstration** : l'application du fil rouge s'entraîne au démarrage depuis `data/raw/diabetes.csv` quand le modèle manque. Si votre application ne le fait pas, ajoutez ce comportement (voir `load_predictor` dans le fil rouge) ou utilisez l'option suivante.
- **★★ Modèle téléchargé** : publiez `model.joblib` comme asset d'une *release* GitHub, puis secret `MODEL_URL`.

### 3. Créer l'application

1. [share.streamlit.io](https://share.streamlit.io) → **Create app** → **Deploy a public app from GitHub**.
2. Dépôt : le vôtre · Branche : `main` · Fichier principal : `app/streamlit_app.py`.
3. URL : choisissez un nom (par exemple `diabete-<prenom>`).

### 4. Advanced settings

- **Python version** : `3.11`.
- **Secrets** (format TOML) :
  ```toml
  # API_URL = "https://diabetes-api.<region>.azurecontainerapps.io"
  # GEMINI_API_KEY = "AIza..."
  ```
  Laissez tout commenté pour l'instant : mode local. Vous reviendrez ici au lab 9 et au lab 11.

### 5. Deploy

Les journaux de construction défilent (2 à 4 minutes la première fois). Quand l'application s'affiche, testez une estimation, puis ouvrez l'URL depuis votre téléphone : elle est publique.

### 6. Mettre à jour

Modifiez le titre de l'application, commitez, poussez : Streamlit Cloud redéploie automatiquement à chaque push sur `main`. C'est du déploiement continu sans rien configurer.

## ★★ Aller plus loin

- **Modèle en release** : sur GitHub, *Releases → Draft a new release*, tag `v0.1.0`, joignez `models/model.joblib`. Copiez l'URL de l'asset dans le secret `MODEL_URL`. Redémarrez l'application (*Manage app → Reboot*) : elle télécharge et sert exactement ce fichier. Comparez avec le repli : quel est l'avantage pour la traçabilité ?
- **Thème** : `.streamlit/config.toml` dans le dépôt est pris en compte.
- **Analyse** : *Manage app → Analytics* montre les visites. Que se passe-t-il si l'application reste sans visite plusieurs jours ?

## Dépannage

| Symptôme | Cause | Solution |
|---|---|---|
| `ModuleNotFoundError: diabete_lab` | `src/` pas dans le chemin | le `sys.path.insert` en tête du script ; vérifier que `src/` est bien dans le dépôt |
| Installation très longue ou mémoire dépassée | `mlflow` ou `dvc` dans `requirements.txt` | regénérer avec `--group app` seulement |
| `FileNotFoundError: models/model.joblib` | modèle absent, pas de repli | mode API, `MODEL_URL`, ou le repli d'entraînement |
| Application « sleeping » | pas de visite depuis plusieurs jours | un clic la réveille ; normal sur le plan gratuit |
| Le secret n'est pas lu | faute de frappe ou guillemets manquants dans le TOML | relire la syntaxe `CLE = "valeur"` |

## Ce qu'il faut retenir

Déployer une application Streamlit, c'est trois choses : un dépôt public, un `requirements.txt` cohérent avec le lock, et la configuration en secrets. Le modèle servi doit venir d'un artefact versionné. Solution : publiée après la séance.
