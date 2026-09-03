from __future__ import annotations

import json
from statistics import mean
from typing import Any

from fastapi.testclient import TestClient

from app.main import app


DATABASE_ID = 2

RECOMMENDED_THRESHOLD = 20.0
REVIEW_THRESHOLD = 5.0


QUERIES = [
    """
    SELECT *
    FROM orders
    WHERE customer_id = 11111
      AND status = 'SHIPPED'
    ORDER BY created_at DESC
    """,

    """
    SELECT *
    FROM orders
    WHERE customer_id = 22222
      AND status = 'CANCELLED'
    ORDER BY created_at DESC
    """,

    """
    SELECT *
    FROM orders
    WHERE status = 'PAID'
      AND total_amount > 750
    ORDER BY created_at DESC
    """,

    """
    SELECT *
    FROM orders
    WHERE status = 'PENDING'
      AND total_amount > 1200
    ORDER BY total_amount DESC
    """,

    """
    SELECT *
    FROM orders
    WHERE total_amount BETWEEN 250 AND 500
    ORDER BY created_at DESC
    """,

    """
    SELECT *
    FROM orders
    WHERE created_at >= '2025-01-01'
      AND created_at < '2025-02-01'
    ORDER BY created_at DESC
    """,

    """
    SELECT *
    FROM products
    WHERE price > 100
    ORDER BY price DESC
    """,

    """
    SELECT *
    FROM products
    WHERE price BETWEEN 50 AND 150
    ORDER BY price ASC
    """,

    """
    SELECT *
    FROM products
    WHERE stock_quantity < 20
    ORDER BY stock_quantity ASC
    """,

    """
    SELECT *
    FROM customers
    WHERE email LIKE 'a%'
    ORDER BY id DESC
    """,

    """
    SELECT *
    FROM customers
    WHERE created_at >= '2025-01-01'
    ORDER BY created_at DESC
    """,

    """
    SELECT *
    FROM order_items
    WHERE quantity >= 3
    ORDER BY id DESC
    """,

    """
    SELECT *
    FROM order_items
    WHERE product_id = 12345
    ORDER BY id DESC
    """,

    """
    SELECT *
    FROM order_items
    WHERE order_id = 54321
    ORDER BY id DESC
    """,

    """
    SELECT *
    FROM orders
    WHERE customer_id = 33333
      AND total_amount > 500
    ORDER BY total_amount DESC
    """,
]


def normalize_query(query: str) -> str:
    return " ".join(
        query.strip().split()
    )


def improvement_to_status(
    improvement_percent: float,
) -> str:
    if improvement_percent >= RECOMMENDED_THRESHOLD:
        return "RECOMMENDED"

    if improvement_percent >= REVIEW_THRESHOLD:
        return "REVIEW"

    return "REJECTED"


def calculate_mae(
    rows: list[dict[str, Any]],
) -> float | None:
    if not rows:
        return None

    errors = [
        abs(
            row["actual_improvement"]
            - row["predicted_improvement"]
        )
        for row in rows
    ]

    return mean(errors)


def calculate_rmse(
    rows: list[dict[str, Any]],
) -> float | None:
    if not rows:
        return None

    squared_errors = [
        (
            row["actual_improvement"]
            - row["predicted_improvement"]
        )
        ** 2
        for row in rows
    ]

    mse = mean(
        squared_errors
    )

    return mse ** 0.5


def calculate_status_accuracy(
    rows: list[dict[str, Any]],
) -> float | None:
    if not rows:
        return None

    correct = sum(
        1
        for row in rows
        if row["predicted_status"]
        == row["actual_status"]
    )

    return (
        correct
        / len(rows)
        * 100
    )


def print_separator() -> None:
    print(
        "=" * 100
    )


