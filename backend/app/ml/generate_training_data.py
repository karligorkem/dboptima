from __future__ import annotations

import random
from collections import Counter
from typing import Any, Callable

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.analyzers.plan_analyzer import find_sequential_scans
from app.analyzers.recommendation_evaluator import evaluate_benchmark
from app.benchmark.index_benchmark import benchmark_index_candidate
from app.collectors.explain_collector import collect_explain_plan
from app.db.session import SessionLocal
from app.models.database_connection import DatabaseConnection
from app.models.ml_training_sample import MLTrainingSample
from app.recommenders.index_advisor import generate_index_recommendations
from app.services.optimization_service import (
    get_query_evaluation_context,
    persist_optimization_result,
)


DATABASE_ID = 2

TARGET_PER_CLASS = {
    "RECOMMENDED": 100,
    "REVIEW": 100,
    "REJECTED": 100,
}

MAX_ATTEMPTS = 1500

STATUSES = [
    "PAID",
    "SHIPPED",
    "CANCELLED",
    "PENDING",
]


def get_database_connection(
    db: Session,
    database_id: int,
) -> DatabaseConnection:
    connection = db.scalar(
        select(
            DatabaseConnection
        ).where(
            DatabaseConnection.id
            == database_id
        )
    )

    if connection is None:
        raise RuntimeError(
            f"Database connection {database_id} not found."
        )

    return connection


def get_current_class_counts(
    db: Session,
) -> dict[str, int]:
    statuses = db.scalars(
        select(
            MLTrainingSample.decision_status
        )
    ).all()

    counts = Counter(
        str(status)
        for status in statuses
    )

    return {
        "RECOMMENDED": counts.get(
            "RECOMMENDED",
            0,
        ),
        "REVIEW": counts.get(
            "REVIEW",
            0,
        ),
        "REJECTED": counts.get(
            "REJECTED",
            0,
        ),
    }


def dataset_complete(
    counts: dict[str, int],
) -> bool:
    return all(
        counts.get(
            status,
            0,
        )
        >= target
        for status, target
        in TARGET_PER_CLASS.items()
    )


def print_counts(
    counts: dict[str, int],
) -> None:
    print(
        "DATASET:"
        f" RECOMMENDED="
        f"{counts['RECOMMENDED']}/"
        f"{TARGET_PER_CLASS['RECOMMENDED']},"
        f" REVIEW="
        f"{counts['REVIEW']}/"
        f"{TARGET_PER_CLASS['REVIEW']},"
        f" REJECTED="
        f"{counts['REJECTED']}/"
        f"{TARGET_PER_CLASS['REJECTED']}"
    )


def random_customer_id() -> int:
    return random.randint(
        1,
        100000,
    )


def random_status() -> str:
    return random.choice(
        STATUSES
    )


def build_customer_status_query() -> str:
    customer_id = random_customer_id()
    status = random_status()

    return (
        "SELECT * FROM orders "
        f"WHERE customer_id = {customer_id} "
        f"AND status = '{status}' "
        "ORDER BY created_at DESC"
    )


def build_customer_query() -> str:
    customer_id = random_customer_id()

    return (
        "SELECT * FROM orders "
        f"WHERE customer_id = {customer_id}"
    )


def build_status_query() -> str:
    status = random_status()

    return (
        "SELECT * FROM orders "
        f"WHERE status = '{status}'"
    )


def build_status_ordered_query() -> str:
    status = random_status()

    return (
        "SELECT * FROM orders "
        f"WHERE status = '{status}' "
        "ORDER BY created_at DESC"
    )


def build_amount_low_selectivity_query() -> str:
    threshold = random.choice(
        [
            10,
            25,
            50,
            100,
        ]
    )

    return (
        "SELECT * FROM orders "
        f"WHERE total_amount > {threshold}"
    )


def build_amount_high_selectivity_query() -> str:
    threshold = random.choice(
        [
            500,
            750,
            1000,
            1500,
            2000,
        ]
    )

    return (
        "SELECT * FROM orders "
        f"WHERE total_amount > {threshold}"
    )


def build_amount_range_query() -> str:
    lower = random.choice(
        [
            50,
            100,
            250,
            500,
        ]
    )

    width = random.choice(
        [
            10,
            25,
            50,
            100,
        ]
    )

    upper = (
        lower
        + width
    )

    return (
        "SELECT * FROM orders "
        f"WHERE total_amount >= {lower} "
        f"AND total_amount < {upper}"
    )


