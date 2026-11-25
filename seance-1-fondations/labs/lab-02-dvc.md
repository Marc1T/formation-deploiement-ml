# Lab 2 · Un pipeline reproductible avec DVC

**Durée** : 35 min · **Objectif** : confier les données à DVC, découper l'entraînement en étapes décrites dans `dvc.yaml` et paramétrées par `params.yaml`, et constater que `dvc repro` ne relance que ce qui a changé.

**Terminal** : Git Bash sous Windows, Terminal sous macOS et Linux.

**Point de départ** : le projet `diabete-lab` du lab 1, commité (`git status` n'affiche rien).

## ★ Parcours de base

### 1. Installer DVC dans un groupe d'outils

```bash
uv add --group mlops dvc
```

DVC n'est pas nécessaire pour faire tourner le modèle : c'est un outil de travail. On le range dans un **groupe** `mlops`, que les images Docker de la séance 2 pourront ignorer. Par défaut, uv n'installe que le groupe `dev` : sans réglage, le prochain `uv sync` désinstallerait DVC. Ajoutez à la fin de `pyproject.toml` :

```toml
[tool.uv]
default-groups = "all"
```

```bash
uv sync
uv run dvc --version
uv run dvc init
git add -A
git commit -m "Initialise DVC"
```

> **Point de contrôle** : `uv run dvc --version` affiche une version 3.x ; `dvc init` a créé `.dvc/` et `.dvcignore`, commités.

### 2. Confier les données à DVC

Depuis le lab 1, Git suit `data/raw/diabetes.csv`. Un fichier est suivi **soit** par Git, **soit** par DVC : on commence par le retirer de Git (le fichier reste sur le disque).

```bash
git rm --cached data/raw/diabetes.csv
uv run dvc add data/raw/diabetes.csv
cat data/raw/diabetes.csv.dvc          # le pointeur : empreinte md5, taille, chemin
cat data/raw/.gitignore                # DVC a exclu le vrai fichier de Git
git add -A
git commit -m "Données brutes suivies par DVC"
git ls-files data
```

> **Point de contrôle** : `git ls-files data` n'affiche plus que `data/raw/.gitignore` et `data/raw/diabetes.csv.dvc`. Le pointeur contient `md5: 521ac9eeeafc8acc452b05815e287e2c` : le même pour tout le monde, puisque c'est le même fichier.

Configurez un remote, ici un simple dossier à côté du projet, et envoyez-y les données :

```bash
uv run dvc remote add -d local ../dvc-remote
git add .dvc/config
git commit -m "Remote DVC local"
uv run dvc push
```

Simulez un collègue qui clone le projet sans les données :

```bash
rm data/raw/diabetes.csv
uv run dvc pull
```

> **Point de contrôle** : `dvc push` affiche `1 file pushed`, puis `dvc pull` affiche `1 file added` et le CSV est de retour.

### 3. Découper en deux étapes paramétrées

Créez `params.yaml` à la racine : tout ce qu'on veut faire varier est ici, plus dans le code.

```yaml
data:
  test_size: 0.2
  random_state: 42
train:
  n_estimators: 200
  max_depth: 6
```

Créez `src/diabete_lab/prepare.py`. Dans ce jeu de données, un 0 dans la glycémie, la pression, le pli cutané, l'insuline ou l'IMC signifie « mesure manquante » : on le remplace par une vraie valeur manquante, que le pipeline imputera.

```python
from pathlib import Path

import numpy as np
import pandas as pd
import yaml
from sklearn.model_selection import train_test_split

ZERO_MEANS_MISSING = ["glucose", "blood_pressure", "skin_thickness", "insulin", "bmi"]


def main() -> None:
    with open("params.yaml", encoding="utf-8") as f:
        params = yaml.safe_load(f)["data"]
    df = pd.read_csv("data/raw/diabetes.csv")
    for col in ZERO_MEANS_MISSING:
        df[col] = df[col].replace(0, np.nan)
    train, test = train_test_split(
        df, test_size=params["test_size"], random_state=params["random_state"], stratify=df["outcome"]
    )
    Path("data/processed").mkdir(parents=True, exist_ok=True)
    train.to_csv("data/processed/train.csv", index=False)
    test.to_csv("data/processed/test.csv", index=False)
    print(f"prepare : {len(train)} train / {len(test)} test")


if __name__ == "__main__":
    main()
```

Réécrivez `src/diabete_lab/train.py` pour qu'il lise `params.yaml` et les fichiers préparés, et qu'il écrive l'accuracy dans `reports/metrics.json`. Essayez d'abord seul, à partir de la version du lab 1 ; le code complet est ci-dessous si vous bloquez.

<details>
<summary>Code complet de <code>train.py</code></summary>

```python
import json
from pathlib import Path

import joblib
import pandas as pd
import yaml
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

FEATURES = ["pregnancies", "glucose", "blood_pressure", "skin_thickness",
            "insulin", "bmi", "diabetes_pedigree", "age"]


def main() -> None:
    with open("params.yaml", encoding="utf-8") as f:
        params = yaml.safe_load(f)["train"]
    train = pd.read_csv("data/processed/train.csv")
    test = pd.read_csv("data/processed/test.csv")

    pipe = Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", StandardScaler()),
        ("clf", RandomForestClassifier(
            n_estimators=params["n_estimators"], max_depth=params["max_depth"], random_state=42)),
    ])
    pipe.fit(train[FEATURES], train["outcome"])
    acc = pipe.score(test[FEATURES], test["outcome"])

    Path("models").mkdir(exist_ok=True)
    Path("reports").mkdir(exist_ok=True)
    joblib.dump(pipe, "models/model.joblib")
    with open("reports/metrics.json", "w", encoding="utf-8") as f:
        json.dump({"accuracy": round(acc, 4)}, f)
    print(f"train : accuracy={acc:.3f}")


if __name__ == "__main__":
    main()
```

</details>

### 4. Décrire le pipeline

Créez `dvc.yaml` à la racine :

```yaml
stages:
  prepare:
    cmd: python -m diabete_lab.prepare
    deps: [data/raw/diabetes.csv, src/diabete_lab/prepare.py]
    params: [data]
    outs: [data/processed/train.csv, data/processed/test.csv]
  train:
    cmd: python -m diabete_lab.train
    deps: [data/processed/train.csv, data/processed/test.csv, src/diabete_lab/train.py]
    params: [train]
    outs: [models/model.joblib]
    metrics:
      - reports/metrics.json:
          cache: false
```

```bash
uv run dvc repro            # exécute prepare puis train
uv run dvc dag              # le graphe des étapes
uv run dvc metrics show     # l'accuracy
git status
git add -A
git commit -m "Pipeline DVC : prepare + train"
```

> **Point de contrôle** : `dvc repro` affiche `prepare : 614 train / 154 test` puis `train : accuracy=0.734` ; `dvc metrics show` affiche `0.7338`. Après le commit, `git status` est vide : `dvc.yaml`, `dvc.lock`, `params.yaml`, `reports/metrics.json`, le code et `data/processed/.gitignore` sont commités.

### 5. Constater la mise en cache

```bash
uv run dvc repro            # rien ne se relance : tout est à jour
```

Dans `params.yaml`, passez `max_depth: 6` à `max_depth: 10`, puis :

```bash
uv run dvc repro            # seule l'étape train se relance
uv run dvc params diff      # ce qui a changé
uv run dvc metrics diff     # l'effet sur la métrique
```

> **Point de contrôle** : `Stage 'prepare' didn't change, skipping` puis `Running stage 'train'` ; `dvc metrics diff` affiche l'accuracy passée de `0.7338` à `0.7468`.

Changez maintenant `test_size: 0.2` en `test_size: 0.25` et lancez `uv run dvc status` **sans** relancer. Quelles étapes DVC juge-t-il périmées, et pourquoi ?

Revenez ensuite à la version commitée :

```bash
git checkout params.yaml
uv run dvc repro            # DVC retrouve les sorties dans son cache, sans réentraîner
```

## ★★ Aller plus loin

- **Expériences sans toucher aux fichiers** : `uv run dvc exp run --set-param train.max_depth=3`, puis `=12`, puis `uv run dvc exp show`. Sous Windows, si `exp show` plante sur une erreur `charmap`, lancez d'abord `export PYTHONUTF8=1`. Gardez la meilleure avec `uv run dvc exp apply <nom>`.
- **Une troisième étape** `evaluate` qui produit aussi une matrice de confusion en CSV, déclarée comme `plots` (voir [dvc.yaml](../../projet-fil-rouge/dvc.yaml) du fil rouge), puis `uv run dvc plots show`.
- **Remote cloud** : `uv add --group mlops "dvc[azure]"` ; en séance 3, vous pointerez ce remote vers un conteneur Azure Blob.
- **Pourquoi `cache: false` sur les métriques ?** Cherchez dans la documentation et expliquez-le en une phrase.

## Dépannage

| Symptôme | Cause | Solution |
|---|---|---|
| `output 'data/raw/diabetes.csv' is already tracked by SCM` | le fichier est encore suivi par Git | `git rm --cached data/raw/diabetes.csv`, puis `dvc add` |
| `dvc: command not found` après un `uv sync` | groupe `mlops` désinstallé faute de `default-groups = "all"` | ajouter la section `[tool.uv]` puis `uv sync` |
| `dvc init` : `not a git repository` | dépôt Git absent | `git init -b main` d'abord |
| `dvc repro` ne relance rien après une modification | la dépendance modifiée n'est pas listée dans `deps` | l'ajouter : DVC ne surveille que ce qui est déclaré |
| `'charmap' codec can't encode characters` | console Windows en encodage ancien | `export PYTHONUTF8=1` puis relancer |
| Sorties signalées comme modifiées | une sortie a été changée à la main | `uv run dvc repro -f` pour forcer, ou `uv run dvc checkout` |

## À retenir

- **Git versionne le code et un petit pointeur, DVC le contenu lourd** : le remote stocke les données, `dvc push` et `dvc pull` les partagent.
- **Un fichier est suivi par Git ou par DVC, jamais les deux** : `git rm --cached` avant `dvc add`.
- **`dvc.yaml` décrit le pipeline, `dvc.lock` enregistre son état** : les deux se commitent, avec `params.yaml`.
- **`dvc repro` ne relance que ce qui a changé** ; `params diff` et `metrics diff` mesurent l'effet d'un changement.

## Solution

Solution complète : publiée après la séance.
