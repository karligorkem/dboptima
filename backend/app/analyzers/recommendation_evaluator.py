from typing import Any


RECOMMENDED_THRESHOLD = 20.0
REVIEW_THRESHOLD = 5.0


def calculate_variability_score(
    values: list[float],
) -> float:
    if not values:
        return 1.0

    mean_value = (
        sum(values)
        / len(values)
    )

    if mean_value <= 0:
        return 1.0

    variance = (
        sum(
            (
                value
                - mean_value
            ) ** 2
            for value in values
        )
        / len(values)
    )

    std_dev = (
        variance ** 0.5
    )

    coefficient_of_variation = (
        std_dev
        / mean_value
    )

    stability_score = (
        1.0
        - coefficient_of_variation
    )

    return max(
        0.0,
        min(
            stability_score,
            1.0,
        ),
    )


def calculate_benchmark_stability(
    benchmark: dict[str, Any],
) -> float:
    before = benchmark.get(
        "before",
        {},
    )

    after = benchmark.get(
        "after",
        {},
    )

    before_runs = before.get(
        "runs_ms",
        [],
    )

    after_runs = after.get(
        "runs_ms",
        [],
    )

    before_stability = (
        calculate_variability_score(
            before_runs
        )
    )

    after_stability = (
        calculate_variability_score(
            after_runs
        )
    )

    return (
        before_stability
        + after_stability
    ) / 2


def calculate_sample_confidence(
    sample_count: int,
) -> float:
    if sample_count <= 0:
        return 0.0

    return min(
        sample_count / 20.0,
        1.0,
    )


def calculate_history_confidence(
    history: dict[str, Any] | None,
) -> float:
    if not history:
        return 0.0

    total_runs = int(
        history.get(
            "total_runs",
            0,
        )
        or 0
    )

    success_rate = (
        history.get(
            "success_rate"
        )
    )

    avg_confidence = (
        history.get(
            "avg_confidence"
        )
    )

    if total_runs <= 0:
        return 0.0

    if success_rate is None:
        success_score = 0.0
    else:
        success_score = max(
            0.0,
            min(
                float(
                    success_rate
                )
                / 100.0,
                1.0,
            ),
        )

    if avg_confidence is None:
        historical_confidence_score = (
            0.0
        )
    else:
        historical_confidence_score = max(
            0.0,
            min(
                float(
                    avg_confidence
                ),
                1.0,
            ),
        )

    run_count_score = min(
        total_runs / 10.0,
        1.0,
    )

    history_score = (
        0.45
        * success_score
        + 0.35
        * historical_confidence_score
        + 0.20
        * run_count_score
    )

    return max(
        0.0,
        min(
            history_score,
            1.0,
        ),
    )


def evaluate_benchmark(
    benchmark: dict[str, Any],
    recommendation_history: (
        dict[str, Any] | None
    ) = None,
    latency_sample_count: int = 0,
) -> dict[str, Any]:
    improvement_percent = float(
        benchmark.get(
            "improvement_percent",
            0.0,
        )
    )

    before_ms = float(
        benchmark.get(
            "before_ms",
            0.0,
        )
    )

    after_ms = float(
        benchmark.get(
            "after_ms",
            0.0,
        )
    )

    stability = (
        calculate_benchmark_stability(
            benchmark
        )
    )

    if (
        improvement_percent
        >= RECOMMENDED_THRESHOLD
    ):
        status = (
            "RECOMMENDED"
        )

        improvement_confidence = min(
            improvement_percent
            / 100.0,
            1.0,
        )

    elif (
        improvement_percent
        >= REVIEW_THRESHOLD
    ):
        status = (
            "REVIEW"
        )

        improvement_confidence = min(
            improvement_percent
            / RECOMMENDED_THRESHOLD,
            1.0,
        )

    else:
        status = (
            "REJECTED"
        )

        improvement_confidence = (
            0.0
        )

    history_confidence = (
        calculate_history_confidence(
            recommendation_history
        )
    )

    sample_confidence = (
        calculate_sample_confidence(
            latency_sample_count
        )
    )

    base_confidence = (
        improvement_confidence
        * stability
    )

    if recommendation_history:
        final_confidence = (
            0.65
            * base_confidence
            + 0.25
            * history_confidence
            + 0.10
            * sample_confidence
        )
    else:
        final_confidence = (
            0.90
            * base_confidence
            + 0.10
            * sample_confidence
        )

    confidence = round(
        max(
            0.0,
            min(
                final_confidence,
                1.0,
            ),
        ),
        4,
    )

    reason = (
        f"Benchmark showed "
        f"{improvement_percent:.2f}% "
        f"execution time improvement "
        f"({before_ms:.3f} ms -> "
        f"{after_ms:.3f} ms). "
        f"Benchmark stability: "
        f"{stability:.2%}. "
        f"Historical confidence: "
        f"{history_confidence:.2%}. "
        f"Latency sample confidence: "
        f"{sample_confidence:.2%}."
    )

    return {
        "status": (
            status
        ),
        "confidence": (
            confidence
        ),
        "reason": (
            reason
        ),
        "benchmark_stability": (
            round(
                stability,
                4,
            )
        ),
        "history_confidence": (
            round(
                history_confidence,
                4,
            )
        ),
        "sample_confidence": (
            round(
                sample_confidence,
                4,
            )
        ),
        "confidence_components": {
            "improvement_confidence": (
                round(
                    improvement_confidence,
                    4,
                )
            ),
            "benchmark_stability": (
                round(
                    stability,
                    4,
                )
            ),
            "history_confidence": (
                round(
                    history_confidence,
                    4,
                )
            ),
            "sample_confidence": (
                round(
                    sample_confidence,
                    4,
                )
            ),
        },
        "thresholds": {
            "recommended_percent": (
                RECOMMENDED_THRESHOLD
            ),
            "review_percent": (
                REVIEW_THRESHOLD
            ),
        },
    }