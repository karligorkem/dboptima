from __future__ import annotations

import math

import numpy as np
import pandas as pd

from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.metrics import (
    mean_absolute_error,
    mean_squared_error,
    r2_score,
)
from sklearn.model_selection import GroupKFold
from sklearn.pipeline import Pipeline

from app.db.session import SessionLocal
from app.models.ml_training_sample_v2 import MLTrainingSampleV2


FEATURE_COLUMNS = [
    "total_calls",
    "latency_sample_count",
    "avg_latency_ms",
    "min_latency_ms",
    "max_latency_ms",
    "p95_latency_ms",

    "plan_total_cost",
    "plan_rows",

    "seq_scan_count",
    "actual_rows",
    "rows_removed_by_filter",
    "actual_total_time_ms",
    "actual_loops",

    "scan_selectivity_ratio",
    "removed_to_returned_ratio",

    "equality_filter_count",
    "range_filter_count",
    "like_filter_count",

    "has_order_by",
    "has_limit",

    "candidate_column_count",
    "candidate_has_order_column",

    "source_actual_rows",
    "source_rows_removed_by_filter",

    "historical_success_rate",
    "historical_avg_improvement",
]


TARGET_COLUMN = "improvement_percent"


def improvement_to_status(
    value: float,
) -> str:

    if value >= 20.0:
        return "RECOMMENDED"

    if value >= 5.0:
        return "REVIEW"

    return "REJECTED"


def build_model() -> Pipeline:

    preprocessor = ColumnTransformer(
        transformers=[
            (
                "numeric",
                SimpleImputer(
                    strategy="median"
                ),
                FEATURE_COLUMNS,
            )
        ],
        remainder="drop",
    )

    regressor = RandomForestRegressor(
        n_estimators=600,
        min_samples_leaf=2,
        random_state=42,
        n_jobs=-1,
    )

    return Pipeline(
        steps=[
            (
                "preprocessor",
                preprocessor,
            ),
            (
                "model",
                regressor,
            ),
        ]
    )


def load_dataset() -> pd.DataFrame:

    db = SessionLocal()

    try:

        rows = (
            db.query(
                MLTrainingSampleV2
            )
            .order_by(
                MLTrainingSampleV2.id.asc()
            )
            .all()
        )

        records = []

        for row in rows:

            records.append(
                {
                    "id": row.id,
                    "query_id": row.query_id,
                    "recommendation_id": row.recommendation_id,

                    "total_calls": row.total_calls,
                    "latency_sample_count": row.latency_sample_count,

                    "avg_latency_ms": row.avg_latency_ms,
                    "min_latency_ms": row.min_latency_ms,
                    "max_latency_ms": row.max_latency_ms,
                    "p95_latency_ms": row.p95_latency_ms,

                    "plan_total_cost": row.plan_total_cost,
                    "plan_rows": row.plan_rows,

                    "seq_scan_count": row.seq_scan_count,
                    "actual_rows": row.actual_rows,

                    "rows_removed_by_filter": (
                        row.rows_removed_by_filter
                    ),

                    "actual_total_time_ms": (
                        row.actual_total_time_ms
                    ),

                    "actual_loops": row.actual_loops,

                    "scan_selectivity_ratio": (
                        row.scan_selectivity_ratio
                    ),

                    "removed_to_returned_ratio": (
                        row.removed_to_returned_ratio
                    ),

                    "equality_filter_count": (
                        row.equality_filter_count
                    ),

                    "range_filter_count": (
                        row.range_filter_count
                    ),

                    "like_filter_count": (
                        row.like_filter_count
                    ),

                    "has_order_by": row.has_order_by,
                    "has_limit": row.has_limit,

                    "candidate_column_count": (
                        row.candidate_column_count
                    ),

                    "candidate_has_order_column": (
                        row.candidate_has_order_column
                    ),

                    "source_actual_rows": (
                        row.source_actual_rows
                    ),

                    "source_rows_removed_by_filter": (
                        row.source_rows_removed_by_filter
                    ),

                    "historical_success_rate": (
                        row.historical_success_rate
                    ),

                    "historical_avg_improvement": (
                        row.historical_avg_improvement
                    ),

                    "improvement_percent": (
                        row.improvement_percent
                    ),
                }
            )

        return pd.DataFrame(
            records
        )

    finally:
        db.close()


def status_accuracy(
    actual: np.ndarray,
    predicted: np.ndarray,
) -> float:

    actual_status = [
        improvement_to_status(
            float(value)
        )
        for value in actual
    ]

    predicted_status = [
        improvement_to_status(
            float(value)
        )
        for value in predicted
    ]

    correct = sum(
        actual_item == predicted_item
        for actual_item, predicted_item
        in zip(
            actual_status,
            predicted_status,
        )
    )

    return (
        correct
        / len(actual_status)
        * 100.0
    )


