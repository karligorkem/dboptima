from __future__ import annotations

import math
from pathlib import Path

import joblib
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


# ============================================================
# PATHS
# ============================================================


ML_DIR = Path(
    __file__
).resolve().parent

ARTIFACT_DIR = (
    ML_DIR
    / "artifacts"
)

ARTIFACT_DIR.mkdir(
    parents=True,
    exist_ok=True,
)

MODEL_PATH = (
    ARTIFACT_DIR
    / "index_improvement_model_v2.joblib"
)


# ============================================================
# FEATURE SET
#
# IMPORTANT:
# benchmark_before_ms
# benchmark_after_ms
# improvement_percent
# benchmark_stability
# decision_confidence
# decision_status
#
# inference feature değildir.
# ============================================================


FEATURE_COLUMNS = [
    # -----------------------------------------
    # QUERY / LATENCY
    # -----------------------------------------
    "total_calls",
    "latency_sample_count",
    "avg_latency_ms",
    "min_latency_ms",
    "max_latency_ms",
    "p95_latency_ms",

    # -----------------------------------------
    # PLAN
    # -----------------------------------------
    "plan_total_cost",
    "plan_rows",
    "seq_scan_count",
    "actual_rows",
    "rows_removed_by_filter",
    "actual_total_time_ms",
    "actual_loops",

    # -----------------------------------------
    # SELECTIVITY
    # -----------------------------------------
    "scan_selectivity_ratio",
    "removed_to_returned_ratio",

    # -----------------------------------------
    # SQL STRUCTURE
    # -----------------------------------------
    "equality_filter_count",
    "range_filter_count",
    "like_filter_count",
    "has_order_by",
    "has_limit",

    # -----------------------------------------
    # CANDIDATE
    # -----------------------------------------
    "candidate_column_count",
    "candidate_has_order_column",

    # -----------------------------------------
    # SOURCE SCAN
    # -----------------------------------------
    "source_actual_rows",
    "source_rows_removed_by_filter",

    # -----------------------------------------
    # HISTORY
    # -----------------------------------------
    "historical_success_rate",
    "historical_avg_improvement",
]


TARGET_COLUMN = (
    "improvement_percent"
)


# ============================================================
# STATUS
# ============================================================


def improvement_to_status(
    value: float,
) -> str:

    if value >= 20.0:
        return "RECOMMENDED"

    if value >= 5.0:
        return "REVIEW"

    return "REJECTED"


