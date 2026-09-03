from __future__ import annotations

import random
from typing import Any, Callable

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.analyzers.plan_analyzer import find_sequential_scans
from app.analyzers.recommendation_evaluator import evaluate_benchmark
from app.benchmark.index_benchmark import benchmark_index_candidate
from app.collectors.explain_collector import collect_explain_plan
from app.db.session import SessionLocal
from app.models.database_connection import DatabaseConnection
from app.recommenders.index_advisor import generate_index_recommendations
from app.services.optimization_service import (
    get_query_evaluation_context,
    persist_optimization_result,
)


DATABASE_ID = 2
RUNS_PER_FAMILY = 10

STATUSES = [
    "PAID",
    "SHIPPED",
    "CANCELLED",
    "PENDING",
]


def random_customer() -> int:
    return random.randint(
        1,
        100000,
    )


def random_status() -> str:
    return random.choice(
        STATUSES
    )


def random_amount() -> int:
    return random.choice(
        [
            25,
            50,
            100,
            250,
            500,
            750,
            1000,
            1500,
        ]
    )


def random_limit() -> int:
    return random.choice(
        [
            10,
            25,
            50,
            100,
        ]
    )


def random_date_range() -> tuple[str, str]:
    year = random.choice(
        [
            2024,
            2025,
            2026,
        ]
    )

    month = random.randint(
        1,
        11,
    )

    start = (
        f"{year}-{month:02d}-01"
    )

    end = (
        f"{year}-{month + 1:02d}-01"
    )

    return start, end


# ---------------------------------------------------------
# QUERY FAMILIES
# ---------------------------------------------------------


def family_01() -> str:
    return (
        "SELECT * FROM orders "
        f"WHERE customer_id = {random_customer()}"
    )


def family_02() -> str:
    return (
        "SELECT * FROM orders "
        f"WHERE status = '{random_status()}'"
    )


def family_03() -> str:
    return (
        "SELECT * FROM orders "
        f"WHERE total_amount > {random_amount()}"
    )


def family_04() -> str:
    return (
        "SELECT * FROM orders "
        f"WHERE total_amount < {random_amount()}"
    )


def family_05() -> str:
    lower = random_amount()

    upper = (
        lower
        + random.choice(
            [
                25,
                50,
                100,
                250,
            ]
        )
    )

    return (
        "SELECT * FROM orders "
        f"WHERE total_amount >= {lower} "
        f"AND total_amount < {upper}"
    )


def family_06() -> str:
    return (
        "SELECT * FROM orders "
        f"WHERE customer_id = {random_customer()} "
        f"AND status = '{random_status()}'"
    )


def family_07() -> str:
    return (
        "SELECT * FROM orders "
        f"WHERE customer_id = {random_customer()} "
        f"AND total_amount > {random_amount()}"
    )


def family_08() -> str:
    return (
        "SELECT * FROM orders "
        f"WHERE status = '{random_status()}' "
        f"AND total_amount > {random_amount()}"
    )


def family_09() -> str:
    return (
        "SELECT * FROM orders "
        f"WHERE customer_id = {random_customer()} "
        f"AND status = '{random_status()}' "
        f"AND total_amount > {random_amount()}"
    )


def family_10() -> str:
    return (
        "SELECT * FROM orders "
        f"WHERE customer_id = {random_customer()} "
        "ORDER BY created_at DESC"
    )


def family_11() -> str:
    return (
        "SELECT * FROM orders "
        f"WHERE customer_id = {random_customer()} "
        "ORDER BY created_at ASC"
    )


def family_12() -> str:
    return (
        "SELECT * FROM orders "
        f"WHERE status = '{random_status()}' "
        "ORDER BY created_at DESC"
    )


def family_13() -> str:
    return (
        "SELECT * FROM orders "
        f"WHERE status = '{random_status()}' "
        "ORDER BY created_at ASC"
    )


def family_14() -> str:
    return (
        "SELECT * FROM orders "
        f"WHERE total_amount > {random_amount()} "
        "ORDER BY created_at DESC"
    )