def main() -> None:

    dataframe = load_dataset()

    dataframe = dataframe.dropna(
        subset=[
            "query_id",
            TARGET_COLUMN,
        ]
    ).reset_index(
        drop=True
    )

    print()
    print(
        "=" * 80
    )

    print(
        "DBOptima V2 Cold-Start Evaluation"
    )

    print(
        "=" * 80
    )

    print(
        f"Total samples: "
        f"{len(dataframe)}"
    )

    print(
        f"Query groups:  "
        f"{dataframe['query_id'].nunique()}"
    )

    cold_start_mask = (
        dataframe[
            "historical_success_rate"
        ].isna()
        &
        dataframe[
            "historical_avg_improvement"
        ].isna()
    )

    print(
        f"Cold-start rows in dataset: "
        f"{cold_start_mask.sum()}"
    )

    groups = dataframe[
        "query_id"
    ]

    x = dataframe[
        FEATURE_COLUMNS
    ]

    y = dataframe[
        TARGET_COLUMN
    ].astype(
        float
    )

    group_kfold = GroupKFold(
        n_splits=5
    )

    all_actual = []
    all_predicted = []

    fold_results = []

    for fold_number, (
        train_index,
        test_index,
    ) in enumerate(
        group_kfold.split(
            x,
            y,
            groups=groups,
        ),
        start=1,
    ):

        train_df = dataframe.iloc[
            train_index
        ].copy()

        test_df = dataframe.iloc[
            test_index
        ].copy()

        cold_test = test_df[
            test_df[
                "historical_success_rate"
            ].isna()
            &
            test_df[
                "historical_avg_improvement"
            ].isna()
        ].copy()

        if cold_test.empty:

            print()
            print(
                f"Fold {fold_number}: "
                f"no cold-start samples"
            )

            continue

        model = build_model()

        model.fit(
            train_df[
                FEATURE_COLUMNS
            ],
            train_df[
                TARGET_COLUMN
            ].astype(float),
        )

        predictions = model.predict(
            cold_test[
                FEATURE_COLUMNS
            ]
        )

        actual = cold_test[
            TARGET_COLUMN
        ].astype(
            float
        ).to_numpy()

        mae = mean_absolute_error(
            actual,
            predictions,
        )

        rmse = math.sqrt(
            mean_squared_error(
                actual,
                predictions,
            )
        )

        if len(actual) >= 2:

            r2 = r2_score(
                actual,
                predictions,
            )

        else:
            r2 = float("nan")

        accuracy = status_accuracy(
            actual=actual,
            predicted=predictions,
        )

        all_actual.extend(
            actual.tolist()
        )

        all_predicted.extend(
            predictions.tolist()
        )

        fold_results.append(
            {
                "fold": fold_number,
                "count": len(actual),
                "mae": mae,
                "rmse": rmse,
                "r2": r2,
                "accuracy": accuracy,
            }
        )

        print()
        print(
            f"Fold {fold_number}"
        )

        print(
            f"Cold-start samples: "
            f"{len(actual)}"
        )

        print(
            f"MAE:              "
            f"{mae:.4f}"
        )

        print(
            f"RMSE:             "
            f"{rmse:.4f}"
        )

        print(
            f"R2:               "
            f"{r2:.4f}"
        )

        print(
            f"Status accuracy:  "
            f"{accuracy:.2f}%"
        )

    if not all_actual:

        raise RuntimeError(
            "No cold-start samples "
            "were found in GroupKFold tests."
        )

    actual_array = np.array(
        all_actual,
        dtype=float,
    )

    predicted_array = np.array(
        all_predicted,
        dtype=float,
    )

    overall_mae = mean_absolute_error(
        actual_array,
        predicted_array,
    )

    overall_rmse = math.sqrt(
        mean_squared_error(
            actual_array,
            predicted_array,
        )
    )

    overall_r2 = r2_score(
        actual_array,
        predicted_array,
    )

    overall_accuracy = (
        status_accuracy(
            actual=actual_array,
            predicted=predicted_array,
        )
    )

    print()
    print(
        "=" * 80
    )

    print(
        "V2 COLD-START SUMMARY"
    )

    print(
        "=" * 80
    )

    print(
        f"Cold-start samples: "
        f"{len(actual_array)}"
    )

    print(
        f"MAE:              "
        f"{overall_mae:.4f}"
    )

    print(
        f"RMSE:             "
        f"{overall_rmse:.4f}"
    )

    print(
        f"R2:               "
        f"{overall_r2:.4f}"
    )

    print(
        f"Status accuracy:  "
        f"{overall_accuracy:.2f}%"
    )

    print(
        "=" * 80
    )

    errors = np.abs(
        actual_array
        - predicted_array
    )

    worst_indices = np.argsort(
        errors
    )[::-1][:10]

    print()
    print(
        "WORST COLD-START PREDICTIONS"
    )

    print(
        "=" * 80
    )

    for rank, index in enumerate(
        worst_indices,
        start=1,
    ):

        actual_value = actual_array[
            index
        ]

        predicted_value = predicted_array[
            index
        ]

        error = errors[
            index
        ]

        actual_status = (
            improvement_to_status(
                actual_value
            )
        )

        predicted_status = (
            improvement_to_status(
                predicted_value
            )
        )

        print(
            f"{rank:>2}. "
            f"actual={actual_value:>8.2f}% "
            f"predicted={predicted_value:>8.2f}% "
            f"error={error:>8.2f} "
            f"{actual_status:>11} -> "
            f"{predicted_status}"
        )


if __name__ == "__main__":
    main()