# ============================================================
# LOAD DATA
# ============================================================


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

        records: list[dict] = []

        for row in rows:

            record = {
                "id": row.id,
                "query_id": row.query_id,

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
                "rows_removed_by_filter": row.rows_removed_by_filter,
                "actual_total_time_ms": row.actual_total_time_ms,
                "actual_loops": row.actual_loops,

                "scan_selectivity_ratio": row.scan_selectivity_ratio,
                "removed_to_returned_ratio": row.removed_to_returned_ratio,

                "equality_filter_count": row.equality_filter_count,
                "range_filter_count": row.range_filter_count,
                "like_filter_count": row.like_filter_count,

                "has_order_by": row.has_order_by,
                "has_limit": row.has_limit,

                "candidate_column_count": row.candidate_column_count,
                "candidate_has_order_column": row.candidate_has_order_column,

                "source_actual_rows": row.source_actual_rows,
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

            records.append(
                record
            )

        dataframe = pd.DataFrame(
            records
        )

        return dataframe

    finally:
        db.close()


# ============================================================
# MODEL
# ============================================================


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

    pipeline = Pipeline(
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

    return pipeline


# ============================================================
# STATUS ACCURACY
# ============================================================


def calculate_status_accuracy(
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
        1
        for actual_item, predicted_item
        in zip(
            actual_status,
            predicted_status,
        )
        if actual_item
        == predicted_item
    )

    return (
        correct
        / len(actual_status)
        * 100.0
    )


# ============================================================
# GROUP KFOLD
# ============================================================


def evaluate_group_kfold(
    dataframe: pd.DataFrame,
) -> None:

    unique_groups = dataframe[
        "query_id"
    ].nunique()

    n_splits = min(
        5,
        unique_groups,
    )

    if n_splits < 2:
        raise RuntimeError(
            "Not enough query groups "
            "for GroupKFold."
        )

    group_kfold = GroupKFold(
        n_splits=n_splits
    )

    x = dataframe[
        FEATURE_COLUMNS
    ]

    y = dataframe[
        TARGET_COLUMN
    ].astype(
        float
    )

    groups = dataframe[
        "query_id"
    ]

    mae_scores: list[float] = []
    rmse_scores: list[float] = []
    r2_scores: list[float] = []
    status_scores: list[float] = []

    print()
    print(
        "=" * 80
    )

    print(
        "V2 GROUP KFOLD EVALUATION"
    )

    print(
        "=" * 80
    )

    print(
        f"Samples:       {len(dataframe)}"
    )

    print(
        f"Query groups:  {unique_groups}"
    )

    print(
        f"Features:      {len(FEATURE_COLUMNS)}"
    )

    print(
        f"Folds:         {n_splits}"
    )

    print(
        "=" * 80
    )

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

        x_train = x.iloc[
            train_index
        ]

        x_test = x.iloc[
            test_index
        ]

        y_train = y.iloc[
            train_index
        ]

        y_test = y.iloc[
            test_index
        ]

        model = build_model()

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

        rmse = math.sqrt(
            mean_squared_error(
                y_test,
                predictions,
            )
        )

        r2 = r2_score(
            y_test,
            predictions,
        )

        status_accuracy = (
            calculate_status_accuracy(
                actual=y_test.to_numpy(),
                predicted=predictions,
            )
        )

        mae_scores.append(
            mae
        )

        rmse_scores.append(
            rmse
        )

        r2_scores.append(
            r2
        )

        status_scores.append(
            status_accuracy
        )

        print()
        print(
            f"Fold {fold_number}"
        )

        print(
            f"Train samples:    "
            f"{len(train_index)}"
        )

        print(
            f"Test samples:     "
            f"{len(test_index)}"
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
            f"{status_accuracy:.2f}%"
        )

    print()
    print(
        "=" * 80
    )

    print(
        "V2 GROUP KFOLD SUMMARY"
    )

    print(
        "=" * 80
    )

    print(
        f"MAE: "
        f"{np.mean(mae_scores):.4f} "
        f"+/- "
        f"{np.std(mae_scores):.4f}"
    )

    print(
        f"RMSE: "
        f"{np.mean(rmse_scores):.4f} "
        f"+/- "
        f"{np.std(rmse_scores):.4f}"
    )

    print(
        f"R2: "
        f"{np.mean(r2_scores):.4f} "
        f"+/- "
        f"{np.std(r2_scores):.4f}"
    )

    print(
        f"Status accuracy: "
        f"{np.mean(status_scores):.2f}% "
        f"+/- "
        f"{np.std(status_scores):.2f}%"
    )

    print(
        "=" * 80
    )


# ============================================================
# FINAL TRAIN
# ============================================================


def train_final_model(
    dataframe: pd.DataFrame,
) -> None:

    x = dataframe[
        FEATURE_COLUMNS
    ]

    y = dataframe[
        TARGET_COLUMN
    ].astype(
        float
    )

    model = build_model()

    model.fit(
        x,
        y,
    )

    artifact = {
        "version": "v2",

        "model": model,

        "feature_columns": (
            FEATURE_COLUMNS
        ),

        "target_column": (
            TARGET_COLUMN
        ),

        "thresholds": {
            "recommended": 20.0,
            "review": 5.0,
        },

        "training_samples": (
            len(dataframe)
        ),

        "query_groups": (
            dataframe[
                "query_id"
            ].nunique()
        ),
    }

    joblib.dump(
        artifact,
        MODEL_PATH,
    )

    print()
    print(
        f"Final V2 model saved:"
    )

    print(
        MODEL_PATH
    )


# ============================================================
# MAIN
# ============================================================


def main() -> None:

    dataframe = load_dataset()

    if dataframe.empty:
        raise RuntimeError(
            "ml_training_samples_v2 "
            "table is empty."
        )

    dataframe = dataframe.dropna(
        subset=[
            TARGET_COLUMN,
            "query_id",
        ]
    ).reset_index(
        drop=True
    )

    print()
    print(
        "DBOptima V2 Training"
    )

    print(
        f"Rows: "
        f"{len(dataframe)}"
    )

    print(
        f"Query groups: "
        f"{dataframe['query_id'].nunique()}"
    )

    print()

    print(
        "Decision distribution:"
    )

    statuses = dataframe[
        TARGET_COLUMN
    ].apply(
        improvement_to_status
    )

    print(
        statuses.value_counts()
    )

    evaluate_group_kfold(
        dataframe=dataframe
    )

    train_final_model(
        dataframe=dataframe
    )


if __name__ == "__main__":
    main()