def main() -> None:
    client = TestClient(
        app
    )

    results: list[
        dict[str, Any]
    ] = []

    skipped: list[
        dict[str, Any]
    ] = []

    failed: list[
        dict[str, Any]
    ] = []

    print_separator()

    print(
        "DBOPTIMA COLD-START ML EVALUATION"
    )

    print_separator()

    for index, raw_query in enumerate(
        QUERIES,
        start=1,
    ):
        query = normalize_query(
            raw_query
        )

        print()

        print(
            f"[{index}/{len(QUERIES)}]"
        )

        print(
            query
        )

        try:
            response = client.post(
                (
                    f"/api/databases/"
                    f"{DATABASE_ID}/"
                    f"optimize-query"
                ),
                json={
                    "query": query,
                },
            )

        except Exception as exc:
            failed.append(
                {
                    "query": query,
                    "error": repr(
                        exc
                    ),
                }
            )

            print(
                "REQUEST ERROR:",
                repr(
                    exc
                ),
            )

            continue

        if response.status_code != 200:
            failed.append(
                {
                    "query": query,
                    "status_code": (
                        response.status_code
                    ),
                    "response": (
                        response.text
                    ),
                }
            )

            print(
                "HTTP ERROR:",
                response.status_code,
            )

            print(
                response.text
            )

            continue

        payload = response.json()

        candidates = payload.get(
            "candidates"
        ) or []

        if not candidates:
            skipped.append(
                {
                    "query": query,
                    "reason": (
                        "No index candidate "
                        "generated."
                    ),
                }
            )

            print(
                "SKIPPED: "
                "No candidate generated."
            )

            continue

        for candidate_index, candidate in enumerate(
            candidates,
            start=1,
        ):
            ml_prediction = (
                candidate.get(
                    "ml_prediction"
                )
                or {}
            )

            benchmark = (
                candidate.get(
                    "benchmark"
                )
                or {}
            )

            recommendation = (
                candidate.get(
                    "recommendation"
                )
                or {}
            )

            features = (
                ml_prediction.get(
                    "features"
                )
                or {}
            )

            predicted_improvement = (
                ml_prediction.get(
                    "predicted_improvement_percent"
                )
            )

            actual_improvement = (
                benchmark.get(
                    "improvement_percent"
                )
            )

            if (
                predicted_improvement
                is None
                or actual_improvement
                is None
            ):
                skipped.append(
                    {
                        "query": query,
                        "reason": (
                            "Missing ML or "
                            "benchmark result."
                        ),
                    }
                )

                print(
                    "SKIPPED: "
                    "Missing prediction "
                    "or benchmark."
                )

                continue

            predicted_improvement = float(
                predicted_improvement
            )

            actual_improvement = float(
                actual_improvement
            )

            predicted_status = (
                ml_prediction.get(
                    "predicted_status"
                )
            )

            actual_status = (
                improvement_to_status(
                    actual_improvement
                )
            )

            error = abs(
                actual_improvement
                - predicted_improvement
            )

            has_history = (
                features.get(
                    "historical_success_rate"
                )
                is not None
                or features.get(
                    "historical_avg_improvement"
                )
                is not None
            )

            row = {
                "query_number": index,
                "candidate_number": (
                    candidate_index
                ),
                "query": query,
                "table": (
                    recommendation.get(
                        "table"
                    )
                ),
                "index_name": (
                    recommendation.get(
                        "index_name"
                    )
                ),
                "predicted_improvement": (
                    predicted_improvement
                ),
                "actual_improvement": (
                    actual_improvement
                ),
                "absolute_error": (
                    round(
                        error,
                        2,
                    )
                ),
                "predicted_status": (
                    predicted_status
                ),
                "actual_status": (
                    actual_status
                ),
                "status_correct": (
                    predicted_status
                    == actual_status
                ),
                "benchmark_priority": (
                    ml_prediction.get(
                        "benchmark_priority"
                    )
                ),
                "historical_success_rate": (
                    features.get(
                        "historical_success_rate"
                    )
                ),
                "historical_avg_improvement": (
                    features.get(
                        "historical_avg_improvement"
                    )
                ),
                "has_history": (
                    has_history
                ),
                "before_ms": (
                    benchmark.get(
                        "before_ms"
                    )
                ),
                "after_ms": (
                    benchmark.get(
                        "after_ms"
                    )
                ),
            }

            results.append(
                row
            )

            print(
                "Prediction:",
                f"{predicted_improvement:.2f}%",
            )

            print(
                "Actual:",
                f"{actual_improvement:.2f}%",
            )

            print(
                "Error:",
                f"{error:.2f}",
            )

            print(
                "Status:",
                predicted_status,
                "->",
                actual_status,
            )

            print(
                "History:",
                (
                    "YES"
                    if has_history
                    else "NO"
                ),
            )

    print()

    print_separator()

    print(
        "EVALUATION SUMMARY"
    )

    print_separator()

    if not results:
        print(
            "No usable evaluation "
            "results were generated."
        )

        return

    cold_rows = [
        row
        for row in results
        if not row[
            "has_history"
        ]
    ]

    warm_rows = [
        row
        for row in results
        if row[
            "has_history"
        ]
    ]

    overall_mae = calculate_mae(
        results
    )

    overall_rmse = calculate_rmse(
        results
    )

    overall_accuracy = (
        calculate_status_accuracy(
            results
        )
    )

    print(
        "Total candidates:",
        len(
            results
        ),
    )

    print(
        "Cold-start candidates:",
        len(
            cold_rows
        ),
    )

    print(
        "Warm-history candidates:",
        len(
            warm_rows
        ),
    )

    print(
        "Skipped:",
        len(
            skipped
        ),
    )

    print(
        "Failed:",
        len(
            failed
        ),
    )

    print()

    print(
        "OVERALL"
    )

    print(
        "MAE:",
        (
            f"{overall_mae:.2f}"
            if overall_mae
            is not None
            else "N/A"
        ),
    )

    print(
        "RMSE:",
        (
            f"{overall_rmse:.2f}"
            if overall_rmse
            is not None
            else "N/A"
        ),
    )

    print(
        "Status accuracy:",
        (
            f"{overall_accuracy:.2f}%"
            if overall_accuracy
            is not None
            else "N/A"
        ),
    )

    if cold_rows:
        print()

        print(
            "COLD START ONLY"
        )

        cold_mae = calculate_mae(
            cold_rows
        )

        cold_rmse = calculate_rmse(
            cold_rows
        )

        cold_accuracy = (
            calculate_status_accuracy(
                cold_rows
            )
        )

        print(
            "MAE:",
            f"{cold_mae:.2f}",
        )

        print(
            "RMSE:",
            f"{cold_rmse:.2f}",
        )

        print(
            "Status accuracy:",
            f"{cold_accuracy:.2f}%",
        )

    if warm_rows:
        print()

        print(
            "WARM HISTORY ONLY"
        )

        warm_mae = calculate_mae(
            warm_rows
        )

        warm_rmse = calculate_rmse(
            warm_rows
        )

        warm_accuracy = (
            calculate_status_accuracy(
                warm_rows
            )
        )

        print(
            "MAE:",
            f"{warm_mae:.2f}",
        )

        print(
            "RMSE:",
            f"{warm_rmse:.2f}",
        )

        print(
            "Status accuracy:",
            f"{warm_accuracy:.2f}%",
        )

    print()

    print_separator()

    print(
        "WORST PREDICTIONS"
    )

    print_separator()

    worst_rows = sorted(
        results,
        key=lambda row: (
            row[
                "absolute_error"
            ]
        ),
        reverse=True,
    )[:10]

    for row in worst_rows:
        print()

        print(
            "Query:",
            row[
                "query"
            ],
        )

        print(
            "Predicted:",
            f"{row['predicted_improvement']:.2f}%",
        )

        print(
            "Actual:",
            f"{row['actual_improvement']:.2f}%",
        )

        print(
            "Error:",
            f"{row['absolute_error']:.2f}",
        )

        print(
            "Status:",
            row[
                "predicted_status"
            ],
            "->",
            row[
                "actual_status"
            ],
        )

        print(
            "History:",
            row[
                "has_history"
            ],
        )

    output = {
        "summary": {
            "total_candidates": (
                len(
                    results
                )
            ),
            "cold_start_candidates": (
                len(
                    cold_rows
                )
            ),
            "warm_history_candidates": (
                len(
                    warm_rows
                )
            ),
            "skipped": len(
                skipped
            ),
            "failed": len(
                failed
            ),
            "overall_mae": (
                round(
                    overall_mae,
                    4,
                )
                if overall_mae
                is not None
                else None
            ),
            "overall_rmse": (
                round(
                    overall_rmse,
                    4,
                )
                if overall_rmse
                is not None
                else None
            ),
            "overall_status_accuracy": (
                round(
                    overall_accuracy,
                    2,
                )
                if overall_accuracy
                is not None
                else None
            ),
        },
        "results": results,
        "skipped": skipped,
        "failed": failed,
    }

    output_path = (
        "cold_start_evaluation.json"
    )

    with open(
        output_path,
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            output,
            file,
            indent=2,
            ensure_ascii=False,
        )

    print()

    print_separator()

    print(
        "Saved:",
        output_path,
    )

    print_separator()


if __name__ == "__main__":
    main()