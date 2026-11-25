# Lab 3 · Tracer et comparer avec MLflow

**Durée** : 30 min · **Objectif** : enregistrer chaque entraînement comme un run MLflow, comparer trois variantes dans l'interface, enregistrer le meilleur modèle dans le registre et l'interroger.

**Terminal** : Git Bash sous Windows, Terminal sous macOS et Linux.

**Point de départ** : le projet `diabete-lab` du lab 2, commité, avec son pipeline DVC.

## ★ Parcours de base

### 1. Installer MLflow

```bash
uv add --group mlops mlflow
printf "mlflow.db\nmlruns/\nmlartifacts/\n" >> .gitignore
```

Le suivi MLflow local (`mlflow.db`) reste sur votre machine : il ne se commite pas.

### 2. Instrumenter `train.py`

Remplacez `src/diabete_lab/train.py` par cette version. Les lignes `mlflow.*` sont les seules nouveautés.

```python
import json
from pathlib import Path

import joblib
import mlflow
import mlflow.sklearn
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

    mlflow.set_tracking_uri("sqlite:///mlflow.db")      # où MLflow range ses données
    mlflow.set_experiment("diabete-lab")

    with mlflow.start_run(run_name=f"rf_depth_{params['max_depth']}") as run:
        mlflow.log_params(params)
        pipe = Pipeline([
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
            ("clf", RandomForestClassifier(
                n_estimators=params["n_estimators"], max_depth=params["max_depth"], random_state=42)),
        ])
        pipe.fit(train[FEATURES], train["outcome"])
        acc = pipe.score(test[FEATURES], test["outcome"])
        mlflow.log_metric("accuracy", acc)
        mlflow.sklearn.log_model(
            pipe,
            name="model",
            input_example=train[FEATURES].head(3),
            serialization_format=mlflow.sklearn.SERIALIZATION_FORMAT_CLOUDPICKLE,
        )

        Path("models").mkdir(exist_ok=True)
        Path("reports").mkdir(exist_ok=True)
        joblib.dump(pipe, "models/model.joblib")
        with open("reports/metrics.json", "w", encoding="utf-8") as f:
            json.dump({"accuracy": round(acc, 4)}, f)
        print(f"train : accuracy={acc:.3f} run={run.info.run_id[:8]}")


if __name__ == "__main__":
    main()
```

> **Pourquoi `serialization_format` ?** Les versions récentes de MLflow enregistrent les modèles scikit-learn au format *skops*, qui refuse par sécurité les arbres de décision des forêts aléatoires tant qu'on ne les déclare pas « de confiance ». Le format *cloudpickle*, historique, convient pour un modèle que vous avez entraîné vous-même. Sans cette option, l'entraînement plante sur `untrusted types`.

### 3. Produire trois runs

```bash
uv run dvc repro                                    # run 1 : max_depth 6
git add -A
git commit -m "Suivi MLflow"
uv run dvc exp run --set-param train.max_depth=3    # run 2
uv run dvc exp run --set-param train.max_depth=12   # run 3
```

> **Point de contrôle** : trois lignes `train : accuracy=… run=…`, avec `0.734` pour les profondeurs 6 et 3, et `0.740` pour la profondeur 12.

`dvc exp run` laisse les paramètres, les métriques et le modèle de la dernière expérience dans l'espace de travail. Pour revenir à la version commitée : `git checkout -- .` puis `uv run dvc checkout` (DVC remet le modèle correspondant depuis son cache).

### 4. Comparer dans l'interface

```bash
uv run mlflow ui --backend-store-uri sqlite:///mlflow.db
```

Ouvrez http://localhost:5000 :

1. Expérience `diabete-lab` : trois runs.
2. Cochez-les → **Compare** : tableau des paramètres et métriques, graphique en coordonnées parallèles.
3. Triez par `accuracy`. La profondeur 12 gagne avec 0,740 contre 0,734. Combien de patientes de différence sur les 154 du jeu de test ? Est-ce une vraie amélioration ?
4. Ouvrez le meilleur run → onglet **Artifacts** → `model/` : MLflow a stocké le modèle, son environnement (`requirements.txt`) et un exemple d'entrée.

