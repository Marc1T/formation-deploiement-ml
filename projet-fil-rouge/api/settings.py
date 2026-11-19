"""Configuration de l'API : variables d'environnement (ou fichier .env)."""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Chaque champ peut être surchargé par une variable d'environnement du même nom.

    Exemple : MODEL_PATH=/app/models/model.joblib THRESHOLD=0.4
    """

    model_config = SettingsConfigDict(env_file=".env", extra="ignore", protected_namespaces=())

    app_name: str = "API Risque de diabète"
    app_version: str = "0.1.0"
    model_path: str = "models/model.joblib"
    threshold: float = 0.5
    cors_origins: list[str] = ["*"]
