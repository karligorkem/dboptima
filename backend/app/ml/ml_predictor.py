from __future__ import annotations

from pathlib import Path
from typing import Any

import joblib
import pandas as pd


# ============================================================
# PATHS
# ============================================================

ML_DIR = Path(__file__).resolve().parent

MODEL_PATH = (
    ML_DIR
    / "artifacts"
    / "index_improvement_model_v2_final.joblib"
)


# ============================================================
# EXCEPTIONS
# ============================================================


class MLModelNotFoundError(RuntimeError):
    pass


class MLPredictionError(RuntimeError):
    pass


# ============================================================
# MODEL LOADING
# ============================================================


def load_model_artifact() -> dict[str, Any]:

    if not MODEL_PATH.exists():
        raise MLModelNotFoundError(
            f"ML model not found: {MODEL_PATH}"
        )

    try:
        artifact = joblib.load(
            MODEL_PATH
        )

    except Exception as exc:
        raise MLPredictionError(
            f"Failed to load ML model: {MODEL_PATH}"
        ) from exc

    if not isinstance(
        artifact,
        dict,
    ):
        raise MLPredictionError(
            "Invalid ML artifact format. "
            "Expected dictionary."
        )

    required_keys = [
        "model",
        "feature_columns",
    ]

    missing_keys = [
        key
        for key in required_keys
        if key not in artifact
    ]

    if missing_keys:
        raise MLPredictionError(
            "ML artifact is missing keys: "
            + ", ".join(
                missing_keys
            )
        )

    return artifact


# ============================================================
# STATUS
# ============================================================


def prediction_to_status(
    predicted_improvement: float,
    recommended_threshold: float,
    review_threshold: float,
) -> str:

    if (
        predicted_improvement
        >= recommended_threshold
    ):
        return "RECOMMENDED"

    if (
        predicted_improvement
        >= review_threshold
    ):
        return "REVIEW"

    return "REJECTED"


# ============================================================
# BENCHMARK PRIORITY
# ============================================================


def prediction_to_priority(
    predicted_improvement: float,
) -> str:

    if predicted_improvement >= 50.0:
        return "HIGH"

    if predicted_improvement >= 20.0:
        return "MEDIUM"

    if predicted_improvement >= 5.0:
        return "LOW"

    return "VERY_LOW"


# ============================================================
# FEATURE FRAME
# ============================================================


def build_prediction_dataframe(
    features: dict[str, Any],
    feature_columns: list[str],
) -> pd.DataFrame:

    row = {
        feature_name: features.get(
            feature_name
        )
        for feature_name
        in feature_columns
    }

    dataframe = pd.DataFrame(
        [row],
        columns=feature_columns,
    )

    return dataframe


# ============================================================
# PREDICT
# ============================================================


def predict_index_improvement(
    features: dict[str, Any],
) -> dict[str, Any]:

    artifact = load_model_artifact()

    model = artifact[
        "model"
    ]

    feature_columns = artifact[
        "feature_columns"
    ]

    thresholds = artifact.get(
        "thresholds",
        {},
    )

    recommended_threshold = float(
        thresholds.get(
            "recommended",
            20.0,
        )
    )

    review_threshold = float(
        thresholds.get(
            "review",
            5.0,
        )
    )

    model_version = str(
        artifact.get(
            "version",
            "unknown",
        )
    )

    dataframe = (
        build_prediction_dataframe(
            features=features,
            feature_columns=feature_columns,
        )
    )

    try:

        prediction = model.predict(
            dataframe
        )

    except Exception as exc:

        raise MLPredictionError(
            "ML prediction failed."
        ) from exc

    if len(prediction) != 1:
        raise MLPredictionError(
            "Unexpected ML prediction size."
        )

    predicted_improvement = float(
        prediction[0]
    )

    predicted_status = (
        prediction_to_status(
            predicted_improvement=(
                predicted_improvement
            ),
            recommended_threshold=(
                recommended_threshold
            ),
            review_threshold=(
                review_threshold
            ),
        )
    )

    benchmark_priority = (
        prediction_to_priority(
            predicted_improvement
        )
    )

    return {
        "model_version": (
            model_version
        ),

        "predicted_improvement_percent": round(
            predicted_improvement,
            2,
        ),

        "predicted_status": (
            predicted_status
        ),

        "benchmark_priority": (
            benchmark_priority
        ),

        "recommended_threshold": (
            recommended_threshold
        ),

        "review_threshold": (
            review_threshold
        ),

        "feature_count": len(
            feature_columns
        ),

        "model_path": str(
            MODEL_PATH
        ),
    }