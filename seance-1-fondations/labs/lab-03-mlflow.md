# Lab 3 · Tracer et comparer avec MLflow

**Durée** : 30 min · **Objectif** : enregistrer chaque entraînement comme un run MLflow, comparer trois variantes dans l'interface, et enregistrer le meilleur modèle dans le registre.

## ★ Parcours de base

### 1. Installer MLflow

```bash
uv add --group mlops mlflow
```

### 2. Instrumenter `train.py`

Ajoutez autour de l'entraînement (adaptez les noms de variables) :

```python
import mlflow
import mlflow.sklearn

mlflow.set_tracking_uri("sqlite:///mlflow.db")
mlflow.set_experiment("diabete-lab")

with mlflow.start_run(run_name=f"rf_depth_{params['max_depth']}"):
    mlflow.log_params(params)                     # n_estimators, max_depth
    pipe.fit(x_train, y_train)
    acc = pipe.score(x_test, y_test)
    mlflow.log_metric("accuracy", acc)
    mlflow.sklearn.log_model(pipe, name="model", input_example=x_train.head(3))
```

Ajoutez `mlflow.db` et `mlruns/` au `.gitignore` : le suivi local ne se commite pas.

### 3. Produire trois runs

```bash
uv run dvc repro                                     # run 1 : paramètres actuels
uv run dvc exp run --set-param train.max_depth=3     # run 2
uv run dvc exp run --set-param train.max_depth=12    # run 3
```

(Sans DVC : modifiez `params.yaml` et relancez `uv run python -m diabete_lab.train` trois fois.)

### 4. Comparer dans l'interface

```bash
uv run mlflow ui --backend-store-uri sqlite:///mlflow.db
```

Ouvrez http://localhost:5000 :

1. Expérience `diabete-lab` : trois runs.
2. Cochez-les → **Compare** : tableau des paramètres et métriques, graphique parallèle.
3. Triez par `accuracy`. Lequel garderiez-vous ? Est-ce que la profondeur 12 est vraiment meilleure, ou juste mieux ajustée au jeu de test ?
4. Ouvrez le meilleur run → onglet **Artifacts** → `model/` : MLflow a stocké le modèle, son environnement (`requirements.txt`) et un exemple d'entrée.

### 5. Enregistrer le modèle dans le registre

Copiez l'identifiant du meilleur run (en haut de sa page), puis :

```bash
uv run python -c "import mlflow; mlflow.set_tracking_uri('sqlite:///mlflow.db'); print(mlflow.register_model('runs:/<RUN_ID>/model', 'diabete-risque'))"
```

Dans l'interface, onglet **Models** : `diabete-risque` version 1. Vous pouvez y ajouter une description et un alias (`champion`). Pour le servir sans écrire d'API :

```bash
uv run mlflow models serve -m "models:/diabete-risque/1" -p 5001 --no-conda
curl -X POST http://localhost:5001/invocations -H "Content-Type: application/json" \
  -d '{"dataframe_split": {"columns": ["pregnancies","glucose","blood_pressure","skin_thickness","insulin","bmi","diabetes_pedigree","age"], "data": [[2,138,72,35,120,33.6,0.62,45]]}}'
```

C'est un aperçu de la séance 2 : nous écrirons notre propre API, plus lisible et plus légère.

## ★★ Aller plus loin

- **Autolog** : remplacez les `log_*` par `mlflow.sklearn.autolog()` avant `fit`. Comparez ce qui est enregistré (beaucoup plus de choses, moins choisies).
- **Tags et artefacts** : `mlflow.set_tag("auteur", "vous")`, `mlflow.log_artifact("reports/metrics.json")`, `mlflow.log_figure(fig, "roc.png")` avec une courbe ROC matplotlib.
- **Serveur partagé** : lancez `docker compose up mlflow` dans le fil rouge, puis exportez `MLFLOW_TRACKING_URI=http://localhost:5000` avant `dvc repro`. Les runs apparaissent sur le serveur, qui pourrait être partagé par toute l'équipe.
- **Charger un modèle du registre dans du code** : `mlflow.sklearn.load_model("models:/diabete-risque/1")`.

## Dépannage

| Symptôme | Cause | Solution |
|---|---|---|
| L'interface est vide | lancée sans `--backend-store-uri` : elle lit `./mlruns` | relancer avec `--backend-store-uri sqlite:///mlflow.db` |
| `register_model` échoue : « not supported » | tracking dans un dossier, pas une base | utiliser `sqlite:///mlflow.db` |
| `log_model` avertit sur `artifact_path` | API MLflow 2 | avec MLflow 3, utiliser `name="model"` |
| Port 5000 déjà utilisé | un autre `mlflow ui` tourne | `--port 5002` |

## Ce qu'il faut retenir

Un run par entraînement, des paramètres et métriques explicites, l'interface pour comparer, le registre pour nommer le modèle qui part en production. Solution complète : publiée après la séance.