def build_customer_amount_query() -> str:
    customer_id = random_customer_id()

    threshold = random.choice(
        [
            50,
            100,
            250,
            500,
            1000,
        ]
    )

    return (
        "SELECT * FROM orders "
        f"WHERE customer_id = {customer_id} "
        f"AND total_amount > {threshold}"
    )


def build_status_amount_query() -> str:
    status = random_status()

    threshold = random.choice(
        [
            25,
            50,
            100,
            250,
            500,
        ]
    )

    return (
        "SELECT * FROM orders "
        f"WHERE status = '{status}' "
        f"AND total_amount > {threshold}"
    )


def build_status_amount_ordered_query() -> str:
    status = random_status()

    threshold = random.choice(
        [
            25,
            50,
            100,
            250,
            500,
        ]
    )

    return (
        "SELECT * FROM orders "
        f"WHERE status = '{status}' "
        f"AND total_amount > {threshold} "
        "ORDER BY created_at DESC"
    )


def build_customer_status_amount_query() -> str:
    customer_id = random_customer_id()
    status = random_status()

    threshold = random.choice(
        [
            50,
            100,
            250,
            500,
            1000,
        ]
    )

    return (
        "SELECT * FROM orders "
        f"WHERE customer_id = {customer_id} "
        f"AND status = '{status}' "
        f"AND total_amount > {threshold} "
        "ORDER BY created_at DESC"
    )


GENERAL_BUILDERS: list[
    Callable[[], str]
] = [
    build_customer_status_query,
    build_customer_query,
    build_status_query,
    build_status_ordered_query,
    build_amount_low_selectivity_query,
    build_amount_high_selectivity_query,
    build_amount_range_query,
    build_customer_amount_query,
    build_status_amount_query,
    build_status_amount_ordered_query,
    build_customer_status_amount_query,
]


RECOMMENDED_BUILDERS: list[
    Callable[[], str]
] = [
    build_customer_query,
    build_customer_status_query,
    build_customer_amount_query,
    build_customer_status_amount_query,
]


BORDERLINE_BUILDERS: list[
    Callable[[], str]
] = [
    build_status_query,
    build_status_ordered_query,
    build_amount_low_selectivity_query,
    build_amount_high_selectivity_query,
    build_amount_range_query,
    build_status_amount_query,
    build_status_amount_ordered_query,
]


def choose_query_builder(
    counts: dict[str, int],
) -> Callable[[], str]:
    deficits = {
        status: max(
            TARGET_PER_CLASS[
                status
            ]
            - counts.get(
                status,
                0,
            ),
            0,
        )
        for status
        in TARGET_PER_CLASS
    }

    largest_deficit = max(
        deficits,
        key=deficits.get,
    )

    if (
        largest_deficit
        == "RECOMMENDED"
    ):
        return random.choice(
            RECOMMENDED_BUILDERS
        )

    if largest_deficit in {
        "REVIEW",
        "REJECTED",
    }:
        return random.choice(
            BORDERLINE_BUILDERS
        )

    return random.choice(
        GENERAL_BUILDERS
    )


def optimize_query_for_training(
    db: Session,
    connection: DatabaseConnection,
    query: str,
) -> dict[str, Any]:
    explain_result = (
        collect_explain_plan(
            connection=connection,
            query=query,
        )
    )

    plan = explain_result.get(
        "plan",
        {},
    )

    sequential_scans = (
        find_sequential_scans(
            plan
        )
    )

    recommendations = (
        generate_index_recommendations(
            connection=connection,
            sequential_scans=(
                sequential_scans
            ),
            query=query,
        )
    )

    if not recommendations:
        return {
            "query": query,
            "candidate_count": 0,
            "benchmark_results": [],
            "persistence": None,
        }

    evaluation_context = (
        get_query_evaluation_context(
            db=db,
            database_id=(
                connection.id
            ),
            query_text=query,
        )
    )

    benchmark_results: list[
        dict[str, Any]
    ] = []

    for recommendation in recommendations:
        benchmark = (
            benchmark_index_candidate(
                connection=connection,
                query=query,
                create_index_sql=(
                    recommendation[
                        "sql_command"
                    ]
                ),
                index_name=(
                    recommendation[
                        "index_name"
                    ]
                ),
                schema_name=(
                    recommendation.get(
                        "schema",
                        "public",
                    )
                ),
            )
        )

        decision = (
            evaluate_benchmark(
                benchmark=benchmark,
                recommendation_history=(
                    evaluation_context[
                        "recommendation_history"
                    ]
                ),
                latency_sample_count=(
                    evaluation_context[
                        "latency_sample_count"
                    ]
                ),
            )
        )

        benchmark_results.append(
            {
                "recommendation": (
                    recommendation
                ),
                "benchmark": (
                    benchmark
                ),
                "decision": (
                    decision
                ),
            }
        )

    benchmark_results.sort(
        key=lambda item: (
            item[
                "benchmark"
            ].get(
                "improvement_percent",
                0.0,
            )
        ),
        reverse=True,
    )

    persistence = (
        persist_optimization_result(
            db=db,
            database_id=(
                connection.id
            ),
            query_text=query,
            explain_result=(
                explain_result
            ),
            benchmark_results=(
                benchmark_results
            ),
        )
    )

    return {
        "query": query,
        "candidate_count": len(
            benchmark_results
        ),
        "benchmark_results": (
            benchmark_results
        ),
        "persistence": (
            persistence
        ),
    }


