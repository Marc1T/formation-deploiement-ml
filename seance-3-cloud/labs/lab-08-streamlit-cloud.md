# Lab 8 · Déployer l'application sur Streamlit Community Cloud

**Durée** : 35 min · **Objectif** : une URL publique `https://<nom>.streamlit.app` qui sert votre application, gratuitement et sans carte bancaire.

**Terminal** : Git Bash sous Windows, Terminal sous macOS et Linux.

**Point de départ** : le projet `diabete-lab` du lab 7, poussé sur GitHub dans un dépôt **public** ; un compte sur [share.streamlit.io](https://share.streamlit.io) connecté à GitHub. Guide de référence : [projet-fil-rouge/deploy/streamlit-cloud.md](../../projet-fil-rouge/deploy/streamlit-cloud.md).

## Ce que fait Streamlit Cloud, et les trois problèmes à régler

Streamlit Cloud clone votre dépôt, installe les dépendances, lance `streamlit run` sur votre fichier principal. Trois choses ne marcheront pas telles quelles :

1. **Les dépendances.** Il cherche un fichier de dépendances d'abord **à côté du fichier principal**, puis à la racine ; à la racine, il prendrait `uv.lock` et installerait tous vos groupes, DVC et MLflow compris. On lui donne un `app/requirements.txt` réduit au groupe `app`.
2. **Le modèle.** `models/model.joblib` n'est pas dans Git, et les données sont dans votre remote DVC local. L'application doit savoir se débrouiller sans.
3. **La configuration.** Pas de fichier `.env` sur Streamlit Cloud : les réglages (`API_URL`, plus tard la clé Gemini) arrivent par ses *Secrets*, à lire avec `st.secrets`.

## ★ Parcours de base

### 1. Lire la configuration dans l'environnement ou dans les secrets

Dans `app/streamlit_app.py`, remplacez les deux lignes `API_URL = …` et `MODEL_PATH = …` par :

```python
def setting(name: str, default: str = "") -> str:
    """Variable d'environnement, sinon secret Streamlit, sinon valeur par défaut."""
    if os.getenv(name):
        return os.environ[name]
    try:
        return str(st.secrets.get(name, default))
    except FileNotFoundError:      # aucun fichier de secrets : cas normal en local
        return default


API_URL = setting("API_URL").rstrip("/")
MODEL_PATH = setting("MODEL_PATH", str(ROOT / "models" / "model.joblib"))
DATA_URL = "https://raw.githubusercontent.com/Marc1T/formation-deploiement-ml/main/projet-fil-rouge/data/raw/diabetes.csv"
```

### 2. Un modèle de démonstration quand le vrai manque

Remplacez la fonction `load_predictor` par ces deux fonctions :

```python
def train_demo_model(path: Path) -> None:
    """Repli de démonstration : entraîne un modèle sur les données publiques du jeu Pima."""
    import joblib
    import numpy as np
    import pandas as pd
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.impute import SimpleImputer
    from sklearn.pipeline import Pipeline
    from sklearn.preprocessing import StandardScaler

    from diabete_lab.prepare import ZERO_MEANS_MISSING

    df = pd.read_csv(DATA_URL)
    df[ZERO_MEANS_MISSING] = df[ZERO_MEANS_MISSING].replace(0, np.nan)
    pipe = Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", StandardScaler()),
        ("clf", RandomForestClassifier(n_estimators=200, max_depth=6, random_state=42)),
    ]).fit(df.drop(columns="outcome"), df["outcome"])
    path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(pipe, path)


@st.cache_resource(show_spinner="Chargement du modèle…")
def load_predictor() -> tuple[Predictor, bool]:
    path = Path(MODEL_PATH)
    demo = not path.exists()
    if demo:
        train_demo_model(path)
    return Predictor(path), demo
```

Et dans `predict`, la dernière ligne devient :

```python
    predictor, demo = load_predictor()
    if demo:
        st.warning("Modèle de démonstration entraîné au démarrage : le modèle versionné est absent.")
    return predictor.predict_one(values)
```

En local rien ne change : votre modèle existe, il est chargé. Vérifiez :

```bash
uv run streamlit run app/streamlit_app.py
```

> **Point de contrôle** : toujours `58%` et « Mode local », sans avertissement.

Ce repli sert à réussir le déploiement aujourd'hui. Dans un vrai projet, le modèle servi est un artefact versionné (release, remote DVC, registre MLflow, ou l'API de la séance 2), jamais un réentraînement silencieux.

