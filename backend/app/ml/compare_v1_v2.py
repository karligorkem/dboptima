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
from app.models.ml_training_sample import MLTrainingSample
from app.models.ml_training_sample_v2 import MLTrainingSampleV2


# ============================================================
# V1 FEATURE SET
# ============================================================

V1_FEATURE_COLUMNS = [
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


# ============================================================
# V2 FEATURE SET
# ============================================================

V2_FEATURE_COLUMNS = [
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


# ============================================================
# STATUS HELPERS
# ============================================================


def improvement_to_status(
    value: float,
) -> str:

    if value >= 20.0:
        return "RECOMMENDED"

    if value >= 5.0:
        return "REVIEW"

    return "REJECTED"


def calculate_status_accuracy(
    actual: np.ndarray,
    predicted: np.ndarray,
) -> float:

    actual_statuses = [
        improvement_to_status(
            float(value)
        )
        for value in actual
    ]

    predicted_statuses = [
        improvement_to_status(
            float(value)
        )
        for value in predicted
    ]

    correct = sum(
        actual_status == predicted_status
        for actual_status, predicted_status
        in zip(
            actual_statuses,
            predicted_statuses,
        )
    )

    return (
        correct
        / len(actual_statuses)
        * 100.0
    )


# ============================================================
# MODEL
# ============================================================


def build_model(
    feature_columns: list[str],
) -> Pipeline:

    preprocessor = ColumnTransformer(
        transformers=[
            (
                "numeric",
                SimpleImputer(
                    strategy="median",
                ),
                feature_columns,
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


# ============================================================
# LOAD V1 DATA
# ============================================================


def load_v1_dataset() -> pd.DataFrame:

    db = SessionLocal()

    try:

        rows = (
            db.query(
                MLTrainingSample
            )
            .order_by(
                MLTrainingSample.id.asc()
            )
            .all()
        )

        records: list[dict] = []

        for row in rows:

            records.append(
                {
                    "v1_id": row.id,
                    "recommendation_id": row.recommendation_id,
                    "query_id": row.query_id,

                    "total_calls": row.total_calls,
                    "latency_sample_count": row.latency_sample_count,

                    "avg_latency_ms": row.avg_latency_ms,
                    "min_latency_ms": row.min_latency_ms,
                    "max_latency_ms": row.max_latency_ms,
                    "p95_latency_ms": row.p95_latency_ms,

                    "plan_total_cost": row.plan_total_cost,
                    "plan_rows": row.plan_rows,

                    "filter_column_count": row.filter_column_count,
                    "index_column_count": row.index_column_count,

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


# ============================================================
# LOAD V2 DATA
# ============================================================


def load_v2_dataset() -> pd.DataFrame:

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

            records.append(
                {
                    "v2_id": row.id,
                    "recommendation_id": row.recommendation_id,
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


# ============================================================
# BUILD PAIRED DATASET
# ============================================================


def build_paired_dataset() -> pd.DataFrame:

    v1 = load_v1_dataset()
    v2 = load_v2_dataset()

    print()
    print(
        f"Raw V1 samples: {len(v1)}"
    )

    print(
        f"Raw V2 samples: {len(v2)}"
    )

    if v1.empty:
        raise RuntimeError(
            "V1 training table is empty."
        )

    if v2.empty:
        raise RuntimeError(
            "V2 training table is empty."
        )

    paired = v1.merge(
        v2,
        on="recommendation_id",
        how="inner",
        suffixes=(
            "_v1",
            "_v2",
        ),
    )

    if paired.empty:
        raise RuntimeError(
            "No matching recommendation_id "
            "between V1 and V2 datasets."
        )

    # --------------------------------------------------------
    # Query ID safety check
    # --------------------------------------------------------

    query_mismatch_mask = (
        paired["query_id_v1"]
        != paired["query_id_v2"]
    )

    query_mismatch_count = int(
        query_mismatch_mask.sum()
    )

    if query_mismatch_count > 0:

        print()
        print(
            "WARNING:"
        )

        print(
            f"{query_mismatch_count} paired rows "
            f"have different query_id values."
        )

        print(
            "These rows will be excluded."
        )

        paired = paired[
            ~query_mismatch_mask
        ].copy()

    # --------------------------------------------------------
    # Target safety check
    # --------------------------------------------------------

    target_difference = (
        paired[
            "improvement_percent_v1"
        ]
        -
        paired[
            "improvement_percent_v2"
        ]
    ).abs()

    target_mismatch_mask = (
        target_difference > 0.01
    )

    target_mismatch_count = int(
        target_mismatch_mask.sum()
    )

    if target_mismatch_count > 0:

        print()
        print(
            "WARNING:"
        )

        print(
            f"{target_mismatch_count} paired rows "
            f"have different improvement targets."
        )

        print(
            "These rows will be excluded."
        )

        paired = paired[
            ~target_mismatch_mask
        ].copy()

    paired = paired.reset_index(
        drop=True
    )

    if paired.empty:
        raise RuntimeError(
            "No valid paired rows remain "
            "after consistency checks."
        )

    return paired


# ============================================================
# MERGED COLUMN RESOLUTION
# ============================================================


def resolve_merged_column(
    paired: pd.DataFrame,
    feature: str,
    suffix: str,
) -> str:
    """
    Pandas merge only appends suffixes to columns
    that exist in BOTH source dataframes.

    Example shared feature:
        total_calls
        ->
        total_calls_v1
        total_calls_v2

    Example V1-only feature:
        filter_column_count
        ->
        filter_column_count

    Example V2-only feature:
        seq_scan_count
        ->
        seq_scan_count
    """

    suffixed_column = (
        f"{feature}_{suffix}"
    )

    if suffixed_column in paired.columns:
        return suffixed_column

    if feature in paired.columns:
        return feature

    available_candidates = [
        column
        for column in paired.columns
        if feature.lower()
        in column.lower()
    ]

    raise KeyError(
        "Feature column could not be resolved. "
        f"feature={feature}, "
        f"suffix={suffix}, "
        f"possible_columns={available_candidates}"
    )


# ============================================================
# BUILD CLEAN V1 FRAME
# ============================================================


def build_v1_frame(
    paired: pd.DataFrame,
) -> pd.DataFrame:

    dataframe = pd.DataFrame(
        index=paired.index
    )

    dataframe["query_id"] = (
        paired["query_id_v1"]
    )

    dataframe[
        TARGET_COLUMN
    ] = (
        paired[
            "improvement_percent_v1"
        ]
    )

    for feature in V1_FEATURE_COLUMNS:

        source_column = (
            resolve_merged_column(
                paired=paired,
                feature=feature,
                suffix="v1",
            )
        )

        dataframe[
            feature
        ] = paired[
            source_column
        ]

    return dataframe.reset_index(
        drop=True
    )


# ============================================================
# BUILD CLEAN V2 FRAME
# ============================================================


def build_v2_frame(
    paired: pd.DataFrame,
) -> pd.DataFrame:

    dataframe = pd.DataFrame(
        index=paired.index
    )

    dataframe["query_id"] = (
        paired["query_id_v2"]
    )

    dataframe[
        TARGET_COLUMN
    ] = (
        paired[
            "improvement_percent_v2"
        ]
    )

    for feature in V2_FEATURE_COLUMNS:

        source_column = (
            resolve_merged_column(
                paired=paired,
                feature=feature,
                suffix="v2",
            )
        )

        dataframe[
            feature
        ] = paired[
            source_column
        ]

    return dataframe.reset_index(
        drop=True
    )


# ============================================================
# METRICS
# ============================================================


def calculate_metrics(
    actual: np.ndarray,
    predicted: np.ndarray,
) -> dict:

    mae = mean_absolute_error(
        actual,
        predicted,
    )

    rmse = math.sqrt(
        mean_squared_error(
            actual,
            predicted,
        )
    )

    if len(actual) >= 2:

        r2 = r2_score(
            actual,
            predicted,
        )

    else:

        r2 = float(
            "nan"
        )

    accuracy = (
        calculate_status_accuracy(
            actual=actual,
            predicted=predicted,
        )
    )

    return {
        "mae": float(mae),
        "rmse": float(rmse),
        "r2": float(r2),
        "status_accuracy": float(
            accuracy
        ),
    }


# ============================================================
# SAME-FOLD OVERALL EVALUATION
# ============================================================


def evaluate_same_folds(
    v1_dataframe: pd.DataFrame,
    v2_dataframe: pd.DataFrame,
) -> tuple[dict, dict]:

    groups = (
        v1_dataframe[
            "query_id"
        ]
    )

    unique_groups = groups.nunique()

    n_splits = min(
        5,
        unique_groups,
    )

    if n_splits < 2:
        raise RuntimeError(
            "Not enough query groups "
            "for GroupKFold."
        )

    splitter = GroupKFold(
        n_splits=n_splits
    )

    dummy_x = np.zeros(
        (
            len(v1_dataframe),
            1,
        )
    )

    dummy_y = (
        v1_dataframe[
            TARGET_COLUMN
        ]
        .astype(float)
        .to_numpy()
    )

    v1_all_actual: list[float] = []
    v1_all_predicted: list[float] = []

    v2_all_actual: list[float] = []
    v2_all_predicted: list[float] = []

    print()
    print(
        "=" * 90
    )

    print(
        "V1 VS V2 - SAME GROUPKFOLD SPLITS"
    )

    print(
        "=" * 90
    )

    print(
        f"Paired samples:  "
        f"{len(v1_dataframe)}"
    )

    print(
        f"Query groups:    "
        f"{unique_groups}"
    )

    print(
        f"Folds:           "
        f"{n_splits}"
    )

    print(
        f"V1 features:     "
        f"{len(V1_FEATURE_COLUMNS)}"
    )

    print(
        f"V2 features:     "
        f"{len(V2_FEATURE_COLUMNS)}"
    )

    print(
        "=" * 90
    )

    for fold_number, (
        train_index,
        test_index,
    ) in enumerate(
        splitter.split(
            dummy_x,
            dummy_y,
            groups=groups,
        ),
        start=1,
    ):

        # ====================================================
        # V1 TRAIN
        # ====================================================

        v1_model = build_model(
            V1_FEATURE_COLUMNS
        )

        v1_x_train = (
            v1_dataframe.iloc[
                train_index
            ][
                V1_FEATURE_COLUMNS
            ]
        )

        v1_y_train = (
            v1_dataframe.iloc[
                train_index
            ][
                TARGET_COLUMN
            ].astype(float)
        )

        v1_x_test = (
            v1_dataframe.iloc[
                test_index
            ][
                V1_FEATURE_COLUMNS
            ]
        )

        v1_y_test = (
            v1_dataframe.iloc[
                test_index
            ][
                TARGET_COLUMN
            ]
            .astype(float)
            .to_numpy()
        )

        v1_model.fit(
            v1_x_train,
            v1_y_train,
        )

        v1_predictions = (
            v1_model.predict(
                v1_x_test
            )
        )

        # ====================================================
        # V2 TRAIN
        # ====================================================

        v2_model = build_model(
            V2_FEATURE_COLUMNS
        )

        v2_x_train = (
            v2_dataframe.iloc[
                train_index
            ][
                V2_FEATURE_COLUMNS
            ]
        )

        v2_y_train = (
            v2_dataframe.iloc[
                train_index
            ][
                TARGET_COLUMN
            ].astype(float)
        )

        v2_x_test = (
            v2_dataframe.iloc[
                test_index
            ][
                V2_FEATURE_COLUMNS
            ]
        )

        v2_y_test = (
            v2_dataframe.iloc[
                test_index
            ][
                TARGET_COLUMN
            ]
            .astype(float)
            .to_numpy()
        )

        v2_model.fit(
            v2_x_train,
            v2_y_train,
        )

        v2_predictions = (
            v2_model.predict(
                v2_x_test
            )
        )

        # ====================================================
        # SAFETY
        # ====================================================

        if not np.allclose(
            v1_y_test,
            v2_y_test,
            atol=0.01,
            rtol=0.0,
        ):
            raise RuntimeError(
                f"Fold {fold_number}: "
                "V1 and V2 test targets "
                "do not match."
            )

        # ====================================================
        # METRICS
        # ====================================================

        v1_metrics = (
            calculate_metrics(
                actual=v1_y_test,
                predicted=v1_predictions,
            )
        )

        v2_metrics = (
            calculate_metrics(
                actual=v2_y_test,
                predicted=v2_predictions,
            )
        )

        v1_all_actual.extend(
            v1_y_test.tolist()
        )

        v1_all_predicted.extend(
            v1_predictions.tolist()
        )

        v2_all_actual.extend(
            v2_y_test.tolist()
        )

        v2_all_predicted.extend(
            v2_predictions.tolist()
        )

        print()
        print(
            f"Fold {fold_number}"
        )

        print(
            f"Train samples: "
            f"{len(train_index)}"
        )

        print(
            f"Test samples:  "
            f"{len(test_index)}"
        )

        print()

        print(
            "V1"
        )

        print(
            f"  MAE:              "
            f"{v1_metrics['mae']:.4f}"
        )

        print(
            f"  RMSE:             "
            f"{v1_metrics['rmse']:.4f}"
        )

        print(
            f"  R2:               "
            f"{v1_metrics['r2']:.4f}"
        )

        print(
            f"  Status accuracy:  "
            f"{v1_metrics['status_accuracy']:.2f}%"
        )

        print()

        print(
            "V2"
        )

        print(
            f"  MAE:              "
            f"{v2_metrics['mae']:.4f}"
        )

        print(
            f"  RMSE:             "
            f"{v2_metrics['rmse']:.4f}"
        )

        print(
            f"  R2:               "
            f"{v2_metrics['r2']:.4f}"
        )

        print(
            f"  Status accuracy:  "
            f"{v2_metrics['status_accuracy']:.2f}%"
        )

    v1_overall = (
        calculate_metrics(
            actual=np.array(
                v1_all_actual,
                dtype=float,
            ),
            predicted=np.array(
                v1_all_predicted,
                dtype=float,
            ),
        )
    )

    v2_overall = (
        calculate_metrics(
            actual=np.array(
                v2_all_actual,
                dtype=float,
            ),
            predicted=np.array(
                v2_all_predicted,
                dtype=float,
            ),
        )
    )

    return (
        v1_overall,
        v2_overall,
    )


# ============================================================
# SAME-FOLD COLD START
# ============================================================


def evaluate_cold_start_same_folds(
    v1_dataframe: pd.DataFrame,
    v2_dataframe: pd.DataFrame,
) -> tuple[dict, dict, int]:

    groups = (
        v1_dataframe[
            "query_id"
        ]
    )

    unique_groups = groups.nunique()

    n_splits = min(
        5,
        unique_groups,
    )

    splitter = GroupKFold(
        n_splits=n_splits
    )

    dummy_x = np.zeros(
        (
            len(v1_dataframe),
            1,
        )
    )

    dummy_y = (
        v1_dataframe[
            TARGET_COLUMN
        ]
        .astype(float)
        .to_numpy()
    )

    v1_actual_all: list[float] = []
    v1_predicted_all: list[float] = []

    v2_actual_all: list[float] = []
    v2_predicted_all: list[float] = []

    print()
    print(
        "=" * 90
    )

    print(
        "COLD-START SAME-FOLD EVALUATION"
    )

    print(
        "=" * 90
    )

    for fold_number, (
        train_index,
        test_index,
    ) in enumerate(
        splitter.split(
            dummy_x,
            dummy_y,
            groups=groups,
        ),
        start=1,
    ):

        # ====================================================
        # TRAIN V1
        # ====================================================

        v1_model = build_model(
            V1_FEATURE_COLUMNS
        )

        v1_model.fit(
            v1_dataframe.iloc[
                train_index
            ][
                V1_FEATURE_COLUMNS
            ],
            v1_dataframe.iloc[
                train_index
            ][
                TARGET_COLUMN
            ].astype(float),
        )

        # ====================================================
        # TRAIN V2
        # ====================================================

        v2_model = build_model(
            V2_FEATURE_COLUMNS
        )

        v2_model.fit(
            v2_dataframe.iloc[
                train_index
            ][
                V2_FEATURE_COLUMNS
            ],
            v2_dataframe.iloc[
                train_index
            ][
                TARGET_COLUMN
            ].astype(float),
        )

        # ====================================================
        # TEST FRAME
        # ====================================================

        v1_test = (
            v1_dataframe.iloc[
                test_index
            ]
        )

        v2_test = (
            v2_dataframe.iloc[
                test_index
            ]
        )

        # ====================================================
        # COLD START MASK
        #
        # Her iki history alanı da NULL ise,
        # bu recommendation çalışmadan önce
        # query için geçmiş yok demektir.
        # ====================================================

        cold_mask = (
            v2_test[
                "historical_success_rate"
            ].isna()
            &
            v2_test[
                "historical_avg_improvement"
            ].isna()
        )

        cold_count = int(
            cold_mask.sum()
        )

        if cold_count == 0:

            print(
                f"Fold {fold_number}: "
                "no cold-start samples"
            )

            continue

        cold_positions = np.flatnonzero(
            cold_mask.to_numpy()
        )

        absolute_indices = (
            np.asarray(
                test_index
            )[
                cold_positions
            ]
        )

        v1_cold = (
            v1_dataframe.iloc[
                absolute_indices
            ]
        )

        v2_cold = (
            v2_dataframe.iloc[
                absolute_indices
            ]
        )

        # ====================================================
        # PREDICT
        # ====================================================

        v1_predictions = (
            v1_model.predict(
                v1_cold[
                    V1_FEATURE_COLUMNS
                ]
            )
        )

        v2_predictions = (
            v2_model.predict(
                v2_cold[
                    V2_FEATURE_COLUMNS
                ]
            )
        )

        actual_v1 = (
            v1_cold[
                TARGET_COLUMN
            ]
            .astype(float)
            .to_numpy()
        )

        actual_v2 = (
            v2_cold[
                TARGET_COLUMN
            ]
            .astype(float)
            .to_numpy()
        )

        if not np.allclose(
            actual_v1,
            actual_v2,
            atol=0.01,
            rtol=0.0,
        ):
            raise RuntimeError(
                f"Fold {fold_number}: "
                "V1/V2 cold-start targets "
                "do not match."
            )

        v1_metrics = (
            calculate_metrics(
                actual=actual_v1,
                predicted=v1_predictions,
            )
        )

        v2_metrics = (
            calculate_metrics(
                actual=actual_v2,
                predicted=v2_predictions,
            )
        )

        print()
        print(
            f"Fold {fold_number}"
        )

        print(
            f"Cold-start samples: "
            f"{cold_count}"
        )

        print(
            f"V1 MAE: "
            f"{v1_metrics['mae']:.4f}"
        )

        print(
            f"V2 MAE: "
            f"{v2_metrics['mae']:.4f}"
        )

        print(
            f"V1 status accuracy: "
            f"{v1_metrics['status_accuracy']:.2f}%"
        )

        print(
            f"V2 status accuracy: "
            f"{v2_metrics['status_accuracy']:.2f}%"
        )

        v1_actual_all.extend(
            actual_v1.tolist()
        )

        v1_predicted_all.extend(
            v1_predictions.tolist()
        )

        v2_actual_all.extend(
            actual_v2.tolist()
        )

        v2_predicted_all.extend(
            v2_predictions.tolist()
        )

    if not v1_actual_all:
        raise RuntimeError(
            "No paired cold-start "
            "samples were found."
        )

    v1_metrics = (
        calculate_metrics(
            actual=np.array(
                v1_actual_all,
                dtype=float,
            ),
            predicted=np.array(
                v1_predicted_all,
                dtype=float,
            ),
        )
    )

    v2_metrics = (
        calculate_metrics(
            actual=np.array(
                v2_actual_all,
                dtype=float,
            ),
            predicted=np.array(
                v2_predicted_all,
                dtype=float,
            ),
        )
    )

    return (
        v1_metrics,
        v2_metrics,
        len(v1_actual_all),
    )


# ============================================================
# COMPARISON OUTPUT
# ============================================================


def safe_percent_improvement(
    old_value: float,
    new_value: float,
) -> float:

    if old_value == 0:
        return 0.0

    return (
        (
            old_value
            - new_value
        )
        / old_value
        * 100.0
    )


def print_comparison(
    title: str,
    v1_metrics: dict,
    v2_metrics: dict,
) -> None:

    mae_change = (
        safe_percent_improvement(
            v1_metrics["mae"],
            v2_metrics["mae"],
        )
    )

    rmse_change = (
        safe_percent_improvement(
            v1_metrics["rmse"],
            v2_metrics["rmse"],
        )
    )

    accuracy_change = (
        v2_metrics[
            "status_accuracy"
        ]
        -
        v1_metrics[
            "status_accuracy"
        ]
    )

    r2_change = (
        v2_metrics["r2"]
        -
        v1_metrics["r2"]
    )

    print()
    print(
        "=" * 90
    )

    print(
        title
    )

    print(
        "=" * 90
    )

    print(
        f"{'Metric':<24}"
        f"{'V1':>16}"
        f"{'V2':>16}"
        f"{'Change':>20}"
    )

    print(
        "-" * 90
    )

    print(
        f"{'MAE':<24}"
        f"{v1_metrics['mae']:>16.4f}"
        f"{v2_metrics['mae']:>16.4f}"
        f"{mae_change:>19.2f}%"
    )

    print(
        f"{'RMSE':<24}"
        f"{v1_metrics['rmse']:>16.4f}"
        f"{v2_metrics['rmse']:>16.4f}"
        f"{rmse_change:>19.2f}%"
    )

    print(
        f"{'R2':<24}"
        f"{v1_metrics['r2']:>16.4f}"
        f"{v2_metrics['r2']:>16.4f}"
        f"{r2_change:>20.4f}"
    )

    print(
        f"{'Status accuracy':<24}"
        f"{v1_metrics['status_accuracy']:>15.2f}%"
        f"{v2_metrics['status_accuracy']:>15.2f}%"
        f"{accuracy_change:>18.2f} pp"
    )

    print(
        "=" * 90
    )


# ============================================================
# MAIN
# ============================================================


def main() -> None:

    paired = (
        build_paired_dataset()
    )

    print()
    print(
        "=" * 90
    )

    print(
        "PAIRED DATASET"
    )

    print(
        "=" * 90
    )

    print(
        f"Matched samples: "
        f"{len(paired)}"
    )

    print(
        f"Query groups: "
        f"{paired['query_id_v1'].nunique()}"
    )

    print(
        "=" * 90
    )

    # ========================================================
    # BUILD FEATURE FRAMES
    # ========================================================

    v1_dataframe = (
        build_v1_frame(
            paired
        )
    )

    v2_dataframe = (
        build_v2_frame(
            paired
        )
    )

    # ========================================================
    # SAFETY CHECKS
    # ========================================================

    if (
        len(v1_dataframe)
        != len(v2_dataframe)
    ):
        raise RuntimeError(
            "V1 and V2 row counts "
            "do not match."
        )

    if not np.array_equal(
        v1_dataframe[
            "query_id"
        ].to_numpy(),
        v2_dataframe[
            "query_id"
        ].to_numpy(),
    ):
        raise RuntimeError(
            "V1 and V2 query order "
            "does not match."
        )

    if not np.allclose(
        v1_dataframe[
            TARGET_COLUMN
        ].astype(float).to_numpy(),
        v2_dataframe[
            TARGET_COLUMN
        ].astype(float).to_numpy(),
        atol=0.01,
        rtol=0.0,
    ):
        raise RuntimeError(
            "V1 and V2 target values "
            "do not match."
        )

    print()
    print(
        "Dataset safety checks passed."
    )

    # ========================================================
    # OVERALL SAME-FOLD TEST
    # ========================================================

    (
        v1_overall,
        v2_overall,
    ) = evaluate_same_folds(
        v1_dataframe=v1_dataframe,
        v2_dataframe=v2_dataframe,
    )

    print_comparison(
        title=(
            "FINAL SAME-FOLD V1 VS V2"
        ),
        v1_metrics=v1_overall,
        v2_metrics=v2_overall,
    )

    # ========================================================
    # COLD START SAME-FOLD TEST
    # ========================================================

    (
        v1_cold,
        v2_cold,
        cold_count,
    ) = evaluate_cold_start_same_folds(
        v1_dataframe=v1_dataframe,
        v2_dataframe=v2_dataframe,
    )

    print()

    print(
        f"Paired cold-start samples: "
        f"{cold_count}"
    )

    print_comparison(
        title=(
            "COLD-START SAME-FOLD V1 VS V2"
        ),
        v1_metrics=v1_cold,
        v2_metrics=v2_cold,
    )

    # ========================================================
    # FINAL DECISION
    # ========================================================

    overall_v2_wins = (
        v2_overall["mae"]
        < v1_overall["mae"]
    )

    cold_v2_wins = (
        v2_cold["mae"]
        < v1_cold["mae"]
    )

    overall_accuracy_better = (
        v2_overall[
            "status_accuracy"
        ]
        >=
        v1_overall[
            "status_accuracy"
        ]
    )

    cold_accuracy_better = (
        v2_cold[
            "status_accuracy"
        ]
        >=
        v1_cold[
            "status_accuracy"
        ]
    )

    print()
    print(
        "=" * 90
    )

    print(
        "DECISION"
    )

    print(
        "=" * 90
    )

    if (
        overall_v2_wins
        and
        cold_v2_wins
        and
        overall_accuracy_better
        and
        cold_accuracy_better
    ):

        print(
            "V2 CLEAR WINNER"
        )

        print(
            "V2 has lower MAE on both "
            "overall and cold-start evaluation."
        )

        print(
            "V2 status accuracy is also "
            "equal or better."
        )

        print(
            "V2 is eligible to replace V1 "
            "as the candidate-ranking model."
        )

    elif (
        overall_v2_wins
        and
        cold_v2_wins
    ):

        print(
            "V2 WINS ON REGRESSION ERROR"
        )

        print(
            "V2 has lower overall and "
            "cold-start MAE."
        )

        print(
            "However, status classification "
            "accuracy should be reviewed."
        )

    elif cold_v2_wins:

        print(
            "V2 WINS COLD-START ONLY"
        )

        print(
            "V2 generalizes better to unseen "
            "query families, but does not "
            "clearly beat V1 overall."
        )

        print(
            "Do not replace V1 automatically "
            "without reviewing the trade-off."
        )

    else:

        print(
            "V2 DOES NOT CLEARLY BEAT V1"
        )

        print(
            "Keep V1 as the active ranking model "
            "and continue feature engineering."
        )

    print(
        "=" * 90
    )


if __name__ == "__main__":
    main()