def generate_training_data() -> None:
    db = SessionLocal()

    try:
        connection = (
            get_database_connection(
                db=db,
                database_id=(
                    DATABASE_ID
                ),
            )
        )

        counts = (
            get_current_class_counts(
                db
            )
        )

        print()
        print(
            "=" * 80
        )

        print(
            "DBOPTIMA TRAINING DATA GENERATOR"
        )

        print_counts(
            counts
        )

        if dataset_complete(
            counts
        ):
            print(
                "Dataset targets are "
                "already complete."
            )
            return

        attempt = 0

        while (
            attempt
            < MAX_ATTEMPTS
        ):
            counts = (
                get_current_class_counts(
                    db
                )
            )

            if dataset_complete(
                counts
            ):
                break

            attempt += 1

            builder = (
                choose_query_builder(
                    counts
                )
            )

            query = builder()

            print()
            print(
                "-" * 80
            )

            print(
                f"ATTEMPT "
                f"{attempt}/"
                f"{MAX_ATTEMPTS}"
            )

            print_counts(
                counts
            )

            print(
                "BUILDER:",
                builder.__name__,
            )

            print(
                "QUERY:",
                query,
            )

            try:
                result = (
                    optimize_query_for_training(
                        db=db,
                        connection=(
                            connection
                        ),
                        query=query,
                    )
                )

                if (
                    result[
                        "candidate_count"
                    ]
                    == 0
                ):
                    print(
                        "SKIPPED: "
                        "no candidate generated."
                    )

                    continue

                persistence = (
                    result.get(
                        "persistence"
                    )
                    or {}
                )

                sample_ids = (
                    persistence.get(
                        "ml_training_sample_ids",
                        [],
                    )
                )

                print(
                    "ML SAMPLE IDS:",
                    sample_ids,
                )

                for benchmark_result in (
                    result[
                        "benchmark_results"
                    ]
                ):
                    benchmark = (
                        benchmark_result[
                            "benchmark"
                        ]
                    )

                    decision = (
                        benchmark_result[
                            "decision"
                        ]
                    )

                    print(
                        "RESULT:",
                        decision.get(
                            "status"
                        ),
                        "| improvement:",
                        benchmark.get(
                            "improvement_percent"
                        ),
                        "%",
                        "| stability:",
                        decision.get(
                            "benchmark_stability"
                        ),
                        "| confidence:",
                        decision.get(
                            "confidence"
                        ),
                    )

            except KeyboardInterrupt:
                print()
                print(
                    "Generation stopped "
                    "by user."
                )

                break

            except Exception as exc:
                db.rollback()

                print(
                    "SAMPLE ERROR:",
                    repr(
                        exc
                    ),
                )

        final_counts = (
            get_current_class_counts(
                db
            )
        )

        print()
        print(
            "=" * 80
        )

        print(
            "GENERATION FINISHED"
        )

        print(
            "ATTEMPTS:",
            attempt,
        )

        print_counts(
            final_counts
        )

        if dataset_complete(
            final_counts
        ):
            print(
                "TARGET DATASET COMPLETE."
            )
        else:
            print(
                "Target distribution "
                "was not reached."
            )

            print(
                "This is not necessarily "
                "an error."
            )

            print(
                "The real benchmark "
                "distribution may naturally "
                "contain fewer REVIEW or "
                "REJECTED cases."
            )

    finally:
        db.close()


if __name__ == "__main__":
    generate_training_data()