### 3. Les dépendances pour Streamlit Cloud

```bash
uv export --format requirements-txt --no-default-groups --group app --no-hashes --no-emit-project -o app/requirements.txt
grep -E "^(streamlit|scikit-learn|pandas|mlflow|dvc)==" app/requirements.txt
```

> **Point de contrôle** : `streamlit`, `scikit-learn` et `pandas` sont listés, `mlflow` et `dvc` ne le sont pas.

```bash
git add -A
git commit -m "Prêt pour Streamlit Cloud : secrets, repli, requirements"
git push
```

### 4. Créer l'application

1. [share.streamlit.io](https://share.streamlit.io) → **Create app** → **Deploy a public app from GitHub**.
2. Dépôt : `<votre-compte>/diabete-lab` · Branche : `main` · Fichier principal : `app/streamlit_app.py`.
3. URL : choisissez un nom, par exemple `diabete-<prenom>`.
4. **Advanced settings** → **Python version** : `3.11` (celle du projet ; Streamlit Cloud propose 3.12 par défaut). Laissez les *Secrets* vides pour l'instant.
5. **Deploy**.

Les journaux de construction défilent (deux à quatre minutes la première fois). Vérifiez qu'ils mentionnent `app/requirements.txt`.

> **Point de contrôle** : l'application s'ouvre ; au premier clic, l'avertissement « Modèle de démonstration » apparaît et la probabilité vaut `61%` (le modèle de démonstration est entraîné sur toutes les données, pas seulement sur le jeu d'entraînement : il diffère un peu du vôtre). Ouvrez l'URL sur votre téléphone : elle est publique.

### 5. Mettre à jour

Changez le titre de l'application, commitez, poussez : Streamlit Cloud redéploie tout seul à chaque push sur `main`.

Au lab 9, vous ajouterez le secret `API_URL` : l'application utilisera alors votre API sur Azure et son vrai modèle.

## ★★ Aller plus loin

- **Simuler Streamlit Cloud en local** : un environnement neuf, installé uniquement depuis `app/requirements.txt`, sans le paquet du projet ni le modèle.

  ```bash
  uv venv ../cloud-test --python 3.11
  uv pip install --python ../cloud-test -r app/requirements.txt
  mv models models.bak
  MODEL_PATH=models/model.joblib ../cloud-test/Scripts/python -m streamlit run app/streamlit_app.py   # macOS/Linux : ../cloud-test/bin/python
  ```

  L'avertissement de démonstration apparaît, avec `61%`. Remettez ensuite votre modèle : `rm -rf models && mv models.bak models`.
- **Servir le vrai modèle sans API** : publiez `models/model.joblib` comme fichier d'une *release* GitHub, ajoutez un secret `MODEL_URL`, et téléchargez-le dans `load_predictor` quand il manque (voir le fil rouge).
- **Thème** : un fichier `.streamlit/config.toml` à la racine du dépôt est pris en compte.

## Dépannage

| Symptôme | Cause | Solution |
|---|---|---|
| Les journaux installent MLflow, DVC, ou tout le projet | `requirements.txt` absent du dossier `app/` | `uv export … -o app/requirements.txt`, commit, push, *Reboot* |
| `ModuleNotFoundError: diabete_lab` | `src/` absent du chemin | garder le `sys.path.insert` en tête du script ; vérifier que `src/` est dans le dépôt |
| `ModuleNotFoundError` sur une bibliothèque | dépendance ajoutée sans régénérer `app/requirements.txt` | relancer `uv export`, commit, push |
| `StreamlitSecretNotFoundError` en local | `st.secrets` lu hors du `try` | utiliser la fonction `setting` |
| Erreur de version de Python | Python par défaut (3.12) | *Settings → General → Python version* : 3.11, puis *Reboot* |
| Application endormie | pas de visite depuis plusieurs jours | un clic la réveille ; normal sur l'offre gratuite |

## À retenir

- **Déployer, c'est rendre explicite tout ce que votre machine fournissait en silence** : dépendances, modèle, configuration.
- **Un fichier de dépendances à côté du fichier principal**, généré depuis `uv.lock` : il prime sur ceux de la racine.
- **La configuration vient de l'environnement ou des secrets**, jamais du code ; une seule fonction (`setting`) lit les deux.
- **Le repli de démonstration est un filet, pas une méthode** : le modèle servi en vrai est un artefact versionné.

## Solution

Solution complète : publiée après la séance.
