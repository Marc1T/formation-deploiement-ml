"""API de prédiction du risque de diabète.

Lancer en local :  uv run uvicorn api.main:app --reload
Documentation :    http://localhost:8000/docs
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

from api.schemas import HealthOut, ModelInfoOut, PatientFeatures, PredictionOut
from api.settings import Settings
from diabetes_ml.predict import Predictor

logger = logging.getLogger("api")
settings = Settings()
state: dict[str, Predictor | None] = {"predictor": None}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Charge le modèle une seule fois au démarrage, pas à chaque requête."""
    try:
        state["predictor"] = Predictor(settings.model_path, settings.threshold)
        logger.info("Modèle chargé : %s", settings.model_path)
    except FileNotFoundError as exc:
        logger.error("%s", exc)
        state["predictor"] = None
    yield
    state["predictor"] = None


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description=(
        "Projet fil rouge de la formation « Déployer un modèle ML et un site web ». "
        "Le modèle est un pipeline scikit-learn entraîné sur le jeu de données Pima. "
        "Usage pédagogique uniquement : ce n'est pas un outil médical."
    ),
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_predictor() -> Predictor:
    predictor = state["predictor"]
    if predictor is None:
        raise HTTPException(
            status_code=503,
            detail="Modèle non chargé. Entraînez-le (uv run dvc repro) puis redémarrez l'API.",
        )
    return predictor


@app.get("/", include_in_schema=False)
def root() -> RedirectResponse:
    return RedirectResponse(url="/docs")


@app.get("/health", response_model=HealthOut, tags=["Supervision"])
def health() -> HealthOut:
    """Sonde de santé : utilisée par Docker, Azure et Cloud Run pour savoir si l'API répond."""
    predictor = state["predictor"]
    return HealthOut(
        status="ok" if predictor else "degraded",
        model_loaded=predictor is not None,
        model_type=predictor.model_type if predictor else None,
        model_version=predictor.version if predictor else None,
    )


@app.get("/model", response_model=ModelInfoOut, tags=["Supervision"])
def model_info() -> ModelInfoOut:
    """Métadonnées du modèle servi (type, date, métriques, run MLflow)."""
    info = get_predictor().info
    return ModelInfoOut(**{k: v for k, v in info.items() if k in ModelInfoOut.model_fields})


@app.post("/predict", response_model=PredictionOut, tags=["Prédiction"])
def predict(patient: PatientFeatures) -> PredictionOut:
    """Prédit le risque de diabète pour un patient."""
    result = get_predictor().predict_one(patient.model_dump())
    return PredictionOut(**result)
