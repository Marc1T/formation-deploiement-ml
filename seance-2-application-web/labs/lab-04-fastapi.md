# Lab 4 · Servir le modèle avec FastAPI

**Durée** : 35 min · **Objectif** : exposer votre modèle derrière `POST /predict` et `GET /health`, avec validation des entrées, documentation automatique et tests.

**Terminal** : Git Bash sous Windows, Terminal sous macOS et Linux.

**Point de départ** : le projet `diabete-lab` des labs 1 à 3. Les expériences DVC du lab 3 ont laissé des fichiers modifiés (paramètres, métriques, modèle de profondeur 12). Remettez le projet dans son état commité, avec le modèle de profondeur 6 :

```bash
cd diabete-lab
git checkout -- .        # annule les modifications laissées par dvc exp run
uv run dvc checkout      # remet le modèle et les données préparées qui correspondent au commit
git status               # doit être vide
```

Référence complète : [projet-fil-rouge/api](../../projet-fil-rouge/api).

## ★ Parcours de base

### 1. Installer

```bash
uv add --group api fastapi "uvicorn[standard]"
uv add --dev httpx            # utilisé par le client de test de FastAPI
```

### 2. Une fonction de prédiction réutilisable

L'API (ce lab) et l'interface web (lab 5) feront la même chose : charger le modèle, appliquer **le même nettoyage qu'à l'entraînement**, prédire. On l'écrit une seule fois. Créez `src/diabete_lab/predict.py` :

```python
"""Chargement du modèle et prédiction unitaire : partagés par l'API et l'interface web."""
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from diabete_lab.prepare import ZERO_MEANS_MISSING


class Predictor:
    def __init__(self, path: str | Path, threshold: float = 0.5):
        self.model = joblib.load(path)                          # FileNotFoundError si absent
        self.features = list(self.model.feature_names_in_)      # le modèle connaît ses colonnes
        self.threshold = threshold

    def predict_one(self, values: dict) -> dict:
        x = pd.DataFrame([{f: values[f] for f in self.features}]).astype(float)
        x[ZERO_MEANS_MISSING] = x[ZERO_MEANS_MISSING].replace(0, np.nan)   # comme prepare.py
        proba = float(self.model.predict_proba(x)[0, 1])
        return {"prediction": int(proba >= self.threshold), "probability": round(proba, 4)}
```

Deux choix méritent l'attention :

- `feature_names_in_` : un pipeline scikit-learn entraîné sur un DataFrame retient le nom et l'ordre de ses colonnes. On n'a pas à recopier la liste, ni à importer `train.py` (qui importe MLflow, inutile en production).
- Le remplacement des 0 : c'est exactement ce que fait `prepare.py` avant l'entraînement. Un modèle doit voir en production des données préparées **comme à l'entraînement**.

Vérifiez :

```bash
uv run python -c "
from diabete_lab.predict import Predictor
p = Predictor('models/model.joblib')
patient = dict(pregnancies=2, glucose=138, blood_pressure=72, skin_thickness=35, insulin=120, bmi=33.6, diabetes_pedigree=0.62, age=45)
print(p.predict_one(patient))
print(p.predict_one({**patient, 'insulin': 0}))"
```

> **Point de contrôle** : `{'prediction': 1, 'probability': 0.5838}`, puis `0.6142` pour une insuline inconnue.

Question : commentez temporairement la ligne du `replace` et relancez. Que devient la probabilité avec `insulin: 0` ? Pourquoi est-ce dangereux en production ?

### 3. Le contrat d'entrée et de sortie

Créez le dossier `api/`, un fichier vide `api/__init__.py`, et `api/schemas.py` :

```python
from pydantic import BaseModel, Field


class PatientFeatures(BaseModel):
    pregnancies: int = Field(ge=0, le=20, description="Nombre de grossesses")
    glucose: float = Field(ge=0, le=300, description="Glycémie à 2 h (mg/dL), 0 = inconnue")
    blood_pressure: float = Field(ge=0, le=200, description="Pression diastolique (mm Hg)")
    skin_thickness: float = Field(ge=0, le=100, description="Pli cutané (mm)")
    insulin: float = Field(ge=0, le=900, description="Insuline à 2 h (µU/mL)")
    bmi: float = Field(ge=0, le=80, description="Indice de masse corporelle")
    diabetes_pedigree: float = Field(ge=0, le=3, description="Antécédents familiaux")
    age: int = Field(ge=1, le=120, description="Âge en années")


class PredictionOut(BaseModel):
    prediction: int
    probability: float
```

```bash
mkdir -p api && touch api/__init__.py
```

### 4. L'application

`api/main.py` :

```python
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException

from api.schemas import PatientFeatures, PredictionOut
from diabete_lab.predict import Predictor

MODEL_PATH = os.getenv("MODEL_PATH", "models/model.joblib")
state: dict = {"predictor": None}


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        state["predictor"] = Predictor(MODEL_PATH)   # chargé une seule fois, au démarrage
    except FileNotFoundError:
        state["predictor"] = None
    yield


app = FastAPI(title="API diabète", lifespan=lifespan)


@app.get("/health")
def health():
    return {"status": "ok" if state["predictor"] else "degraded"}


@app.post("/predict", response_model=PredictionOut)
def predict(patient: PatientFeatures):
    if state["predictor"] is None:
        raise HTTPException(status_code=503, detail="Modèle non chargé : lancez uv run dvc repro")
    return state["predictor"].predict_one(patient.model_dump())
```

