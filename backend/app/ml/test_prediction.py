from __future__ import annotations

from app.ml.ml_predictor import (
    predict_index_improvement,
)


def main() -> None:
    features = {
        "total_calls": 25,
        "latency_sample_count": 20,
        "avg_latency_ms": 28.5,
        "min_latency_ms": 22.0,
        "max_latency_ms": 41.0,
        "p95_latency_ms": 38.0,
        "plan_total_cost": 1850.0,
        "plan_rows": 50000.0,
        "filter_column_count": 2,
        "index_column_count": 3,
        "historical_success_rate": 75.0,
        "historical_avg_improvement": 48.0,
    }

    result = predict_index_improvement(
        features
    )

    print("=" * 72)
    print("DBOPTIMA ML PREDICTION TEST")
    print("=" * 72)

    print(
        "Predicted improvement:",
        result["predicted_improvement_percent"],
        "%",
    )

    print(
        "Predicted status:",
        result["predicted_status"],
    )

    print(
        "Benchmark priority:",
        result["benchmark_priority"],
    )

    print("=" * 72)


if __name__ == "__main__":
    main()