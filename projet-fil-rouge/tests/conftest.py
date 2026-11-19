"""Fixtures partagées : données nettoyées et un modèle rapide dans un dossier temporaire."""

from __future__ import annotations

from pathlib import Path

import pytest

from diabetes_ml.data import clean, load_raw, split
from diabetes_ml.model import fit, save

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="session")
def datasets():
    df = clean(load_raw(ROOT / "data" / "raw" / "diabetes.csv"))
    return split(df, test_size=0.2, random_state=42)


@pytest.fixture(scope="session")
def model_dir(tmp_path_factory, datasets) -> Path:
    """Régression logistique : rapide, suffisante pour tester la chaîne complète."""
    train_df, _ = datasets
    pipe, metrics = fit(train_df, {"model": "logistic_regression", "C": 1.0})
    out = tmp_path_factory.mktemp("models")
    save(pipe, out, {"model": "logistic_regression", "version": "test", "metrics": metrics})
    return out