Arrêtez l'interface avec `Ctrl+C`.

### 5. Enregistrer le modèle et l'interroger

Copiez l'identifiant du run de profondeur 12 (en haut de sa page, ou colonne *Run ID*), puis :

```bash
uv run python -c "import mlflow; mlflow.set_tracking_uri('sqlite:///mlflow.db'); print(mlflow.register_model('runs:/<RUN_ID>/model', 'diabete-risque'))"
```

> **Point de contrôle** : `Created version '1' of model 'diabete-risque'`, et l'onglet **Models** de l'interface affiche `diabete-risque` version 1.

Servez-le sans écrire une ligne d'API :

```bash
export MLFLOW_TRACKING_URI=sqlite:///mlflow.db
uv run mlflow models serve -m "models:/diabete-risque/1" -p 5001 --env-manager local
```

Dans un **second terminal**, dans le dossier du projet :

```bash
curl -X POST http://127.0.0.1:5001/invocations -H "Content-Type: application/json" \
  -d '{"dataframe_split": {"columns": ["pregnancies","glucose","blood_pressure","skin_thickness","insulin","bmi","diabetes_pedigree","age"], "data": [[2,138,72,35,120,33.6,0.62,45]]}}'
```

> **Point de contrôle** : la réponse est `{"predictions": [1]}`. Arrêtez le serveur avec `Ctrl+C`.

C'est un aperçu de la séance 2 : vous écrirez votre propre API, plus lisible, validée et documentée.

## ★★ Aller plus loin

- **Autolog** : remplacez les `log_*` par `mlflow.sklearn.autolog()` avant `fit`. Comparez ce qui est enregistré : beaucoup plus de choses, moins choisies.
- **Tags et artefacts** : `mlflow.set_tag("auteur", "vous")`, `mlflow.log_artifact("reports/metrics.json")`, `mlflow.log_figure(fig, "roc.png")` avec une courbe ROC matplotlib.
- **Validation croisée** : enregistrez aussi `cv_accuracy` et `cv_roc_auc` (voir `fit` dans [model.py](../../projet-fil-rouge/src/diabetes_ml/model.py) du fil rouge). Le classement des trois runs change-t-il ?
- **Serveur partagé** : lancez `docker compose up -d mlflow` dans le fil rouge, puis `export MLFLOW_TRACKING_URI=http://localhost:5000` et retirez `set_tracking_uri` du code. Les runs apparaissent sur le serveur, qu'une équipe pourrait partager.
- **Charger un modèle du registre dans du code** : `mlflow.sklearn.load_model("models:/diabete-risque/1")`.

## Dépannage

| Symptôme | Cause | Solution |
|---|---|---|
| `untrusted types found … sklearn.tree._tree.Tree` | format skops par défaut | ajouter `serialization_format=mlflow.sklearn.SERIALIZATION_FORMAT_CLOUDPICKLE` |
| Un run marqué *Failed* dans l'interface | un entraînement a planté après le début du run | normal ; le supprimer depuis l'interface si besoin |
| L'interface est vide | lancée sans `--backend-store-uri` | relancer avec `--backend-store-uri sqlite:///mlflow.db` |
| `register_model` échoue : `not supported` | suivi dans un dossier, pas une base | utiliser `sqlite:///mlflow.db` |
| `models serve` ne trouve pas le modèle | `MLFLOW_TRACKING_URI` non défini dans ce terminal | `export MLFLOW_TRACKING_URI=sqlite:///mlflow.db` |
| Port 5000 ou 5001 déjà utilisé | une autre instance tourne | ajouter `--port 5002` (ou `-p 5002`) |

## À retenir

- **Un run par entraînement** : paramètres, métriques et modèle sont enregistrés à chaque exécution, sans tableau Excel à tenir à la main.
- **L'interface compare les runs, mais c'est vous qui jugez** : un écart d'une patiente sur 154 n'est pas une amélioration.
- **Le registre donne un nom et une version au modèle retenu** : c'est ce nom qu'on déploie, pas un chemin de fichier.
- **DVC orchestre, MLflow trace** : ensemble, chaque expérience est à la fois reproductible et comparable.

## Solution

Solution complète : publiée après la séance.
