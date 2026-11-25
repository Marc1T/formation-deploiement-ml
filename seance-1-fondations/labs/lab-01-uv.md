# Lab 1 · Transformer un notebook en projet uv

**Durée** : 25 min · **Objectif** : partir d'un script d'entraînement « à plat » et obtenir un projet que `uv sync` réinstalle à l'identique sur n'importe quelle machine.

**Terminal** : Git Bash sous Windows (installé avec Git ; dans VS Code, menu déroulant du terminal → *Git Bash*), Terminal sous macOS et Linux. Toutes les commandes des labs sont écrites pour ce shell.

**Point de départ** : uv et Git installés et configurés ([prérequis](../../00-prerequis/README.md)). Le projet fil rouge sert de modèle : gardez [projet-fil-rouge/pyproject.toml](../../projet-fil-rouge/pyproject.toml) ouvert dans un onglet.

## ★ Parcours de base

### 1. Créer le projet

```bash
cd <votre dossier de travail>
uv init --package --python 3.11 diabete-lab
cd diabete-lab
ls -a
cat pyproject.toml
```

`uv init` a créé : `pyproject.toml`, `.python-version`, `README.md`, `src/diabete_lab/__init__.py`, un `.gitignore`, et un dépôt Git. L'option `--python 3.11` fixe la version de Python du projet ; sans elle, uv prend la plus récente installée sur votre machine, qui n'est pas forcément celle de vos camarades ni celle des images Docker de la séance 2.

> **Point de contrôle** : `cat .python-version` affiche `3.11`, et `pyproject.toml` contient `requires-python = ">=3.11"`.

Question : pourquoi `uv init --package` range-t-il le code dans `src/diabete_lab/` plutôt qu'à la racine ?

### 2. Déclarer les dépendances

```bash
uv add pandas scikit-learn joblib pyyaml
uv add --dev pytest ruff
```

Ouvrez `pyproject.toml` : les dépendances y sont écrites avec une borne basse (`pandas>=…`). Ouvrez `uv.lock` : chaque paquet y a une version exacte et une empreinte (hash).

```bash
grep -c '^\[\[package\]\]' uv.lock     # nombre de paquets figés dans uv.lock
uv tree --depth 1                      # vos dépendances directes et ce qu'elles entraînent
```

Question : combien de paquets sont figés dans `uv.lock`, alors que vous n'en avez demandé que six ?

### 3. Récupérer les données et ajouter le code d'entraînement

```bash
mkdir -p data/raw
curl -L -o data/raw/diabetes.csv https://raw.githubusercontent.com/Marc1T/formation-deploiement-ml/main/projet-fil-rouge/data/raw/diabetes.csv
wc -l data/raw/diabetes.csv
```

