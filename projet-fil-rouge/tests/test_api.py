"""Tests de l'API FastAPI avec le client de test (aucun serveur à lancer)."""

import importlib
import os

import pytest
from fastapi.testclient import TestClient

PATIENT = {
    "pregnancies": 2,
    "glucose": 138,
    "blood_pressure": 72,
    "skin_thickness": 35,
    "insulin": 120,
    "bmi": 33.6,
    "diabetes_pedigree": 0.62,
    "age": 45,
}


def load_app(model_path: str):
    """Recharge api.main pour que Settings relise MODEL_PATH."""
    os.environ["MODEL_PATH"] = model_path
    import api.main as main

    return importlib.reload(main).app


@pytest.fixture(scope="module")
def client(model_dir):
    app = load_app(str(model_dir / "model.joblib"))
    with TestClient(app) as c:  # déclenche le lifespan (chargement du modèle)
        yield c


def test_health_reports_loaded_model(client):
    r = client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert body["model_loaded"] is True
    assert body["model_type"] == "logistic_regression"


def test_predict_returns_prediction(client):
    r = client.post("/predict", json=PATIENT)
    assert r.status_code == 200
    body = r.json()
    assert body["prediction"] in (0, 1)
    assert 0.0 <= body["probability"] <= 1.0
    assert body["risk_level"] in ("faible", "modéré", "élevé")


def test_predict_validates_input(client):
    assert client.post("/predict", json={**PATIENT, "age": -3}).status_code == 422
    assert client.post("/predict", json={"glucose": 120}).status_code == 422


def test_model_info_endpoint(client):
    r = client.get("/model")
    assert r.status_code == 200
    assert r.json()["model"] == "logistic_regression"


def test_openapi_docs_available(client):
    assert client.get("/docs").status_code == 200
    schema = client.get("/openapi.json").json()
    assert "/predict" in schema["paths"]


def test_missing_model_returns_503(model_dir):
    app = load_app(str(model_dir / "absent.joblib"))
    with TestClient(app) as c:
        assert c.get("/health").json()["status"] == "degraded"
        assert c.post("/predict", json=PATIENT).status_code == 503
    load_app(str(model_dir / "model.joblib"))
