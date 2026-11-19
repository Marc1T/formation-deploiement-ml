# Séance 1 · Du notebook au projet reproductible

**Durée** : 3 h · **Slides** : [slides.html](slides.html) · **Labs** : [1 uv](labs/lab-01-uv.md) · [2 DVC](labs/lab-02-dvc.md) · [3 MLflow](labs/lab-03-mlflow.md)

À la fin de la séance, votre modèle n'est plus « un notebook qui marche chez vous » mais un projet que n'importe qui (un collègue, un serveur, vous dans six mois) peut réinstaller, relancer et comparer.

## Déroulé

| Temps | Contenu | Support |
|---|---|---|
| 0:00 – 0:30 | Pourquoi déployer ? La chaîne complète, le tour des outils | §1 |
| 0:30 – 1:15 | Git et GitHub express, puis uv | §2, §3, Lab 1 |
| 1:15 – 2:00 | DVC : versionner les données et le pipeline | §4, Lab 2 |
| 2:00 – 2:45 | MLflow : tracer et comparer les expériences | §5, Lab 3 |
| 2:45 – 3:00 | Récapitulatif, devoir pour la séance 2 | §6 |

## 1. Pourquoi déployer ?

Un modèle qui n'est pas accessible ne sert à personne. Entre le notebook et l'application utilisée, il y a une chaîne d'étapes, et chacune a ses outils :

![La chaîne complète](../assets/diagrams/chaine-complete.svg)

Cette première séance s'occupe de la partie gauche : rendre le projet **reproductible**. Les trois problèmes classiques du notebook seul, et ce qui les remplace :

![Notebook contre projet](../assets/diagrams/notebook-vs-projet.svg)

Les trois outils de la séance répondent chacun à une question :

| Question | Outil | Ce qu'il versionne |
|---|---|---|
| Quel code, quelles versions de bibliothèques ? | Git + **uv** | le code, `pyproject.toml`, `uv.lock` |
| Quelles données, quel pipeline ? | **DVC** | les fichiers de données et de modèle, le graphe des étapes |
| Quelle expérience a donné quel résultat ? | **MLflow** | paramètres, métriques, artefacts de chaque exécution |

## 2. Git et GitHub en 20 minutes (★ rappel)

Git enregistre l'historique du code ; GitHub l'héberge et fera tourner notre intégration continue en séance 2. Le strict nécessaire :

```bash
git init -b main                 # démarre un dépôt
git status                       # qu'est-ce qui a changé ?
git add .                        # prépare les fichiers
git commit -m "Projet initial"   # enregistre un instantané
git log --oneline                # l'historique
```

Pour publier sur GitHub : créer un dépôt vide sur github.com, puis

```bash
git remote add origin https://github.com/<vous>/<depot>.git
git push -u origin main
```

Trois réflexes :

