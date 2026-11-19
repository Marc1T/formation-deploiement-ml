"""Étape `train` : entraînement du modèle, suivi MLflow, sauvegarde joblib.

La logique ML est dans `diabetes_ml.model` ; ce script l'orchestre et trace
l'exécution dans MLflow (paramètres, métriques, modèle).
"""

from __future__ import annotations

from datetime import UTC, datetime

import mlflow
import mlflow.sklearn
import pandas as pd

from diabetes_ml import __version__
from diabetes_ml.config import load_params, project_root, tracking_uri
from diabetes_ml.data import FEATURES, TARGET
from diabetes_ml.model import build_pipeline, fit, save

__all__ = ["build_pipeline", "fit", "save", "main"]


def main() -> None:
    params = load_params()
    root = project_root()
    train_params = params["train"]
    train_df = pd.read_csv(root / params["data"]["processed_dir"] / "train.csv")

    mlflow.set_tracking_uri(tracking_uri(params))
    mlflow.set_experiment(params["mlflow"]["experiment"])

    with mlflow.start_run(run_name=f"{train_params['model']}") as run:
        mlflow.log_params({k: v for k, v in train_params.items() if k != "model_dir"})
        mlflow.log_param("n_train", len(train_df))
        mlflow.set_tag("stage", "train")

        pipe, metrics = fit(train_df, train_params)
        mlflow.log_metrics(metrics)

        # cloudpickle : format classique, lisible par toutes les versions de MLflow.
        # Le format skops (défaut récent) exige de déclarer les types « de confiance »
        # des forêts aléatoires via skops_trusted_types.
        mlflow.sklearn.log_model(
            pipe,
            name="model",
            input_example=train_df[FEATURES].head(3),
            serialization_format=mlflow.sklearn.SERIALIZATION_FORMAT_CLOUDPICKLE,
        )

        info = {
            "model": train_params["model"],
            "features": FEATURES,
            "target": TARGET,
            "version": __version__,
            "trained_at": datetime.now(UTC).isoformat(timespec="seconds"),
            "mlflow_run_id": run.info.run_id,
            "metrics": metrics,
        }
        save(pipe, root / train_params["model_dir"], info)

    print(
        f"train : {train_params['model']} | cv_accuracy={metrics['cv_accuracy']:.3f} "
        f"| cv_roc_auc={metrics['cv_roc_auc']:.3f} | run {run.info.run_id[:8]}"
    )


if __name__ == "__main__":
    main()
