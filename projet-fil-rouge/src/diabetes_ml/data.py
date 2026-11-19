"""Étape `prepare` : nettoyage et découpage train / test.

Dans le jeu de données Pima, un 0 dans glucose, blood_pressure, skin_thickness,
insulin ou bmi signifie « valeur manquante ». On le remplace par NaN ; l'imputation
est faite ensuite dans le pipeline scikit-learn, pour qu'elle soit embarquée
dans le modèle déployé.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split

from diabetes_ml.config import load_params, project_root

FEATURES: list[str] = [
    "pregnancies",
    "glucose",
    "blood_pressure",
    "skin_thickness",
    "insulin",
    "bmi",
    "diabetes_pedigree",
    "age",
]
TARGET = "outcome"
ZERO_MEANS_MISSING = ["glucose", "blood_pressure", "skin_thickness", "insulin", "bmi"]


def load_raw(path: str | Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    missing = set(FEATURES + [TARGET]) - set(df.columns)
    if missing:
        raise ValueError(f"Colonnes manquantes dans {path} : {sorted(missing)}")
    return df


def clean(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    for col in ZERO_MEANS_MISSING:
        out[col] = out[col].replace(0, np.nan)
    return out


def split(
    df: pd.DataFrame, test_size: float, random_state: int
) -> tuple[pd.DataFrame, pd.DataFrame]:
    train, test = train_test_split(
        df, test_size=test_size, random_state=random_state, stratify=df[TARGET]
    )
    return train.reset_index(drop=True), test.reset_index(drop=True)


def main() -> None:
    params = load_params()["data"]
    root = project_root()
    df = clean(load_raw(root / params["raw_path"]))
    train, test = split(df, params["test_size"], params["random_state"])

    out_dir = root / params["processed_dir"]
    out_dir.mkdir(parents=True, exist_ok=True)
    train.to_csv(out_dir / "train.csv", index=False)
    test.to_csv(out_dir / "test.csv", index=False)
    print(f"prepare : {len(train)} lignes train, {len(test)} lignes test -> {out_dir}")


if __name__ == "__main__":
    main()
