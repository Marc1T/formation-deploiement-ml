# Lab 1 · Transformer un notebook en projet uv

**Durée** : 25 min · **Objectif** : partir d'un script d'entraînement « à plat » et obtenir un projet que `uv sync` réinstalle à l'identique sur n'importe quelle machine.

Vous travaillez dans votre propre dossier, à côté du fil rouge. Le fil rouge sert de modèle : ouvrez [projet-fil-rouge/pyproject.toml](../../projet-fil-rouge/pyproject.toml) dans un onglet.

## ★ Parcours de base

### 1. Créer le projet

```bash
cd <votre dossier de travail>
uv init --package diabete-lab        # structure src/, pyproject.toml, README, .python-version
cd diabete-lab
uv python pin 3.11                   # fige la version de Python
tree /f  (Windows)   ou   ls -R      # regardez ce qui a été créé
```

Question : pourquoi `uv init --package` crée-t-il un dossier `src/diabete_lab/` plutôt que des fichiers à la racine ?

### 2. Déclarer les dépendances

```bash
uv add pandas scikit-learn joblib pyyaml
uv add --dev pytest ruff
```

Ouvrez `pyproject.toml` : les dépendances y sont écrites avec une borne basse (`pandas>=2.3`). Ouvrez `uv.lock` : chaque paquet y a une version exacte et un hash. Combien de paquets ont été installés alors que vous n'en avez demandé que quatre ?

### 3. Ajouter le code d'entraînement

Copiez les données : [projet-fil-rouge/data/raw/diabetes.csv](../../projet-fil-rouge/data/raw/diabetes.csv) dans `data/raw/`.

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

### 4. En faire une commande

Dans `pyproject.toml`, ajoutez :

```toml
[project.scripts]
diabete-train = "diabete_lab.train:main"
```

Puis `uv sync` et `uv run diabete-train`. Le script est maintenant une commande installée dans l'environnement.

### 5. Prouver la reproductibilité

```bash
cd ..
cp -r diabete-lab diabete-lab-copie      # (ou copier-coller le dossier)
cd diabete-lab-copie
rm -rf .venv                            # on supprime l'environnement
uv sync                                 # ... et on le recrée à l'identique
uv run diabete-train
```

Même résultat, même versions : c'est tout l'intérêt de `uv.lock`. Comparez le temps de ce second `uv sync` avec le premier : uv réutilise son cache.

### 6. Git

```bash
cd ../diabete-lab
git init -b main
printf ".venv/\n__pycache__/\nmodels/\n.env\n" > .gitignore
git add . && git commit -m "Projet uv : entraînement reproductible"
```

## ★★ Aller plus loin

- **Ruff** : `uv run ruff check .` puis `uv run ruff format .`. Ajoutez dans `pyproject.toml` une section `[tool.ruff]` avec `line-length = 100`.
- **Un test** : créez `tests/test_train.py` qui importe `FEATURES` et vérifie qu'il y a 8 variables ; `uv run pytest`.
- **Mettre à jour une dépendance** : `uv lock --upgrade-package scikit-learn` puis `git diff uv.lock` pour voir exactement ce qui a changé.
- **Outils hors projet** : `uvx cowsay -t "uv"`, `uv tool install ruff`. Quelle différence avec `uv add --dev` ?

## Dépannage

| Symptôme | Cause | Solution |
|---|---|---|
| `No module named diabete_lab` | lancé avec `python` au lieu de `uv run python` | toujours `uv run …` |
| `uv: command not found` | PATH non rechargé | rouvrir le terminal |
| `error: Failed to build` | `README.md` manquant alors que `pyproject.toml` le référence | créer le README ou retirer la ligne `readme = …` |
| Lenteur au premier `uv sync` | téléchargement de scikit-learn et scipy | normal une fois ; ensuite le cache sert |

## Ce qu'il faut retenir

`pyproject.toml` dit ce que vous voulez, `uv.lock` dit ce que vous avez, `uv sync` fait coïncider les deux, `uv run` exécute dedans. Solution complète : publiée après la séance.
