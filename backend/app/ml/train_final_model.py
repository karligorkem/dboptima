from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import joblib
import pandas as pd

from sklearn.ensemble import RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sqlalchemy import select

from app.db.session import SessionLocal
from app.models.ml_training_sample import MLTrainingSample


RANDOM_STATE = 42

RECOMMENDED_THRESHOLD = 20.0
REVIEW_THRESHOLD = 5.0


FEATURE_COLUMNS = [
    "total_calls",
    "latency_sample_count",
    "avg_latency_ms",
    "min_latency_ms",
    "max_latency_ms",
    "p95_latency_ms",
    "plan_total_cost",
    "plan_rows",
    "filter_column_count",
    "index_column_count",
    "historical_success_rate",
    "historical_avg_improvement",
]

TARGET_COLUMN = "improvement_percent"


ML_DIR = Path(__file__).resolve().parent

ARTIFACT_DIR = (
    ML_DIR
    / "artifacts"
)

MODEL_PATH = (
    ARTIFACT_DIR
    / "index_improvement_model_final.joblib"
)

METADATA_PATH = (
    ARTIFACT_DIR
    / "index_improvement_model_final_metadata.json"
)


def load_training_data() -> pd.DataFrame:
    db = SessionLocal()

    try:
        samples = db.scalars(
            select(
                MLTrainingSample
            ).order_by(
                MLTrainingSample.id.asc()
            )
        ).all()

        rows = []

        for sample in samples:
            rows.append(
                {
                    "query_id": (
                        sample.query_id
                    ),
                    "total_calls": (
                        sample.total_calls
                    ),
                    "latency_sample_count": (
                        sample.latency_sample_count
                    ),
                    "avg_latency_ms": (
                        sample.avg_latency_ms
                    ),
                    "min_latency_ms": (
                        sample.min_latency_ms
                    ),
                    "max_latency_ms": (
                        sample.max_latency_ms
                    ),
                    "p95_latency_ms": (
                        sample.p95_latency_ms
                    ),
                    "plan_total_cost": (
                        sample.plan_total_cost
                    ),
                    "plan_rows": (
                        sample.plan_rows
                    ),
                    "filter_column_count": (
                        sample.filter_column_count
                    ),
                    "index_column_count": (
                        sample.index_column_count
                    ),
                    "historical_success_rate": (
                        sample.historical_success_rate
                    ),
                    "historical_avg_improvement": (
                        sample.historical_avg_improvement
                    ),
                    "improvement_percent": (
                        sample.improvement_percent
                    ),
                }
            )

        return pd.DataFrame(
            rows
        )

    finally:
        db.close()


def clean_dataset(
    dataframe: pd.DataFrame,
) -> pd.DataFrame:
    dataframe = dataframe.copy()

    dataframe[TARGET_COLUMN] = (
        pd.to_numeric(
            dataframe[TARGET_COLUMN],
            errors="coerce",
        )
    )

    for column in FEATURE_COLUMNS:
        dataframe[column] = (
            pd.to_numeric(
                dataframe[column],
                errors="coerce",
            )
        )

    dataframe = dataframe.dropna(
        subset=[
            TARGET_COLUMN
        ]
    )

    return dataframe


def build_model() -> Pipeline:
    return Pipeline(
        steps=[
            (
                "imputer",
                SimpleImputer(
                    strategy="median",
                ),
            ),
            (
                "model",
                RandomForestRegressor(
                    n_estimators=600,
                    min_samples_leaf=2,
                    random_state=RANDOM_STATE,
                    n_jobs=-1,
                ),
            ),
        ]
    )


def train() -> None:
    print(
        "=" * 72
    )

    print(
        "DBOPTIMA FINAL ML MODEL TRAINING"
    )

    print(
        "=" * 72
    )

    dataframe = (
        load_training_data()
    )

    dataframe = (
        clean_dataset(
            dataframe
        )
    )

    if dataframe.empty:
        raise RuntimeError(
            "No usable ML training samples found."
        )

    x = dataframe[
        FEATURE_COLUMNS
    ]

    y = dataframe[
        TARGET_COLUMN
    ]

    sample_count = len(
        dataframe
    )

    query_family_count = (
        dataframe[
            "query_id"
        ].nunique()
    )

    print(
        "Samples:",
        sample_count,
    )

    print(
        "Query families:",
        query_family_count,
    )

    print()
    print(
        "Training final Random Forest..."
    )

    model = build_model()

    model.fit(
        x,
        y,
    )

    ARTIFACT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    artifact = {
        "model": model,
        "feature_columns": (
            FEATURE_COLUMNS
        ),
        "target": (
            TARGET_COLUMN
        ),
        "thresholds": {
            "recommended": (
                RECOMMENDED_THRESHOLD
            ),
            "review": (
                REVIEW_THRESHOLD
            ),
        },
    }

    joblib.dump(
        artifact,
        MODEL_PATH,
    )

    metadata = {
        "model_name": (
            "RandomForestRegressor"
        ),
        "model_role": (
            "candidate_ranking"
        ),
        "sample_count": (
            sample_count
        ),
        "query_family_count": (
            query_family_count
        ),
        "target": (
            TARGET_COLUMN
        ),
        "features": (
            FEATURE_COLUMNS
        ),
        "thresholds": {
            "recommended": (
                RECOMMENDED_THRESHOLD
            ),
            "review": (
                REVIEW_THRESHOLD
            ),
        },
        "evaluation": {
            "method": (
                "5-fold GroupKFold "
                "by query_id"
            ),
            "mae_mean": 13.6286,
            "mae_std": 1.8527,
            "rmse_mean": 20.7764,
            "rmse_std": 2.0239,
            "r2_mean": 0.7323,
            "r2_std": 0.1222,
            "accuracy_mean": 0.7131,
            "accuracy_std": 0.1367,
            "balanced_accuracy_mean": (
                0.6580
            ),
            "balanced_accuracy_std": (
                0.0754
            ),
        },
        "trained_at": (
            datetime.now(
                timezone.utc
            ).isoformat()
        ),
    }

    with open(
        METADATA_PATH,
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            metadata,
            file,
            indent=4,
        )

    print()
    print(
        "FINAL MODEL TRAINED"
    )

    print()
    print(
        "Model:"
    )

    print(
        MODEL_PATH
    )

    print()
    print(
        "Metadata:"
    )

    print(
        METADATA_PATH
    )


if __name__ == "__main__":
    train()