"""Lecture des paramètres (params.yaml) et chemins du projet."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml


def project_root() -> Path:
    """Racine du projet : dossier contenant pyproject.toml (ou le répertoire courant)."""
    here = Path.cwd().resolve()
    for candidate in (here, *here.parents):
        if (candidate / "pyproject.toml").exists():
            return candidate
    return here


def load_params(path: str | os.PathLike[str] = "params.yaml") -> dict[str, Any]:
    """Charge params.yaml. Le chemin est relatif à la racine du projet."""
    p = Path(path)
    if not p.is_absolute():
        p = project_root() / p
    with p.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


def tracking_uri(params: dict[str, Any]) -> str:
    """URI MLflow : la variable d'environnement MLFLOW_TRACKING_URI l'emporte sur params.yaml."""
    return os.environ.get("MLFLOW_TRACKING_URI") or params["mlflow"]["tracking_uri"]
