from __future__ import annotations

import json
from pathlib import Path

import joblib
import pandas as pd

from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline

from app.db.session import SessionLocal
from app.models.ml_training_sample_v2 import MLTrainingSampleV2


# ============================================================
# PATHS
# ============================================================


ML_DIR = Path(__file__).resolve().parent

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
    / "index_improvement_model_v2_final.joblib"
)


METADATA_PATH = (
    ARTIFACT_DIR
    / "index_improvement_model_v2_final_metadata.json"
)


# ============================================================
# FEATURES
#
# IMPORTANT:
# Bunların tamamı benchmark ÖNCESİ elde edilebilir.
#
# Aşağıdakiler feature DEĞİLDİR:
#
# benchmark_before_ms
# benchmark_after_ms
# improvement_percent
# benchmark_stability
# decision_confidence
# decision_status
#
# Çünkü bunlar mevcut candidate'ın gerçek sonucunu içerir.
# ============================================================


FEATURE_COLUMNS = [
    # --------------------------------------------------------
    # Query history / latency
    # --------------------------------------------------------
    "total_calls",
    "latency_sample_count",
    "avg_latency_ms",
    "min_latency_ms",
    "max_latency_ms",
    "p95_latency_ms",

    # --------------------------------------------------------
    # Execution plan
    # --------------------------------------------------------
    "plan_total_cost",
    "plan_rows",
    "seq_scan_count",
    "actual_rows",
    "rows_removed_by_filter",
    "actual_total_time_ms",
    "actual_loops",

    # --------------------------------------------------------
    # Selectivity
    # --------------------------------------------------------
    "scan_selectivity_ratio",
    "removed_to_returned_ratio",

    # --------------------------------------------------------
    # SQL structure
    # --------------------------------------------------------
    "equality_filter_count",
    "range_filter_count",
    "like_filter_count",
    "has_order_by",
    "has_limit",

    # --------------------------------------------------------
    # Candidate index
    # --------------------------------------------------------
    "candidate_column_count",
    "candidate_has_order_column",

    # --------------------------------------------------------
    # Source scan
    # --------------------------------------------------------
    "source_actual_rows",
    "source_rows_removed_by_filter",

    # --------------------------------------------------------
    # Historical recommendation context
    # --------------------------------------------------------
    "historical_success_rate",
    "historical_avg_improvement",
]


TARGET_COLUMN = "improvement_percent"


# ============================================================
# MODEL SETTINGS
# ============================================================


MODEL_VERSION = "v2-final"

RECOMMENDED_THRESHOLD = 20.0
REVIEW_THRESHOLD = 5.0


