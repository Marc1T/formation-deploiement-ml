"""Étape `evaluate` : métriques sur le jeu de test, rapport pour DVC et MLflow."""

from __future__ import annotations

import json
from pathlib import Path

import joblib
import mlflow
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)

from diabetes_ml.config import load_params, project_root, tracking_uri
from diabetes_ml.data import FEATURES, TARGET


def evaluate(
    model, test_df: pd.DataFrame, threshold: float
) -> tuple[dict[str, float], pd.DataFrame]:
    x, y = test_df[FEATURES], test_df[TARGET]
    proba = model.predict_proba(x)[:, 1]
    pred = (proba >= threshold).astype(int)
    metrics = {
        "accuracy": float(accuracy_score(y, pred)),
        "precision": float(precision_score(y, pred, zero_division=0)),
        "recall": float(recall_score(y, pred, zero_division=0)),
        "f1": float(f1_score(y, pred, zero_division=0)),
        "roc_auc": float(roc_auc_score(y, proba)),
        "threshold": float(threshold),
        "n_test": int(len(test_df)),
    }
    cm = confusion_matrix(y, pred)
    rows = [
        {"actual": int(a), "predicted": int(p), "count": int(cm[a][p])}
        for a in range(cm.shape[0])
        for p in range(cm.shape[1])
    ]
    return metrics, pd.DataFrame(rows)


def main() -> None:
    params = load_params()
    root = project_root()
    model_dir = root / params["train"]["model_dir"]
    reports_dir: Path = root / params["evaluate"]["reports_dir"]
    reports_dir.mkdir(parents=True, exist_ok=True)

    model = joblib.load(model_dir / "model.joblib")
    info = json.loads((model_dir / "model_info.json").read_text(encoding="utf-8"))
    test_df = pd.read_csv(root / params["data"]["processed_dir"] / "test.csv")

    metrics, cm = evaluate(model, test_df, params["evaluate"]["threshold"])
    (reports_dir / "metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    cm.to_csv(reports_dir / "confusion_matrix.csv", index=False)

    # Rattache les métriques de test au run MLflow de l'entraînement.
    mlflow.set_tracking_uri(tracking_uri(params))
    run_id = info.get("mlflow_run_id")
    if run_id:
        with mlflow.start_run(run_id=run_id):
            mlflow.log_metrics({f"test_{k}": v for k, v in metrics.items() if k != "n_test"})
            mlflow.log_artifact(str(reports_dir / "metrics.json"))

    print(
        f"evaluate : accuracy={metrics['accuracy']:.3f} recall={metrics['recall']:.3f} "
        f"roc_auc={metrics['roc_auc']:.3f} -> {reports_dir / 'metrics.json'}"
    )


if __name__ == "__main__":
    main()
