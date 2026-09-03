from __future__ import annotations

from typing import Any

from app.ml.ml_predictor import (
    predict_index_improvement,
)
from app.ml.v2_feature_extractor import (
    build_v2_features,
)


# ============================================================
# SAFE HELPERS
# ============================================================


def safe_dict(
    value: Any,
) -> dict[str, Any]:

    if isinstance(
        value,
        dict,
    ):
        return value

    return {}


def safe_float(
    value: Any,
) -> float | None:

    if value is None:
        return None

    try:
        return float(
            value
        )

    except (
        TypeError,
        ValueError,
    ):
        return None


def safe_int(
    value: Any,
) -> int | None:

    if value is None:
        return None

    try:
        return int(
            value
        )

    except (
        TypeError,
        ValueError,
    ):
        return None


# ============================================================
# QUERY STATS
# ============================================================


def extract_query_stats(
    evaluation_context: dict[str, Any],
) -> dict[str, Any]:

    context = safe_dict(
        evaluation_context
    )

    query_stats = safe_dict(
        context.get(
            "query_stats"
        )
    )

    return {
        "total_calls": safe_int(
            query_stats.get(
                "total_calls"
            )
        ),

        "latency_sample_count": safe_int(
            query_stats.get(
                "latency_sample_count"
            )
        ),

        "avg_latency_ms": safe_float(
            query_stats.get(
                "avg_latency_ms"
            )
        ),

        "min_latency_ms": safe_float(
            query_stats.get(
                "min_latency_ms"
            )
        ),

        "max_latency_ms": safe_float(
            query_stats.get(
                "max_latency_ms"
            )
        ),

        "p95_latency_ms": safe_float(
            query_stats.get(
                "p95_latency_ms"
            )
        ),
    }


# ============================================================
# HISTORY
# ============================================================


def extract_history_features(
    evaluation_context: dict[str, Any],
) -> dict[str, Any]:

    context = safe_dict(
        evaluation_context
    )

    history = safe_dict(
        context.get(
            "recommendation_history"
        )
    )

    success_rate = (
        history.get(
            "success_rate"
        )
    )

    avg_improvement = (
        history.get(
            "avg_improvement"
        )
    )

    if avg_improvement is None:
        avg_improvement = (
            history.get(
                "avg_improvement_percent"
            )
        )

    return {
        "historical_success_rate": (
            safe_float(
                success_rate
            )
        ),

        "historical_avg_improvement": (
            safe_float(
                avg_improvement
            )
        ),
    }


# ============================================================
# QUERY TEXT
# ============================================================


def extract_query_text(
    evaluation_context: dict[str, Any],
) -> str:

    context = safe_dict(
        evaluation_context
    )

    possible_keys = [
        "query",
        "query_text",
        "sql",
        "normalized_query",
    ]

    for key in possible_keys:

        value = context.get(
            key
        )

        if isinstance(
            value,
            str,
        ) and value.strip():

            return value.strip()

    return ""


# ============================================================
# V2 FEATURE BUILDER
# ============================================================


def build_candidate_features_v2(
    explain_result: dict[str, Any],
    evaluation_context: dict[str, Any],
    recommendation: dict[str, Any],
) -> dict[str, Any]:

    query_stats = (
        extract_query_stats(
            evaluation_context
        )
    )

    history_features = (
        extract_history_features(
            evaluation_context
        )
    )

    query = extract_query_text(
        evaluation_context
    )

    # --------------------------------------------------------
    # Main V2 structural features
    #
    # This uses the same extractor used while generating
    # ml_training_samples_v2.
    # --------------------------------------------------------

    extracted_features = (
        build_v2_features(
            query=query,
            explain_result=explain_result,
            recommendation=recommendation,
        )
    )

    if not isinstance(
        extracted_features,
        dict,
    ):
        raise RuntimeError(
            "build_v2_features() did not "
            "return a dictionary."
        )

    features: dict[str, Any] = {}

    # --------------------------------------------------------
    # Query latency/history features
    # --------------------------------------------------------

    features.update(
        query_stats
    )

    # --------------------------------------------------------
    # Plan/query/candidate structural features
    # --------------------------------------------------------

    features.update(
        extracted_features
    )

    # --------------------------------------------------------
    # Historical recommendation context
    # --------------------------------------------------------

    features.update(
        history_features
    )

    return features


# ============================================================
# MAIN CANDIDATE PREDICTOR
# ============================================================


def predict_candidate(
    explain_result: dict[str, Any],
    evaluation_context: dict[str, Any],
    recommendation: dict[str, Any],
) -> dict[str, Any]:

    features = (
        build_candidate_features_v2(
            explain_result=explain_result,
            evaluation_context=evaluation_context,
            recommendation=recommendation,
        )
    )

    prediction = (
        predict_index_improvement(
            features=features
        )
    )

    prediction[
        "feature_schema"
    ] = "v2"

    return prediction