> **Point de contrôle** : `wc -l` affiche `769` (une ligne d'en-tête et 768 patientes).

Créez `src/diabete_lab/train.py` :

```python
"""Entraînement minimal : à faire évoluer pendant la formation."""
from pathlib import Path

import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

FEATURES = ["pregnancies", "glucose", "blood_pressure", "skin_thickness",
            "insulin", "bmi", "diabetes_pedigree", "age"]


def main() -> None:
    df = pd.read_csv("data/raw/diabetes.csv")
    x_train, x_test, y_train, y_test = train_test_split(
        df[FEATURES], df["outcome"], test_size=0.2, random_state=42, stratify=df["outcome"]
    )
    pipe = Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", StandardScaler()),
        ("clf", RandomForestClassifier(n_estimators=200, max_depth=6, random_state=42)),
    ])
    pipe.fit(x_train, y_train)
    print(f"accuracy test : {pipe.score(x_test, y_test):.3f}")
    Path("models").mkdir(exist_ok=True)
    joblib.dump(pipe, "models/model.joblib")


if __name__ == "__main__":
    main()
```

Lancez-le **avec uv** :

```bash
uv run python -m diabete_lab.train
```

> **Point de contrôle** : `accuracy test : 0.740`, et un fichier `models/model.joblib` existe. Tout le monde doit obtenir exactement la même valeur : même code, mêmes données, mêmes versions, même graine aléatoire.

### 4. En faire une commande

`uv init --package` a déjà créé une section `[project.scripts]` dans `pyproject.toml`. **Ajoutez une ligne dans cette section** (n'en créez pas une seconde, le fichier deviendrait invalide) :

```toml
[project.scripts]
diabete-lab = "diabete_lab:main"
diabete-train = "diabete_lab.train:main"
```

```bash
uv sync
uv run diabete-train
```

Le script est maintenant une commande installée dans l'environnement du projet.

### 5. Prouver la reproductibilité

```bash
cd ..
cp -r diabete-lab diabete-lab-copie
cd diabete-lab-copie
rm -rf .venv                 # on supprime l'environnement…
uv sync                      # … et on le recrée à l'identique depuis uv.lock
uv run diabete-train
cd ../diabete-lab
```

> **Point de contrôle** : la copie affiche aussi `accuracy test : 0.740`. Le second `uv sync` prend quelques secondes : uv réutilise son cache.

### 6. Premier commit

`uv init` a déjà créé le dépôt Git et un `.gitignore` qui exclut `.venv` et `__pycache__`. On renomme la branche, on complète le `.gitignore`, on commite.

```bash
git status
git branch -M main
printf "\n# Formation\nmodels/\n.env\n" >> .gitignore
git add .
git commit -m "Projet uv : entraînement reproductible"
git ls-files
```

> **Point de contrôle** : `git ls-files` liste `pyproject.toml`, `uv.lock`, `.python-version`, `src/diabete_lab/train.py` et `data/raw/diabetes.csv`, mais ni `.venv/` ni `models/`.

Le CSV est commité dans Git pour l'instant. Au lab 2, vous le confierez à DVC : c'est exactement ce qui arrive dans les vrais projets quand les données grossissent.

## ★★ Aller plus loin

- **Ruff** : `uv run ruff check .` puis `uv run ruff format .`. Ajoutez dans `pyproject.toml` une section `[tool.ruff]` avec `line-length = 100`. Que change `ruff format` dans `train.py` ?
- **Un test** : créez `tests/test_train.py` qui importe `FEATURES` et vérifie qu'il y a 8 variables ; `uv run pytest`.
- **Mettre à jour une dépendance** : `uv lock --upgrade-package scikit-learn` puis `git diff uv.lock` pour voir exactement ce qui a changé.
- **Outils hors projet** : `uvx pycowsay "uv"`, `uv tool install ruff`. Quelle différence avec `uv add --dev` ?

## Dépannage

| Symptôme | Cause | Solution |
|---|---|---|
| `requested Python version 3.11 is incompatible with requires-python >=3.13` | projet créé sans `--python 3.11` | dans `pyproject.toml`, mettre `requires-python = ">=3.11"`, puis `uv python pin 3.11` |
| `TOML parse error … duplicate key` | une seconde section `[project.scripts]` | ne garder qu'une section, avec les deux lignes |
| `No module named diabete_lab` | lancé avec `python` au lieu de `uv run python` | toujours `uv run …` |
| `uv: command not found` | terminal ouvert avant l'installation | fermer et rouvrir le terminal |
| `Failed to build` : `Readme file does not exist` | `README.md` supprimé alors que `pyproject.toml` le référence | recréer le README ou retirer la ligne `readme = …` |
| `Please tell me who you are` au commit | identité Git non configurée | `git config --global user.name "…"` et `user.email "…"` |
| Lenteur du premier `uv add` | téléchargement de scikit-learn et scipy | normal une fois ; ensuite le cache sert |

## À retenir

- **`pyproject.toml` dit ce que vous demandez, `uv.lock` ce que vous obtenez** : toutes les versions, dépendances des dépendances comprises, figées et commitées.
- **`uv sync` recrée l'environnement à l'identique** sur n'importe quelle machine ; `.venv` ne se versionne jamais.
- **`uv run` exécute dans le bon environnement** sans rien activer : c'est la commande à taper par réflexe.
- **Le code vit dans `src/` et devient une commande** via `[project.scripts]` : il n'est plus prisonnier d'un notebook.

## Solution

Solution complète : publiée après la séance.
