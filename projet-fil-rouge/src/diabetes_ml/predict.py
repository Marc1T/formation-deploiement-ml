"""Chargement du modèle et prédiction unitaire : partagé par l'API et l'application web."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import joblib
import pandas as pd

from diabetes_ml.data import FEATURES, clean


class Predictor:
    """Encapsule le pipeline scikit-learn et ses métadonnées."""

    def __init__(self, model_path: str | Path, threshold: float = 0.5):
        self.model_path = Path(model_path)
        if not self.model_path.exists():
            raise FileNotFoundError(
                f"Modèle introuvable : {self.model_path}. "
                "Lancez `uv run dvc repro` (ou `uv run diabetes-train`) pour l'entraîner."
            )
        self.model = joblib.load(self.model_path)
        self.threshold = threshold
        info_path = self.model_path.with_name("model_info.json")
        self.info: dict[str, Any] = (
            json.loads(info_path.read_text(encoding="utf-8")) if info_path.exists() else {}
        )

    @property
    def version(self) -> str:
        return self.info.get("version", "inconnue")

    @property
    def model_type(self) -> str:
        return self.info.get("model", type(self.model).__name__)

    def predict_one(self, features: dict[str, float]) -> dict[str, Any]:
        """Prédiction pour un patient. `features` doit contenir les 8 variables.

        Le même nettoyage qu'à l'entraînement est appliqué (0 = valeur manquante
        pour certaines mesures), puis le pipeline impute, standardise et prédit.
        """
        missing = [f for f in FEATURES if f not in features]
        if missing:
            raise ValueError(f"Variables manquantes : {missing}")
        x = clean(pd.DataFrame([{f: float(features[f]) for f in FEATURES}]))
        proba = float(self.model.predict_proba(x)[0, 1])
        return {
            "prediction": int(proba >= self.threshold),
            "probability": round(proba, 4),
            "risk_level": risk_level(proba),
            "model_version": self.version,
        }


def risk_level(proba: float) -> str:
    """Trois niveaux lisibles pour l'interface : faible, modéré, élevé."""
    if proba < 0.3:
        return "faible"
    if proba < 0.6:
        return "modéré"
    return "élevé"
