from __future__ import annotations

import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import (
    HistGradientBoostingRegressor,
    RandomForestRegressor,
)
from sklearn.metrics import (
    mean_absolute_error,
    mean_squared_error,
    r2_score,
)
from sklearn.model_selection import train_test_split
from sqlalchemy import select

from app.db.session import SessionLocal
from app.models.ml_training_sample import MLTrainingSample


RANDOM_STATE = 42
TEST_SIZE = 0.20

RECOMMENDED_THRESHOLD = 20.0
REVIEW_THRESHOLD = 5.0

ML_DIR = Path(__file__).resolve().parent
ARTIFACT_DIR = ML_DIR / "artifacts"

MODEL_PATH = (
    ARTIFACT_DIR
    / "index_improvement_model.joblib"
)

METADATA_PATH = (
    ARTIFACT_DIR
    / "index_improvement_model_metadata.json"
)


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
    "benchmark_before_ms",
    "benchmark_stability",
    "historical_success_rate",
    "historical_avg_improvement",
    "historical_avg_confidence",
]

TARGET_COLUMN = (
    "improvement_percent"
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
                    "id": sample.id,
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
                    "benchmark_before_ms": (
                        sample.benchmark_before_ms
                    ),
                    "benchmark_stability": (
                        sample.benchmark_stability
                    ),
                    "historical_success_rate": (
                        sample.historical_success_rate
                    ),
                    "historical_avg_improvement": (
                        sample.historical_avg_improvement
                    ),
                    "historical_avg_confidence": (
                        sample.historical_avg_confidence
                    ),
                    "improvement_percent": (
                        sample.improvement_percent
                    ),
                    "decision_status": (
                        sample.decision_status
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

    dataframe = dataframe.dropna(
        subset=[
            TARGET_COLUMN
        ]
    )

    for column in FEATURE_COLUMNS:
        dataframe[column] = (
            pd.to_numeric(
                dataframe[column],
                errors="coerce",
            )
        )

    dataframe[TARGET_COLUMN] = (
        pd.to_numeric(
            dataframe[TARGET_COLUMN],
            errors="coerce",
        )
    )

    dataframe = dataframe.dropna(
        subset=[
            TARGET_COLUMN
        ]
    )

    return dataframe


def get_feature_matrix(
    dataframe: pd.DataFrame,
) -> pd.DataFrame:
    features = dataframe[
        FEATURE_COLUMNS
    ].copy()

    for column in FEATURE_COLUMNS:
        median_value = (
            features[column]
            .median()
        )

        if pd.isna(
            median_value
        ):
            median_value = 0.0

        features[column] = (
            features[column]
            .fillna(
                median_value
            )
        )

    return features


def improvement_to_status(
    improvement: float,
) -> str:
    if (
        improvement
        >= RECOMMENDED_THRESHOLD
    ):
        return "RECOMMENDED"

    if (
        improvement
        >= REVIEW_THRESHOLD
    ):
        return "REVIEW"

    return "REJECTED"


def calculate_status_accuracy(
    actual_values: np.ndarray,
    predicted_values: np.ndarray,
) -> float:
    actual_statuses = [
        improvement_to_status(
            float(value)
        )
        for value in actual_values
    ]

    predicted_statuses = [
        improvement_to_status(
            float(value)
        )
        for value in predicted_values
    ]

    correct = sum(
        actual == predicted
        for actual, predicted
        in zip(
            actual_statuses,
            predicted_statuses,
        )
    )

    if not actual_statuses:
        return 0.0

    return (
        correct
        / len(actual_statuses)
    )


def evaluate_model(
    model,
    x_test: pd.DataFrame,
    y_test: pd.Series,
) -> dict[str, float]:
    predictions = model.predict(
        x_test
    )

    mae = mean_absolute_error(
        y_test,
        predictions,
    )

    rmse = (
        mean_squared_error(
            y_test,
            predictions,
        )
        ** 0.5
    )

    r2 = r2_score(
        y_test,
        predictions,
    )

    status_accuracy = (
        calculate_status_accuracy(
            actual_values=(
                y_test.to_numpy()
            ),
            predicted_values=(
                predictions
            ),
        )
    )

    return {
        "mae": round(
            float(mae),
            4,
        ),
        "rmse": round(
            float(rmse),
            4,
        ),
        "r2": round(
            float(r2),
            4,
        ),
        "status_accuracy": round(
            float(
                status_accuracy
            ),
            4,
        ),
    }


def build_models() -> dict:
    return {
        "random_forest": (
            RandomForestRegressor(
                n_estimators=400,
                max_depth=None,
                min_samples_leaf=2,
                random_state=(
                    RANDOM_STATE
                ),
                n_jobs=-1,
            )
        ),
        "hist_gradient_boosting": (
            HistGradientBoostingRegressor(
                max_iter=300,
                learning_rate=0.05,
                max_leaf_nodes=15,
                min_samples_leaf=10,
                random_state=(
                    RANDOM_STATE
                ),
            )
        ),
    }


def train() -> None:
    print()
    print(
        "=" * 70
    )

    print(
        "DBOPTIMA ML TRAINING"
    )

    print(
        "=" * 70
    )

    dataframe = (
        load_training_data()
    )

    if dataframe.empty:
        raise RuntimeError(
            "ml_training_samples "
            "table is empty."
        )

    dataframe = (
        clean_dataset(
            dataframe
        )
    )

    print(
        "Total samples:",
        len(dataframe),
    )

    print()
    print(
        "Decision distribution:"
    )

    print(
        dataframe[
            "decision_status"
        ].value_counts()
    )

    if len(dataframe) < 100:
        print()
        print(
            "WARNING: Dataset is "
            "still small."
        )

    x = get_feature_matrix(
        dataframe
    )

    y = dataframe[
        TARGET_COLUMN
    ]

    (
        x_train,
        x_test,
        y_train,
        y_test,
    ) = train_test_split(
        x,
        y,
        test_size=TEST_SIZE,
        random_state=(
            RANDOM_STATE
        ),
    )

    print()
    print(
        "Train samples:",
        len(x_train),
    )

    print(
        "Test samples:",
        len(x_test),
    )

    models = build_models()

    results = {}

    best_model_name = None
    best_model = None
    best_mae = float(
        "inf"
    )

    for (
        model_name,
        model,
    ) in models.items():
        print()
        print(
            "-" * 70
        )

        print(
            "Training:",
            model_name,
        )

        model.fit(
            x_train,
            y_train,
        )

        metrics = (
            evaluate_model(
                model=model,
                x_test=x_test,
                y_test=y_test,
            )
        )

        results[
            model_name
        ] = metrics

        print(
            "MAE:",
            metrics["mae"],
        )

        print(
            "RMSE:",
            metrics["rmse"],
        )

        print(
            "R2:",
            metrics["r2"],
        )

        print(
            "Status accuracy:",
            f"{metrics['status_accuracy'] * 100:.2f}%",
        )

        if (
            metrics["mae"]
            < best_mae
        ):
            best_mae = (
                metrics["mae"]
            )

            best_model_name = (
                model_name
            )

            best_model = model

    if best_model is None:
        raise RuntimeError(
            "No model was trained."
        )

    print()
    print(
        "=" * 70
    )

    print(
        "BEST MODEL:",
        best_model_name,
    )

    print(
        "BEST MAE:",
        best_mae,
    )

    ARTIFACT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    #
    # Final modeli tüm mevcut
    # dataset üzerinde yeniden eğitiyoruz.
    #
    best_model.fit(
        x,
        y,
    )

    artifact = {
        "model": best_model,
        "feature_columns": (
            FEATURE_COLUMNS
        ),
    }

    joblib.dump(
        artifact,
        MODEL_PATH,
    )

    metadata = {
        "model_name": (
            best_model_name
        ),
        "sample_count": (
            len(dataframe)
        ),
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
        "test_results": (
            results
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
        "Model saved:"
    )

    print(
        MODEL_PATH
    )

    print()
    print(
        "Metadata saved:"
    )

    print(
        METADATA_PATH
    )

    print()
    print(
        "TRAINING COMPLETE"
    )


if __name__ == "__main__":
    train()