def family_15() -> str:
    return (
        "SELECT * FROM orders "
        f"WHERE total_amount > {random_amount()} "
        "ORDER BY created_at ASC"
    )


def family_16() -> str:
    return (
        "SELECT * FROM orders "
        f"WHERE customer_id = {random_customer()} "
        f"AND status = '{random_status()}' "
        "ORDER BY created_at DESC"
    )


def family_17() -> str:
    return (
        "SELECT * FROM orders "
        f"WHERE customer_id = {random_customer()} "
        f"AND total_amount > {random_amount()} "
        "ORDER BY created_at DESC"
    )


def family_18() -> str:
    return (
        "SELECT * FROM orders "
        f"WHERE status = '{random_status()}' "
        f"AND total_amount > {random_amount()} "
        "ORDER BY created_at DESC"
    )


def family_19() -> str:
    return (
        "SELECT * FROM orders "
        f"WHERE customer_id = {random_customer()} "
        f"AND status = '{random_status()}' "
        f"AND total_amount > {random_amount()} "
        "ORDER BY created_at DESC"
    )


def family_20() -> str:
    start, end = (
        random_date_range()
    )

    return (
        "SELECT * FROM orders "
        f"WHERE created_at >= '{start}' "
        f"AND created_at < '{end}'"
    )


def family_21() -> str:
    start, end = (
        random_date_range()
    )

    return (
        "SELECT * FROM orders "
        f"WHERE created_at >= '{start}' "
        f"AND created_at < '{end}' "
        "ORDER BY created_at DESC"
    )


def family_22() -> str:
    start, end = (
        random_date_range()
    )

    return (
        "SELECT * FROM orders "
        f"WHERE customer_id = {random_customer()} "
        f"AND created_at >= '{start}' "
        f"AND created_at < '{end}'"
    )


def family_23() -> str:
    start, end = (
        random_date_range()
    )

    return (
        "SELECT * FROM orders "
        f"WHERE status = '{random_status()}' "
        f"AND created_at >= '{start}' "
        f"AND created_at < '{end}'"
    )


def family_24() -> str:
    start, end = (
        random_date_range()
    )

    return (
        "SELECT * FROM orders "
        f"WHERE total_amount > {random_amount()} "
        f"AND created_at >= '{start}' "
        f"AND created_at < '{end}'"
    )


def family_25() -> str:
    start, end = (
        random_date_range()
    )

    return (
        "SELECT * FROM orders "
        f"WHERE customer_id = {random_customer()} "
        f"AND status = '{random_status()}' "
        f"AND created_at >= '{start}' "
        f"AND created_at < '{end}' "
        "ORDER BY created_at DESC"
    )


def family_26() -> str:
    return (
        "SELECT * FROM orders "
        f"WHERE customer_id = {random_customer()} "
        f"LIMIT {random_limit()}"
    )


def family_27() -> str:
    return (
        "SELECT * FROM orders "
        f"WHERE status = '{random_status()}' "
        f"LIMIT {random_limit()}"
    )


def family_28() -> str:
    return (
        "SELECT * FROM orders "
        f"WHERE total_amount > {random_amount()} "
        f"LIMIT {random_limit()}"
    )


def family_29() -> str:
    return (
        "SELECT * FROM orders "
        f"WHERE customer_id = {random_customer()} "
        "ORDER BY created_at DESC "
        f"LIMIT {random_limit()}"
    )


def family_30() -> str:
    return (
        "SELECT * FROM orders "
        f"WHERE status = '{random_status()}' "
        "ORDER BY created_at DESC "
        f"LIMIT {random_limit()}"
    )


def family_31() -> str:
    return (
        "SELECT * FROM orders "
        f"WHERE total_amount > {random_amount()} "
        "ORDER BY created_at DESC "
        f"LIMIT {random_limit()}"
    )


def family_32() -> str:
    return (
        "SELECT * FROM orders "
        f"WHERE customer_id = {random_customer()} "
        f"AND status = '{random_status()}' "
        "ORDER BY created_at DESC "
        f"LIMIT {random_limit()}"
    )


