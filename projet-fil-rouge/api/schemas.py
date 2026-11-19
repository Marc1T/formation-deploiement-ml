"""Schémas Pydantic : contrat d'entrée / sortie de l'API, validés et documentés."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class PatientFeatures(BaseModel):
    """Les 8 mesures du jeu de données Pima. Les bornes évitent les valeurs absurdes."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "pregnancies": 2,
                    "glucose": 138,
                    "blood_pressure": 72,
                    "skin_thickness": 35,
                    "insulin": 120,
                    "bmi": 33.6,
                    "diabetes_pedigree": 0.62,
                    "age": 45,
                }
            ]
        }
    )

    pregnancies: int = Field(ge=0, le=20, description="Nombre de grossesses")
    glucose: float = Field(ge=0, le=300, description="Glycémie à 2 h (mg/dL), 0 = inconnue")
    blood_pressure: float = Field(
        ge=0, le=200, description="Pression diastolique (mm Hg), 0 = inconnue"
    )
    skin_thickness: float = Field(
        ge=0, le=100, description="Pli cutané tricipital (mm), 0 = inconnu"
    )
    insulin: float = Field(ge=0, le=900, description="Insuline sérique à 2 h (µU/mL), 0 = inconnue")
    bmi: float = Field(ge=0, le=80, description="Indice de masse corporelle, 0 = inconnu")
    diabetes_pedigree: float = Field(ge=0, le=3, description="Score d'antécédents familiaux")
    age: int = Field(ge=1, le=120, description="Âge en années")


class PredictionOut(BaseModel):
    prediction: int = Field(description="1 = risque de diabète, 0 = pas de risque détecté")
    probability: float = Field(description="Probabilité estimée de la classe 1")
    risk_level: str = Field(description="faible, modéré ou élevé")
    model_version: str


class HealthOut(BaseModel):
    status: str
    model_loaded: bool
    model_type: str | None = None
    model_version: str | None = None


class ModelInfoOut(BaseModel):
    model: str | None = None
    version: str | None = None
    trained_at: str | None = None
    features: list[str] = []
    metrics: dict[str, float] = {}
    mlflow_run_id: str | None = None