### 5. Lancer et explorer

```bash
uv run uvicorn api.main:app --reload
```

Ouvrez http://localhost:8000/docs et essayez `/predict` avec *Try it out*. Puis, dans un **second terminal** :

```bash
curl http://localhost:8000/health
curl -X POST http://localhost:8000/predict -H "Content-Type: application/json" \
  -d '{"pregnancies":2,"glucose":138,"blood_pressure":72,"skin_thickness":35,"insulin":120,"bmi":33.6,"diabetes_pedigree":0.62,"age":45}'
curl -X POST http://localhost:8000/predict -H "Content-Type: application/json" \
  -d '{"pregnancies":2,"glucose":138,"blood_pressure":72,"skin_thickness":35,"insulin":120,"bmi":33.6,"diabetes_pedigree":0.62,"age":-3}'
```

> **Point de contrôle** : `{"status":"ok"}`, puis `{"prediction":1,"probability":0.5838}`, puis une erreur `422` qui désigne le champ `age`.

Arrêtez le serveur (`Ctrl+C`) et relancez-le avec un modèle introuvable :

```bash
MODEL_PATH=absent.joblib uv run uvicorn api.main:app
```

> **Point de contrôle** : `/health` répond `{"status":"degraded"}` et `/predict` répond `503` avec un message qui dit quoi faire.

### 6. Tester sans lancer de serveur

Pour que pytest trouve le dossier `api/`, ajoutez à `pyproject.toml` :

```toml
[tool.pytest.ini_options]
pythonpath = ["."]
```

`tests/test_api.py` :

```python
from fastapi.testclient import TestClient

from api.main import app

PATIENT = {"pregnancies": 2, "glucose": 138, "blood_pressure": 72, "skin_thickness": 35,
           "insulin": 120, "bmi": 33.6, "diabetes_pedigree": 0.62, "age": 45}


def test_health():
    with TestClient(app) as client:          # le "with" déclenche le lifespan
        assert client.get("/health").json() == {"status": "ok"}


def test_predict():
    with TestClient(app) as client:
        r = client.post("/predict", json=PATIENT)
        assert r.status_code == 200
        assert r.json()["prediction"] in (0, 1)
        assert 0 <= r.json()["probability"] <= 1


def test_validation():
    with TestClient(app) as client:
        assert client.post("/predict", json={**PATIENT, "age": -3}).status_code == 422
        assert client.post("/predict", json={"glucose": 120}).status_code == 422
```

```bash
uv run pytest
git add -A
git commit -m "API FastAPI : /health, /predict, tests"
```

> **Point de contrôle** : `3 passed`, puis `git status` vide.

## ★★ Aller plus loin

- **Route `/model`** qui renvoie les colonnes attendues et le seuil : `{"features": p.features, "threshold": p.threshold}`.
- **Seuil configurable** : lisez `THRESHOLD` dans l'environnement (`float(os.getenv("THRESHOLD", "0.5"))`) et vérifiez qu'avec `THRESHOLD=0.6` le patient d'exemple passe à `prediction: 0`. Version propre : `pydantic-settings` (voir [settings.py](../../projet-fil-rouge/api/settings.py) du fil rouge).
- **Prédiction par lot** : `POST /predict/batch` qui accepte une liste de patients.
- **Exemple dans la documentation** : `model_config = ConfigDict(json_schema_extra={"examples": [PATIENT]})` dans `PatientFeatures`, pour que `/docs` propose un corps pré-rempli.
- **Test du 503** : un test qui crée l'application avec `MODEL_PATH` vers un fichier absent (voir `test_missing_model_returns_503` dans le fil rouge).

## Dépannage

| Symptôme | Cause | Solution |
|---|---|---|
| `ModuleNotFoundError: No module named 'api'` (uvicorn) | lancé depuis un autre dossier | lancer depuis la racine du projet |
| `ModuleNotFoundError: No module named 'api'` (pytest) | `pythonpath` absent | ajouter `[tool.pytest.ini_options] pythonpath = ["."]` |
| Les tests renvoient 503 | modèle absent | `uv run dvc repro` avant `pytest` |
| `/health` est `ok` mais les tests échouent sur le lifespan | `TestClient(app)` utilisé sans `with` | toujours `with TestClient(app) as client:` |
| `AttributeError: … feature_names_in_` | modèle entraîné sur un tableau numpy, pas un DataFrame | réentraîner avec `train.py` (qui passe un DataFrame) |
| Port 8000 occupé | une ancienne instance tourne | `--port 8001`, ou fermer l'ancien terminal |

## À retenir

- **Une API est un contrat** : Pydantic valide l'entrée et documente la sortie ; une requête invalide reçoit un `422` sans toucher au modèle.
- **Le modèle se charge une fois, au démarrage** (`lifespan`), pas à chaque requête.
- **Même préparation qu'à l'entraînement** : sinon le modèle se trompe en silence (0,61 devient 0,35 pour une insuline inconnue).
- **Des codes de statut honnêtes** : `/health` pour la supervision, `503` quand le service n'est pas prêt, et des tests qui le prouvent.

## Solution

Solution complète : publiée après la séance.