# ============================================================
# LOAD DATASET
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

            records.append(
                {
                    "id": row.id,
                    "query_id": row.query_id,
                    "recommendation_id": (
                        row.recommendation_id
                    ),

                    "total_calls": (
                        row.total_calls
                    ),

                    "latency_sample_count": (
                        row.latency_sample_count
                    ),

                    "avg_latency_ms": (
                        row.avg_latency_ms
                    ),

                    "min_latency_ms": (
                        row.min_latency_ms
                    ),

                    "max_latency_ms": (
                        row.max_latency_ms
                    ),

                    "p95_latency_ms": (
                        row.p95_latency_ms
                    ),

                    "plan_total_cost": (
                        row.plan_total_cost
                    ),

                    "plan_rows": (
                        row.plan_rows
                    ),

                    "seq_scan_count": (
                        row.seq_scan_count
                    ),

                    "actual_rows": (
                        row.actual_rows
                    ),

                    "rows_removed_by_filter": (
                        row.rows_removed_by_filter
                    ),

                    "actual_total_time_ms": (
                        row.actual_total_time_ms
                    ),

                    "actual_loops": (
                        row.actual_loops
                    ),

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

                    "has_order_by": (
                        row.has_order_by
                    ),

                    "has_limit": (
                        row.has_limit
                    ),

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
# MODEL
# ============================================================


def build_model() -> Pipeline:

    preprocessor = ColumnTransformer(
        transformers=[
            (
                "numeric",
                SimpleImputer(
                    strategy="median",
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


# ============================================================
# TRAIN
# ============================================================


def train_final_model(
    dataframe: pd.DataFrame,
) -> dict:

    x = dataframe[
        FEATURE_COLUMNS
    ]

    y = dataframe[
        TARGET_COLUMN
    ].astype(
        float
    )

    model = build_model()

    print()
    print(
        "Training final V2 model..."
    )

    model.fit(
        x,
        y,
    )

    artifact = {
        "version": MODEL_VERSION,

        "model": model,

        "feature_columns": (
            FEATURE_COLUMNS
        ),

        "target_column": (
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

        "training_samples": (
            len(dataframe)
        ),

        "query_groups": int(
            dataframe[
                "query_id"
            ].nunique()
        ),

        "model_type": (
            "RandomForestRegressor"
        ),

        "model_parameters": {
            "n_estimators": 600,
            "min_samples_leaf": 2,
            "random_state": 42,
        },
    }

    return artifact


# ============================================================
# SAVE
# ============================================================


def save_artifact(
    artifact: dict,
) -> None:

    joblib.dump(
        artifact,
        MODEL_PATH,
    )

    metadata = {
        "version": (
            artifact["version"]
        ),

        "feature_columns": (
            artifact[
                "feature_columns"
            ]
        ),

        "target_column": (
            artifact[
                "target_column"
            ]
        ),

        "thresholds": (
            artifact[
                "thresholds"
            ]
        ),

        "training_samples": (
            artifact[
                "training_samples"
            ]
        ),

        "query_groups": (
            artifact[
                "query_groups"
            ]
        ),

        "model_type": (
            artifact[
                "model_type"
            ]
        ),

        "model_parameters": (
            artifact[
                "model_parameters"
            ]
        ),

        "evaluation_reference": {
            "paired_samples": 340,
            "paired_query_groups": 51,

            "overall_mae": 10.5133,
            "overall_rmse": 16.9843,
            "overall_r2": 0.8431,
            "overall_status_accuracy": 78.82,

            "cold_start_samples": 51,
            "cold_start_mae": 16.1311,
            "cold_start_rmse": 22.5148,
            "cold_start_r2": 0.7425,
            "cold_start_status_accuracy": 70.59,
        },
    }

    with METADATA_PATH.open(
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            metadata,
            file,
            indent=2,
            ensure_ascii=False,
        )


# ============================================================
# VALIDATION
# ============================================================


def validate_dataset(
    dataframe: pd.DataFrame,
) -> pd.DataFrame:

    if dataframe.empty:
        raise RuntimeError(
            "ml_training_samples_v2 "
            "table is empty."
        )

    required_columns = (
        FEATURE_COLUMNS
        + [
            TARGET_COLUMN,
            "query_id",
        ]
    )

    missing_columns = [
        column
        for column in required_columns
        if column
        not in dataframe.columns
    ]

    if missing_columns:

        raise RuntimeError(
            "Missing dataset columns: "
            + ", ".join(
                missing_columns
            )
        )

    dataframe = (
        dataframe.dropna(
            subset=[
                TARGET_COLUMN,
                "query_id",
            ]
        )
        .reset_index(
            drop=True
        )
    )

    if len(dataframe) < 50:

        raise RuntimeError(
            "Dataset is too small "
            "for final V2 training."
        )

    unique_groups = int(
        dataframe[
            "query_id"
        ].nunique()
    )

    if unique_groups < 10:

        raise RuntimeError(
            "Not enough unique "
            "query groups."
        )

    return dataframe


# ============================================================
# PRINT DATASET INFO
# ============================================================


def print_dataset_info(
    dataframe: pd.DataFrame,
) -> None:

    print()
    print(
        "=" * 80
    )

    print(
        "DBOptima Final V2 Model Training"
    )

    print(
        "=" * 80
    )

    print(
        f"Training samples: "
        f"{len(dataframe)}"
    )

    print(
        f"Query groups:     "
        f"{dataframe['query_id'].nunique()}"
    )

    print(
        f"Features:         "
        f"{len(FEATURE_COLUMNS)}"
    )

    print()

    print(
        "Target distribution:"
    )

    recommended = int(
        (
            dataframe[
                TARGET_COLUMN
            ]
            >= RECOMMENDED_THRESHOLD
        ).sum()
    )

    review = int(
        (
            (
                dataframe[
                    TARGET_COLUMN
                ]
                >= REVIEW_THRESHOLD
            )
            &
            (
                dataframe[
                    TARGET_COLUMN
                ]
                < RECOMMENDED_THRESHOLD
            )
        ).sum()
    )

    rejected = int(
        (
            dataframe[
                TARGET_COLUMN
            ]
            < REVIEW_THRESHOLD
        ).sum()
    )

    print(
        f"RECOMMENDED: "
        f"{recommended}"
    )

    print(
        f"REVIEW:      "
        f"{review}"
    )

    print(
        f"REJECTED:    "
        f"{rejected}"
    )

    print(
        "=" * 80
    )


# ============================================================
# VERIFY ARTIFACT
# ============================================================


def verify_saved_artifact() -> None:

    if not MODEL_PATH.exists():
        raise RuntimeError(
            "Saved model artifact "
            "could not be found."
        )

    artifact = joblib.load(
        MODEL_PATH
    )

    if not isinstance(
        artifact,
        dict,
    ):
        raise RuntimeError(
            "Invalid saved artifact."
        )

    required_keys = [
        "version",
        "model",
        "feature_columns",
        "thresholds",
    ]

    missing_keys = [
        key
        for key in required_keys
        if key not in artifact
    ]

    if missing_keys:

        raise RuntimeError(
            "Saved artifact is missing keys: "
            + ", ".join(
                missing_keys
            )
        )

    model = artifact[
        "model"
    ]

    feature_columns = artifact[
        "feature_columns"
    ]

    test_row = {
        column: None
        for column in feature_columns
    }

    test_dataframe = pd.DataFrame(
        [
            test_row
        ],
        columns=feature_columns,
    )

    prediction = model.predict(
        test_dataframe
    )

    if len(prediction) != 1:
        raise RuntimeError(
            "Artifact prediction "
            "verification failed."
        )

    print()
    print(
        "Artifact verification passed."
    )

    print(
        f"Verification prediction: "
        f"{float(prediction[0]):.2f}%"
    )


# ============================================================
# MAIN
# ============================================================


def main() -> None:

    dataframe = load_dataset()

    dataframe = validate_dataset(
        dataframe
    )

    print_dataset_info(
        dataframe
    )

    artifact = train_final_model(
        dataframe
    )

    save_artifact(
        artifact
    )

    verify_saved_artifact()

    print()
    print(
        "=" * 80
    )

    print(
        "FINAL V2 MODEL READY"
    )

    print(
        "=" * 80
    )

    print(
        f"Model:"
    )

    print(
        MODEL_PATH
    )

    print()

    print(
        f"Metadata:"
    )

    print(
        METADATA_PATH
    )

    print()

    print(
        f"Version: "
        f"{MODEL_VERSION}"
    )

    print(
        f"Training samples: "
        f"{artifact['training_samples']}"
    )

    print(
        f"Query groups: "
        f"{artifact['query_groups']}"
    )

    print(
        f"Feature count: "
        f"{len(FEATURE_COLUMNS)}"
    )

    print(
        "=" * 80
    )


if __name__ == "__main__":
    main()