QUERY_FAMILIES: list[
    Callable[[], str]
] = [
    family_01,
    family_02,
    family_03,
    family_04,
    family_05,
    family_06,
    family_07,
    family_08,
    family_09,
    family_10,
    family_11,
    family_12,
    family_13,
    family_14,
    family_15,
    family_16,
    family_17,
    family_18,
    family_19,
    family_20,
    family_21,
    family_22,
    family_23,
    family_24,
    family_25,
    family_26,
    family_27,
    family_28,
    family_29,
    family_30,
    family_31,
    family_32,
]


def get_connection(
    db: Session,
) -> DatabaseConnection:
    connection = db.scalar(
        select(
            DatabaseConnection
        ).where(
            DatabaseConnection.id
            == DATABASE_ID
        )
    )

    if connection is None:
        raise RuntimeError(
            "Target database "
            "connection not found."
        )

    return connection


def run_training_query(
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

    scans = (
        find_sequential_scans(
            plan
        )
    )

    recommendations = (
        generate_index_recommendations(
            connection=connection,
            sequential_scans=scans,
            query=query,
        )
    )

    if not recommendations:
        return {
            "samples": [],
            "candidate_count": 0,
        }

    context = (
        get_query_evaluation_context(
            db=db,
            database_id=DATABASE_ID,
            query_text=query,
        )
    )

    benchmark_results = []

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

        decision = evaluate_benchmark(
            benchmark=benchmark,
            recommendation_history=(
                context[
                    "recommendation_history"
                ]
            ),
            latency_sample_count=(
                context[
                    "latency_sample_count"
                ]
            ),
        )

        benchmark_results.append(
            {
                "recommendation": (
                    recommendation
                ),
                "benchmark": benchmark,
                "decision": decision,
            }
        )

    persistence = (
        persist_optimization_result(
            db=db,
            database_id=DATABASE_ID,
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
        "samples": (
            persistence.get(
                "ml_training_sample_ids",
                [],
            )
        ),
        "candidate_count": len(
            benchmark_results
        ),
    }


def main() -> None:
    db = SessionLocal()

    successful = 0
    skipped = 0
    errors = 0

    try:
        connection = get_connection(
            db
        )

        print(
            "=" * 70
        )

        print(
            "DBOPTIMA DIVERSE DATA GENERATOR"
        )

        print(
            "Query families:",
            len(
                QUERY_FAMILIES
            ),
        )

        print(
            "Runs per family:",
            RUNS_PER_FAMILY,
        )

        print(
            "=" * 70
        )

        for family_number, builder in enumerate(
            QUERY_FAMILIES,
            start=1,
        ):
            print()
            print(
                f"FAMILY "
                f"{family_number}/"
                f"{len(QUERY_FAMILIES)}"
            )

            print(
                builder.__name__
            )

            for run_number in range(
                1,
                RUNS_PER_FAMILY + 1,
            ):
                query = builder()

                print(
                    f"  Run "
                    f"{run_number}/"
                    f"{RUNS_PER_FAMILY}"
                )

                try:
                    result = (
                        run_training_query(
                            db=db,
                            connection=(
                                connection
                            ),
                            query=query,
                        )
                    )

                    sample_ids = (
                        result[
                            "samples"
                        ]
                    )

                    if not sample_ids:
                        skipped += 1

                        print(
                            "    SKIPPED"
                        )

                        continue

                    successful += len(
                        sample_ids
                    )

                    print(
                        "    CREATED:",
                        sample_ids,
                    )

                except KeyboardInterrupt:
                    print()
                    print(
                        "Stopped by user."
                    )

                    return

                except Exception as exc:
                    db.rollback()

                    errors += 1

                    print(
                        "    ERROR:",
                        repr(
                            exc
                        ),
                    )

        print()
        print(
            "=" * 70
        )

        print(
            "GENERATION COMPLETE"
        )

        print(
            "Created samples:",
            successful,
        )

        print(
            "Skipped:",
            skipped,
        )

        print(
            "Errors:",
            errors,
        )

    finally:
        db.close()


if __name__ == "__main__":
    main()