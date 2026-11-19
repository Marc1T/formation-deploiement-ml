"""Tests du cœur ML : données, entraînement, évaluation, prédiction."""

import numpy as np
import pytest

from diabetes_ml.data import FEATURES, TARGET, ZERO_MEANS_MISSING
from diabetes_ml.evaluate import evaluate
from diabetes_ml.predict import Predictor, risk_level

PATIENT = dict(
    pregnancies=2,
    glucose=138,
    blood_pressure=72,
    skin_thickness=35,
    insulin=120,
    bmi=33.6,
    diabetes_pedigree=0.62,
    age=45,
)


def test_split_is_stratified_and_sized(datasets):
    train_df, test_df = datasets
    assert len(train_df) + len(test_df) == 768
    assert abs(train_df[TARGET].mean() - test_df[TARGET].mean()) < 0.05


def test_zero_values_became_missing(datasets):
    train_df, _ = datasets
    for col in ZERO_MEANS_MISSING:
        assert (train_df[col] == 0).sum() == 0
    assert train_df["insulin"].isna().sum() > 0


def test_model_quality_on_test_set(model_dir, datasets):
    _, test_df = datasets
    predictor = Predictor(model_dir / "model.joblib")
    metrics, cm = evaluate(predictor.model, test_df, threshold=0.5)
    assert metrics["accuracy"] > 0.70
    assert metrics["roc_auc"] > 0.75
    assert cm["count"].sum() == len(test_df)


def test_predict_one_returns_contract(model_dir):
    predictor = Predictor(model_dir / "model.joblib")
    result = predictor.predict_one(PATIENT)
    assert set(result) == {"prediction", "probability", "risk_level", "model_version"}
    assert result["prediction"] in (0, 1)
    assert 0.0 <= result["probability"] <= 1.0
    assert result["model_version"] == "test"


def test_predict_handles_zero_as_missing(model_dir):
    predictor = Predictor(model_dir / "model.joblib")
    p_zero = predictor.predict_one({**PATIENT, "insulin": 0})["probability"]
    assert np.isfinite(p_zero)


def test_predict_one_rejects_missing_feature(model_dir):
    predictor = Predictor(model_dir / "model.joblib")
    with pytest.raises(ValueError, match="manquantes"):
        predictor.predict_one({"glucose": 120})


def test_missing_model_gives_clear_error(tmp_path):
    with pytest.raises(FileNotFoundError, match="dvc repro"):
        Predictor(tmp_path / "absent.joblib")


@pytest.mark.parametrize("proba,expected", [(0.1, "faible"), (0.45, "modéré"), (0.9, "élevé")])
def test_risk_level(proba, expected):
    assert risk_level(proba) == expected


def test_features_list_is_stable():
    assert FEATURES == [
        "pregnancies",
        "glucose",
        "blood_pressure",
        "skin_thickness",
        "insulin",
        "bmi",
        "diabetes_pedigree",
        "age",
    ]