1. **Un `.gitignore` dès le début** : `.venv/`, `__pycache__/`, `.env`, `mlruns/`, et les gros fichiers de données (DVC s'en chargera).
2. **Des commits petits et nommés** : « Ajoute l'étape prepare » vaut mieux que « maj ».
3. **Jamais de secret dans Git** : une clé commitée est une clé compromise, même supprimée au commit suivant.

Le projet fil rouge contient un `.gitignore` complet à copier : [projet-fil-rouge/.gitignore](../projet-fil-rouge/.gitignore).

## 3. uv : Python et dépendances reproductibles

### Le problème

`pip install pandas` installe « la version du jour ». Six mois plus tard, un collègue installe une autre version et le code casse. Il faut distinguer **ce que vous demandez** (pandas ≥ 2.2) de **ce qui a été installé exactement** (pandas 2.3.1, numpy 2.2.6, …), et pouvoir réinstaller exactement la même chose.

![Le cycle uv](../assets/diagrams/uv-workflow.svg)

### Les quatre fichiers et dossiers

| Élément | Rôle | Dans Git ? |
|---|---|---|
| `pyproject.toml` | Déclare le projet et ses dépendances (ce que vous demandez) | oui |
| `uv.lock` | Fige toutes les versions résolues (ce qui est installé) | oui |
| `.python-version` | Version de Python du projet | oui |
| `.venv/` | L'environnement installé | non (régénéré par `uv sync`) |

### Les commandes

```bash
uv init mon-projet            # nouveau projet (pyproject.toml, .python-version, README)
cd mon-projet
uv add pandas scikit-learn    # ajoute une dépendance, met à jour uv.lock, installe
uv add --dev pytest ruff      # dépendance de développement (groupe dev)
uv add --group api fastapi    # dépendance dans un groupe nommé
uv remove pandas              # retire
uv sync                       # installe exactement uv.lock (crée .venv si besoin)
uv run python train.py        # exécute dans l'environnement, sans l'activer
uv run pytest                 # idem pour n'importe quel outil installé
uv lock --upgrade-package pandas   # met à jour une dépendance
uv python install 3.11        # installe un interpréteur Python
uvx ruff check .              # lance un outil sans l'installer dans le projet
```

`uv run` est la commande à retenir : elle garantit que la bonne version de Python et des bibliothèques est utilisée, sur votre machine comme en CI ou dans Docker.

### Dans le projet fil rouge

Le [pyproject.toml](../projet-fil-rouge/pyproject.toml) du fil rouge sépare les dépendances en groupes : le cœur (pandas, scikit-learn), `api` (FastAPI), `app` (Streamlit), `mlops` (MLflow, DVC) et `dev` (pytest, ruff). `uv sync` installe tout ; les images Docker de la séance 2 n'installeront que le groupe dont elles ont besoin.

### Pièges fréquents

- `ModuleNotFoundError` alors que la bibliothèque est « installée » : vous avez lancé `python` au lieu de `uv run python` (mauvais environnement).
- Un `uv.lock` en conflit lors d'un merge : lancez `uv lock` pour le régénérer, puis commitez.
- `uv sync` recrée `.venv` si vous changez de version de Python : normal, c'est rapide.

## 4. DVC : versionner les données et le pipeline

### Pourquoi pas Git ?

Git est fait pour du texte de quelques Ko. Un CSV de 500 Mo ou un modèle de 2 Go fait exploser le dépôt et ne se « diffe » pas. DVC garde dans Git un **pointeur** (un hash et une taille) et range le contenu dans un **remote** : un dossier partagé, un conteneur Azure Blob, un bucket GCS ou S3.

![Git contre DVC](../assets/diagrams/git-vs-dvc.svg)

### Versionner un fichier

```bash
uv run dvc init --subdir         # dans un sous-dossier d'un dépôt Git (sinon : dvc init)
uv run dvc add data/raw/gros_fichier.csv
#   -> crée gros_fichier.csv.dvc (le pointeur) et ajoute le fichier au .gitignore
git add data/raw/gros_fichier.csv.dvc data/raw/.gitignore
git commit -m "Ajoute les données brutes (DVC)"

uv run dvc remote add -d partage ../dvc-remote     # un dossier local pour commencer
uv run dvc push                                     # envoie le contenu vers le remote
uv run dvc pull                                     # (sur une autre machine) le récupère
```

Pour un remote Azure Blob (★★, séance 3) : `uv add "dvc[azure]"`, puis `dvc remote add -d azure azure://conteneur/dossier` et `dvc remote modify --local azure connection_string "..."` (l'option `--local` garde le secret hors de Git).

### Décrire le pipeline

Le vrai gain de DVC est le fichier `dvc.yaml` : il décrit les étapes, leurs entrées, leurs sorties et leurs paramètres. DVC sait alors **quoi relancer** quand quelque chose change.

![Le pipeline DVC du fil rouge](../assets/diagrams/dvc-dag.svg)

Extrait de [dvc.yaml](../projet-fil-rouge/dvc.yaml) :

```yaml
stages:
  train:
    cmd: python -m diabetes_ml.train
    deps:
      - data/processed/train.csv
      - src/diabetes_ml/train.py
    params:
      - train            # la section train de params.yaml
    outs:
      - models/model.joblib
```

Et les commandes du quotidien :

```bash
uv run dvc repro             # exécute ce qui doit l'être (et seulement ça)
uv run dvc dag               # affiche le graphe des étapes
uv run dvc metrics show      # les métriques déclarées (reports/metrics.json)
uv run dvc params diff       # quels paramètres ont changé depuis le dernier commit
uv run dvc metrics diff      # et quel effet sur les métriques
```

`dvc.lock` (généré) enregistre les hash de chaque entrée et sortie : c'est lui qui permet de savoir si une étape est à jour. Il se commite.

### DVC et les paramètres

`params.yaml` centralise ce que vous voulez faire varier : taille du jeu de test, type de modèle, profondeur des arbres. Changer une valeur puis `dvc repro` relance uniquement les étapes qui en dépendent. Pour explorer vite sans toucher au fichier : `uv run dvc exp run --set-param train.max_depth=8` puis `uv run dvc exp show`.

## 5. MLflow : tracer et comparer les expériences

### Le problème

Après dix entraînements, impossible de se souvenir lequel avait donné 0,79 d'AUC, avec quels paramètres, et où est le fichier du modèle. MLflow enregistre chaque exécution (**run**) dans une **expérience** : paramètres, métriques, artefacts, et le modèle lui-même.

![Le cycle MLflow](../assets/diagrams/mlflow-cycle.svg)

### Dans le code

Extrait de [train.py](../projet-fil-rouge/src/diabetes_ml/train.py) :

```python
import mlflow, mlflow.sklearn

mlflow.set_tracking_uri("sqlite:///mlflow.db")      # où stocker (fichier local ici)
mlflow.set_experiment("diabetes-risk")

with mlflow.start_run(run_name="random_forest") as run:
    mlflow.log_params({"n_estimators": 200, "max_depth": 6})
    pipe, metrics = fit(train_df, params)
    mlflow.log_metrics(metrics)                       # cv_accuracy, cv_roc_auc, …
    mlflow.sklearn.log_model(pipe, name="model", input_example=example)
    print(run.info.run_id)                            # identifiant unique du run
```

Avec `mlflow.sklearn.autolog()` avant l'entraînement, MLflow enregistre seul les hyperparamètres et les métriques de scikit-learn : pratique pour démarrer, moins lisible qu'un log explicite.

### L'interface

```bash
uv run mlflow ui --backend-store-uri sqlite:///mlflow.db
# http://localhost:5000
```

Dans l'interface : sélectionner plusieurs runs → **Compare** pour voir paramètres et métriques côte à côte, trier par `cv_roc_auc`, ouvrir un run pour télécharger le modèle.

### Le registre de modèles

Quand un run est bon, on l'enregistre sous un nom et une version : `diabetes-risk` version 3. C'est ce nom que l'API ou le serveur chargera, pas un chemin de fichier.

```bash
uv run python -c "import mlflow; mlflow.set_tracking_uri('sqlite:///mlflow.db'); print(mlflow.register_model('runs:/<RUN_ID>/model', 'diabetes-risk'))"
uv run mlflow models serve -m "models:/diabetes-risk/1" -p 5001 --no-conda   # serveur de prédiction clé en main
```

Le registre demande un backend base de données (`sqlite:///mlflow.db` suffit en local) ; un simple dossier `mlruns/` ne le supporte pas.

### DVC et MLflow : concurrents ou complémentaires ?

| | DVC | MLflow |
|---|---|---|
| Versionne | fichiers (données, modèles) et pipeline | exécutions (paramètres, métriques, artefacts) |
| Répond à | « comment régénérer ce modèle ? » | « quelle tentative était la meilleure ? » |
| Stockage | remote (Blob, GCS, dossier) | tracking (sqlite, serveur) + registre |
| Dans le fil rouge | `dvc repro` orchestre les étapes | chaque `train` crée un run |

Les deux se complètent : DVC rend l'exécution reproductible, MLflow la rend comparable. Beaucoup d'équipes utilisent l'un sans l'autre ; l'important est de couvrir les deux questions.

## 6. Récapitulatif

- Un projet reproductible a **trois fichiers de vérité** : `pyproject.toml` + `uv.lock` (code), `dvc.yaml` + `dvc.lock` (pipeline), et l'historique MLflow (expériences).
- `uv run` partout, `dvc repro` pour régénérer, `mlflow ui` pour comparer.
- Rien de lourd ni de secret dans Git : les données vont dans un remote DVC, les clés dans `.env`.

**Devoir pour la séance 2** : prendre votre propre notebook (ou garder le fil rouge) et le mettre au format du projet : `uv init`, le code d'entraînement dans `src/`, un `params.yaml`, un `dvc.yaml` avec au moins deux étapes, et un run MLflow. La séance 2 construira l'API et le site web par-dessus.

## Pour aller plus loin (★★)

- **Qualité automatique** : `uv add --dev ruff pre-commit`, puis un `.pre-commit-config.yaml` qui lance `ruff check --fix` et `ruff format` avant chaque commit.
- **Expériences DVC** : `dvc exp run --queue` pour planifier plusieurs variantes, `dvc exp show` pour les comparer, `dvc exp apply` pour garder la meilleure.
- **Remote DVC partagé** : un conteneur Azure Blob créé avec le crédit Azure for Students (séance 3, lab 9).
- **Serveur MLflow partagé** : `docker compose up mlflow` dans le fil rouge, puis `MLFLOW_TRACKING_URI=http://localhost:5000` ; toute l'équipe voit les mêmes runs.
- **Lecture** : documentation de [uv](https://docs.astral.sh/uv/), [DVC](https://dvc.org/doc), [MLflow](https://mlflow.org/docs/latest/).
