"""Cœur ML : construction, entraînement et sauvegarde du pipeline scikit-learn.

Ce module ne dépend ni de MLflow ni de DVC : l'API et l'application web peuvent
l'importer sans installer les outils d'expérimentation.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import cross_val_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from diabetes_ml.data import FEATURES, TARGET


def build_pipeline(train_params: dict[str, Any]) -> Pipeline:
    """Imputation + standardisation + classifieur : un seul objet à sauvegarder et à servir."""
    model_name = train_params["model"]
    if model_name == "random_forest":
        clf = RandomForestClassifier(
            n_estimators=train_params["n_estimators"],
            max_depth=train_params["max_depth"],
            random_state=42,
            n_jobs=-1,
        )
    elif model_name == "logistic_regression":
        clf = LogisticRegression(C=train_params["C"], max_iter=1000)
    else:
        raise ValueError(f"Modèle inconnu : {model_name}")

    return Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
            ("clf", clf),
        ]
    )


def fit(train_df: pd.DataFrame, train_params: dict[str, Any]) -> tuple[Pipeline, dict[str, float]]:
    """Entraîne le pipeline et renvoie (modèle, métriques de validation croisée)."""
    x, y = train_df[FEATURES], train_df[TARGET]
    pipe = build_pipeline(train_params)
    cv_acc = cross_val_score(pipe, x, y, cv=5, scoring="accuracy")
    cv_auc = cross_val_score(pipe, x, y, cv=5, scoring="roc_auc")
    pipe.fit(x, y)
    metrics = {
        "cv_accuracy": float(cv_acc.mean()),
        "cv_roc_auc": float(cv_auc.mean()),
        "train_accuracy": float(pipe.score(x, y)),
    }
    return pipe, metrics


def save(pipe: Pipeline, model_dir: Path, info: dict[str, Any]) -> None:
    """Écrit model.joblib et model_info.json (métadonnées lisibles par l'API)."""
    model_dir.mkdir(parents=True, exist_ok=True)
    joblib.dump(pipe, model_dir / "model.joblib")
    (model_dir / "model_info.json").write_text(
        json.dumps(info, indent=2, ensure_ascii=False), encoding="utf-8"
    )
