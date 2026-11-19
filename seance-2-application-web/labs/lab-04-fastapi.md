# Lab 4 · Servir le modèle avec FastAPI

**Durée** : 35 min · **Objectif** : exposer votre modèle derrière `POST /predict` et `GET /health`, avec validation des entrées, documentation automatique et tests.

Vous partez de votre projet des labs 1 à 3 (ou d'une copie du fil rouge). Référence : [projet-fil-rouge/api](../../projet-fil-rouge/api).

## ★ Parcours de base

### 1. Installer

```bash
uv add --group api fastapi "uvicorn[standard]" pydantic-settings
uv add --dev httpx            # pour TestClient
```

### 2. Une fonction de prédiction réutilisable

Dans `src/diabete_lab/predict.py`, isolez ce qui sera partagé par l'API et par l'interface :

```python
import joblib, pandas as pd

FEATURES = ["pregnancies", "glucose", "blood_pressure", "skin_thickness",
            "insulin", "bmi", "diabetes_pedigree", "age"]

class Predictor:
    def __init__(self, path: str):
        self.model = joblib.load(path)

    def predict_one(self, features: dict) -> dict:
        x = pd.DataFrame([{f: features[f] for f in FEATURES}])
        proba = float(self.model.predict_proba(x)[0, 1])
        return {"prediction": int(proba >= 0.5), "probability": round(proba, 4)}
```

### 3. Les schémas

`api/schemas.py` :

```python
from pydantic import BaseModel, Field

class PatientFeatures(BaseModel):
    pregnancies: int = Field(ge=0, le=20)
    glucose: float = Field(ge=0, le=300)
    blood_pressure: float = Field(ge=0, le=200)
    skin_thickness: float = Field(ge=0, le=100)
    insulin: float = Field(ge=0, le=900)
    bmi: float = Field(ge=0, le=80)
    diabetes_pedigree: float = Field(ge=0, le=3)
    age: int = Field(ge=1, le=120)

class PredictionOut(BaseModel):
    prediction: int
    probability: float
```

### 4. L'application

`api/main.py` :

```python
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from api.schemas import PatientFeatures, PredictionOut
from diabete_lab.predict import Predictor

state: dict = {"predictor": None}

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        state["predictor"] = Predictor(os.getenv("MODEL_PATH", "models/model.joblib"))
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
        raise HTTPException(503, "Modèle non chargé : lancez dvc repro")
    return state["predictor"].predict_one(patient.model_dump())
```

Créez un fichier vide `api/__init__.py`.

### 5. Lancer et explorer

```bash
uv run uvicorn api.main:app --reload
```

Ouvrez http://localhost:8000/docs : essayez `/predict` avec le bouton *Try it out*. Puis :

- envoyez un âge de `-3` : code `422`, et lisez le message d'erreur ;
- retirez un champ : `422` encore ;
- renommez `models/model.joblib`, redémarrez : `/health` dit `degraded`, `/predict` renvoie `503`.

En ligne de commande :

```bash
curl -X POST http://localhost:8000/predict -H "Content-Type: application/json" \
  -d '{"pregnancies":2,"glucose":138,"blood_pressure":72,"skin_thickness":35,"insulin":120,"bmi":33.6,"diabetes_pedigree":0.62,"age":45}'
```

(PowerShell : `Invoke-RestMethod -Method Post -Uri http://localhost:8000/predict -ContentType "application/json" -Body '{...}'`.)

### 6. Tester sans serveur

`tests/test_api.py` :

```python
from fastapi.testclient import TestClient
from api.main import app

PATIENT = {"pregnancies": 2, "glucose": 138, "blood_pressure": 72, "skin_thickness": 35,
           "insulin": 120, "bmi": 33.6, "diabetes_pedigree": 0.62, "age": 45}

def test_health():
    with TestClient(app) as client:
        assert client.get("/health").status_code == 200

def test_predict():
    with TestClient(app) as client:
        r = client.post("/predict", json=PATIENT)
        assert r.status_code == 200
        assert r.json()["prediction"] in (0, 1)

def test_validation():
    with TestClient(app) as client:
        assert client.post("/predict", json={**PATIENT, "age": -3}).status_code == 422
```

`uv run pytest` : trois tests verts (le modèle doit exister : `uv run dvc repro`). Ajoutez `pythonpath = ["src", "."]` dans `[tool.pytest.ini_options]` si les imports échouent.

## ★★ Aller plus loin

- **Route `/model`** qui renvoie les métadonnées du modèle (type, date, métriques) lues dans un `model_info.json` écrit par `train.py` (voir le fil rouge).
- **Seuil configurable** : `THRESHOLD` en variable d'environnement, lue avec `pydantic-settings` (`api/settings.py` du fil rouge).
- **Prédiction par lot** : `POST /predict/batch` qui accepte une liste de patients.
- **Exemple dans la documentation** : `model_config = ConfigDict(json_schema_extra={"examples": [...]})` sur `PatientFeatures`, pour que `/docs` propose un corps pré-rempli.
- **Journalisation** : un `logging.info` par prédiction avec la probabilité et la durée.

## Dépannage

| Symptôme | Cause | Solution |
|---|---|---|
| `ModuleNotFoundError: api` | lancé depuis un autre dossier | lancer `uvicorn` depuis la racine du projet |
| `/predict` renvoie 500 | le dictionnaire n'a pas les 8 clés attendues par le modèle | vérifier `FEATURES` et `model_dump()` |
| `TestClient` ne charge pas le modèle | `lifespan` ne s'exécute qu'avec `with TestClient(app)` | utiliser le gestionnaire de contexte |
| Port 8000 occupé | une ancienne instance tourne | `--port 8001` ou fermer l'ancien terminal |

## Ce qu'il faut retenir

Une API, c'est un contrat (schémas), un cycle de vie (charger une fois), et des codes de statut honnêtes. Solution complète : publiée après la séance.
