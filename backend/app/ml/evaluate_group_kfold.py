from __future__ import annotations

import numpy as np
import pandas as pd

from sklearn.ensemble import (
    HistGradientBoostingRegressor,
    RandomForestRegressor,
)
from sklearn.impute import SimpleImputer
from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    mean_absolute_error,
    mean_squared_error,
    r2_score,
)
from sklearn.model_selection import GroupKFold
from sklearn.pipeline import Pipeline

from sqlalchemy import select

from app.db.session import SessionLocal
from app.models.ml_training_sample import MLTrainingSample


N_SPLITS = 5
RANDOM_STATE = 42

RECOMMENDED_THRESHOLD = 20.0
REVIEW_THRESHOLD = 5.0


# Sadece index benchmarkindan ONCE bilinebilecek feature'lar.
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
GROUP_COLUMN = "query_id"


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
                    "query_id": sample.query_id,
                    "total_calls": sample.total_calls,
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
                    "decision_status": (
                        sample.decision_status
                    ),
                }
            )

        return pd.DataFrame(rows)

    finally:
        db.close()


def clean_dataset(
    dataframe: pd.DataFrame,
) -> pd.DataFrame:
    dataframe = dataframe.copy()

    dataframe = dataframe.dropna(
        subset=[
            TARGET_COLUMN,
            GROUP_COLUMN,
        ]
    )

    for column in FEATURE_COLUMNS:
        dataframe[column] = pd.to_numeric(
            dataframe[column],
            errors="coerce",
        )

    dataframe[TARGET_COLUMN] = pd.to_numeric(
        dataframe[TARGET_COLUMN],
        errors="coerce",
    )

    return dataframe.dropna(
        subset=[
            TARGET_COLUMN,
            GROUP_COLUMN,
        ]
    )


def improvement_to_status(
    value: float,
) -> str:
    if value >= RECOMMENDED_THRESHOLD:
        return "RECOMMENDED"

    if value >= REVIEW_THRESHOLD:
        return "REVIEW"

    return "REJECTED"


def build_models() -> dict[str, Pipeline]:
    return {
        "random_forest": Pipeline(
            steps=[
                (
                    "imputer",
                    SimpleImputer(
                        strategy="median"
                    ),
                ),
                (
                    "model",
                    RandomForestRegressor(
                        n_estimators=400,
                        min_samples_leaf=2,
                        random_state=RANDOM_STATE,
                        n_jobs=-1,
                    ),
                ),
            ]
        ),
        "hist_gradient_boosting": Pipeline(
            steps=[
                (
                    "imputer",
                    SimpleImputer(
                        strategy="median"
                    ),
                ),
                (
                    "model",
                    HistGradientBoostingRegressor(
                        max_iter=300,
                        learning_rate=0.05,
                        max_leaf_nodes=15,
                        min_samples_leaf=10,
                        random_state=RANDOM_STATE,
                    ),
                ),
            ]
        ),
    }


