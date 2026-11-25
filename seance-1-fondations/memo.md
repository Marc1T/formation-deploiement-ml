# Mémo · Séance 1 · Git, uv, DVC, MLflow

Toutes les commandes de la séance sur une page. Terminal : Git Bash sous Windows, Terminal sous macOS et Linux.

## Git

| Commande | Effet |
|---|---|
| `git status` | Ce qui a changé depuis le dernier commit |
| `git add .` ou `git add -A` | Prépare tous les changements (les fichiers du `.gitignore` sont ignorés) |
| `git commit -m "message"` | Enregistre un instantané |
| `git log --oneline` | Historique condensé |
| `git ls-files` | Fichiers suivis par Git |
| `git diff` / `git diff uv.lock` | Différences non commitées |
| `git checkout params.yaml` | Annule les changements non commités d'un fichier |
| `git rm --cached <fichier>` | Arrête de suivre un fichier sans le supprimer du disque |
| `git branch -M main` | Renomme la branche courante en `main` |
| `git remote add origin <url>` puis `git push -u origin main` | Publie sur GitHub |

## uv

| Commande | Effet |
|---|---|
| `uv init --package --python 3.11 <nom>` | Nouveau projet : `pyproject.toml`, `src/`, `.python-version`, dépôt Git |
| `uv add <paquet>` | Ajoute une dépendance, met à jour `uv.lock`, installe |
| `uv add --dev <paquet>` | Dépendance de développement (groupe `dev`) |
| `uv add --group <groupe> <paquet>` | Dépendance dans un groupe nommé (`mlops`, `api`, `app`) |
| `uv remove <paquet>` | Retire une dépendance |
| `uv sync` | Installe exactement `uv.lock` (crée `.venv` au besoin) |
| `uv run <commande>` | Exécute dans l'environnement du projet, sans l'activer |
| `uv lock --upgrade-package <paquet>` | Met à jour une seule dépendance |
| `uv tree --depth 1` | Dépendances directes et ce qu'elles entraînent |
| `uv python install 3.11` / `uv python pin 3.11` | Installe / fixe une version de Python |
| `uvx <outil>` | Lance un outil sans l'ajouter au projet |

Dans `pyproject.toml` :

```toml
[project.scripts]
diabete-train = "diabete_lab.train:main"   # uv run diabete-train

[tool.uv]
default-groups = "all"                     # uv sync installe tous les groupes
```

## DVC

| Commande | Effet |
|---|---|
| `uv run dvc init` | Initialise DVC dans un dépôt Git |
| `uv run dvc add <fichier>` | Suit un fichier : crée le pointeur `.dvc` et l'exclut de Git |
| `uv run dvc remote add -d <nom> <chemin ou url>` | Déclare le remote par défaut |
| `uv run dvc push` / `uv run dvc pull` | Envoie / récupère le contenu des fichiers suivis |
| `uv run dvc repro` | Exécute les étapes du pipeline qui doivent l'être |
| `uv run dvc dag` | Affiche le graphe des étapes |
| `uv run dvc status` | Étapes périmées et pourquoi |
| `uv run dvc metrics show` / `metrics diff` | Métriques, et leur évolution depuis le dernier commit |
| `uv run dvc params diff` | Paramètres modifiés depuis le dernier commit |
| `uv run dvc exp run --set-param train.max_depth=8` | Expérience sans toucher aux fichiers |
| `uv run dvc exp show` | Tableau des expériences (Windows : `export PYTHONUTF8=1` avant) |

Fichiers à commiter : `*.dvc`, `dvc.yaml`, `dvc.lock`, `params.yaml`, `.dvc/config`, les métriques en `cache: false`.

## MLflow

```python
mlflow.set_tracking_uri("sqlite:///mlflow.db")
mlflow.set_experiment("diabete-lab")
with mlflow.start_run(run_name="rf_depth_6") as run:
    mlflow.log_params(params)
    mlflow.log_metric("accuracy", acc)
    mlflow.sklearn.log_model(pipe, name="model", input_example=x.head(3),
                             serialization_format=mlflow.sklearn.SERIALIZATION_FORMAT_CLOUDPICKLE)
```

| Commande | Effet |
|---|---|
| `uv run mlflow ui --backend-store-uri sqlite:///mlflow.db` | Interface sur http://localhost:5000 |
| `mlflow.register_model("runs:/<RUN_ID>/model", "<nom>")` | Enregistre un run dans le registre |
| `uv run mlflow models serve -m "models:/<nom>/1" -p 5001 --env-manager local` | Sert le modèle en API (avec `MLFLOW_TRACKING_URI` défini) |
| `mlflow.sklearn.load_model("models:/<nom>/1")` | Charge un modèle du registre dans du code |

À ne jamais commiter : `.venv/`, `mlflow.db`, `mlruns/`, `models/`, `.env`.