def evaluate() -> None:
    dataframe = load_training_data()
    dataframe = clean_dataset(
        dataframe
    )

    print(
        "=" * 72
    )
    print(
        "DBOPTIMA 5-FOLD GROUPED CROSS VALIDATION"
    )
    print(
        "=" * 72
    )

    print(
        "Total samples:",
        len(dataframe),
    )

    unique_families = dataframe[
        GROUP_COLUMN
    ].nunique()

    print(
        "Unique query families:",
        unique_families,
    )

    print()
    print(
        "Features:"
    )

    for feature in FEATURE_COLUMNS:
        print(
            f"  - {feature}"
        )

    x = dataframe[
        FEATURE_COLUMNS
    ]

    y = dataframe[
        TARGET_COLUMN
    ]

    groups = dataframe[
        GROUP_COLUMN
    ]

    splitter = GroupKFold(
        n_splits=N_SPLITS
    )

    all_results = {}

    for model_name in build_models():
        print()
        print(
            "=" * 72
        )
        print(
            "MODEL:",
            model_name,
        )
        print(
            "=" * 72
        )

        fold_metrics = []

        for fold_number, (
            train_indexes,
            test_indexes,
        ) in enumerate(
            splitter.split(
                x,
                y,
                groups,
            ),
            start=1,
        ):
            x_train = x.iloc[
                train_indexes
            ]
            x_test = x.iloc[
                test_indexes
            ]

            y_train = y.iloc[
                train_indexes
            ]
            y_test = y.iloc[
                test_indexes
            ]

            train_groups = set(
                groups.iloc[
                    train_indexes
                ]
            )

            test_groups = set(
                groups.iloc[
                    test_indexes
                ]
            )

            overlap = (
                train_groups
                & test_groups
            )

            if overlap:
                raise RuntimeError(
                    "Query family leakage detected."
                )

            # Her fold icin sifir model.
            model = build_models()[
                model_name
            ]

            model.fit(
                x_train,
                y_train,
            )

            predictions = model.predict(
                x_test
            )

            mae = mean_absolute_error(
                y_test,
                predictions,
            )

            rmse = np.sqrt(
                mean_squared_error(
                    y_test,
                    predictions,
                )
            )

            r2 = r2_score(
                y_test,
                predictions,
            )

            actual_status = [
                improvement_to_status(
                    float(value)
                )
                for value in y_test
            ]

            predicted_status = [
                improvement_to_status(
                    float(value)
                )
                for value in predictions
            ]

            accuracy = accuracy_score(
                actual_status,
                predicted_status,
            )

            balanced_accuracy = (
                balanced_accuracy_score(
                    actual_status,
                    predicted_status,
                )
            )

            metrics = {
                "mae": float(mae),
                "rmse": float(rmse),
                "r2": float(r2),
                "accuracy": float(
                    accuracy
                ),
                "balanced_accuracy": float(
                    balanced_accuracy
                ),
            }

            fold_metrics.append(
                metrics
            )

            print()
            print(
                f"Fold {fold_number}/{N_SPLITS}"
            )

            print(
                "  Train samples:",
                len(train_indexes),
            )

            print(
                "  Test samples:",
                len(test_indexes),
            )

            print(
                "  Train families:",
                len(train_groups),
            )

            print(
                "  Test families:",
                len(test_groups),
            )

            print(
                "  Family overlap:",
                len(overlap),
            )

            print(
                f"  MAE: "
                f"{mae:.4f}"
            )

            print(
                f"  RMSE: "
                f"{rmse:.4f}"
            )

            print(
                f"  R2: "
                f"{r2:.4f}"
            )

            print(
                f"  Accuracy: "
                f"{accuracy * 100:.2f}%"
            )

            print(
                "  Balanced accuracy: "
                f"{balanced_accuracy * 100:.2f}%"
            )

        metric_names = [
            "mae",
            "rmse",
            "r2",
            "accuracy",
            "balanced_accuracy",
        ]

        summary = {}

        print()
        print(
            "-" * 72
        )
        print(
            "CROSS-VALIDATION SUMMARY"
        )
        print(
            "-" * 72
        )

        for metric_name in metric_names:
            values = np.array(
                [
                    fold[
                        metric_name
                    ]
                    for fold in fold_metrics
                ]
            )

            mean_value = float(
                np.mean(values)
            )

            std_value = float(
                np.std(values)
            )

            summary[
                metric_name
            ] = {
                "mean": mean_value,
                "std": std_value,
            }

            if metric_name in {
                "accuracy",
                "balanced_accuracy",
            }:
                print(
                    f"{metric_name}: "
                    f"{mean_value * 100:.2f}% "
                    f"+/- "
                    f"{std_value * 100:.2f}%"
                )
            else:
                print(
                    f"{metric_name}: "
                    f"{mean_value:.4f} "
                    f"+/- "
                    f"{std_value:.4f}"
                )

        all_results[
            model_name
        ] = summary

    print()
    print(
        "=" * 72
    )
    print(
        "FINAL MODEL COMPARISON"
    )
    print(
        "=" * 72
    )

    for (
        model_name,
        summary,
    ) in all_results.items():
        print()
        print(
            model_name
        )

        print(
            "  MAE:",
            f"{summary['mae']['mean']:.4f}",
            "+/-",
            f"{summary['mae']['std']:.4f}",
        )

        print(
            "  R2:",
            f"{summary['r2']['mean']:.4f}",
            "+/-",
            f"{summary['r2']['std']:.4f}",
        )

        print(
            "  Accuracy:",
            f"{summary['accuracy']['mean'] * 100:.2f}%",
            "+/-",
            f"{summary['accuracy']['std'] * 100:.2f}%",
        )

        print(
            "  Balanced accuracy:",
            f"{summary['balanced_accuracy']['mean'] * 100:.2f}%",
            "+/-",
            f"{summary['balanced_accuracy']['std'] * 100:.2f}%",
        )

    best_model = min(
        all_results,
        key=lambda name: (
            all_results[
                name
            ]["mae"]["mean"]
        ),
    )

    print()
    print(
        "=" * 72
    )

    print(
        "BEST MODEL BY GROUPED CV MAE:",
        best_model,
    )

    print(
        "=" * 72
    )


if __name__ == "__main__":
    evaluate()