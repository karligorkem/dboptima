import math
import statistics
from typing import Any

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Connection, Engine

from app.models.database_connection import DatabaseConnection


WARMUP_RUNS = 1
BENCHMARK_RUNS = 5


def build_database_url(
    connection: DatabaseConnection,
) -> str:
    return (
        "postgresql+psycopg://"
        f"{connection.username}:"
        f"{connection.password}@"
        f"{connection.host}:"
        f"{connection.port}/"
        f"{connection.database_name}"
    )


def create_target_engine(
    connection: DatabaseConnection,
) -> Engine:
    return create_engine(
        build_database_url(connection),
        pool_pre_ping=True,
        connect_args={
            "connect_timeout": 5,
        },
    )


def get_execution_time(
    target: Connection,
    query: str,
) -> float:
    result = target.execute(
        text(
            f"""
            EXPLAIN (
                ANALYZE,
                BUFFERS,
                FORMAT JSON
            )
            {query}
            """
        )
    ).scalar_one()

    document = result[0]

    return float(
        document.get(
            "Execution Time",
            0.0,
        )
    )


def run_warmup(
    target: Connection,
    query: str,
    runs: int = WARMUP_RUNS,
) -> None:
    for _ in range(runs):
        get_execution_time(
            target=target,
            query=query,
        )


def run_benchmark(
    target: Connection,
    query: str,
    runs: int = BENCHMARK_RUNS,
) -> list[float]:
    measurements: list[float] = []

    for _ in range(runs):
        execution_time = get_execution_time(
            target=target,
            query=query,
        )

        measurements.append(
            execution_time
        )

    return measurements


def calculate_percentile(
    values: list[float],
    percentile: float,
) -> float:
    if not values:
        return 0.0

    sorted_values = sorted(values)

    position = math.ceil(
        percentile * len(sorted_values)
    )

    index = max(
        0,
        min(
            position - 1,
            len(sorted_values) - 1,
        ),
    )

    return sorted_values[index]


def build_statistics(
    measurements: list[float],
) -> dict[str, float]:
    if not measurements:
        return {
            "median_ms": 0.0,
            "mean_ms": 0.0,
            "min_ms": 0.0,
            "max_ms": 0.0,
            "p95_ms": 0.0,
        }

    return {
        "median_ms": round(
            statistics.median(
                measurements
            ),
            3,
        ),
        "mean_ms": round(
            statistics.mean(
                measurements
            ),
            3,
        ),
        "min_ms": round(
            min(measurements),
            3,
        ),
        "max_ms": round(
            max(measurements),
            3,
        ),
        "p95_ms": round(
            calculate_percentile(
                measurements,
                0.95,
            ),
            3,
        ),
    }


def benchmark_index_candidate(
    connection: DatabaseConnection,
    query: str,
    create_index_sql: str,
    index_name: str,
    schema_name: str = "public",
) -> dict[str, Any]:
    engine = create_target_engine(
        connection
    )

    index_created = False

    try:
        with engine.connect() as target:
            # -------------------------
            # BEFORE INDEX
            # -------------------------

            run_warmup(
                target=target,
                query=query,
            )

            before_runs = run_benchmark(
                target=target,
                query=query,
            )

            before_stats = build_statistics(
                before_runs
            )

            # -------------------------
            # CREATE CANDIDATE INDEX
            # -------------------------

            target.execute(
                text(create_index_sql)
            )

            target.commit()

            index_created = True

            # -------------------------
            # AFTER INDEX
            # -------------------------

            run_warmup(
                target=target,
                query=query,
            )

            after_runs = run_benchmark(
                target=target,
                query=query,
            )

            after_stats = build_statistics(
                after_runs
            )

            # Kararı median üzerinden veriyoruz.
            before_ms = before_stats[
                "median_ms"
            ]

            after_ms = after_stats[
                "median_ms"
            ]

            improvement_ms = (
                before_ms - after_ms
            )

            if before_ms > 0:
                improvement_percent = (
                    improvement_ms
                    / before_ms
                    * 100
                )
            else:
                improvement_percent = 0.0

            return {
                "before_ms": round(
                    before_ms,
                    3,
                ),
                "after_ms": round(
                    after_ms,
                    3,
                ),
                "improvement_ms": round(
                    improvement_ms,
                    3,
                ),
                "improvement_percent": round(
                    improvement_percent,
                    2,
                ),
                "is_improvement": (
                    improvement_percent > 0
                ),
                "index_kept": False,

                "benchmark_config": {
                    "warmup_runs": WARMUP_RUNS,
                    "measurement_runs": (
                        BENCHMARK_RUNS
                    ),
                    "decision_metric": (
                        "median"
                    ),
                },

                "before": {
                    "runs_ms": [
                        round(value, 3)
                        for value in before_runs
                    ],
                    **before_stats,
                },

                "after": {
                    "runs_ms": [
                        round(value, 3)
                        for value in after_runs
                    ],
                    **after_stats,
                },
            }

    finally:
        if index_created:
            try:
                with engine.connect() as cleanup:
                    cleanup.execute(
                        text(
                            f'DROP INDEX IF EXISTS '
                            f'"{schema_name}".'
                            f'"{index_name}"'
                        )
                    )

                    cleanup.commit()

                    print(
                        "BENCHMARK CLEANUP:"
                        f" dropped "
                        f"{schema_name}."
                        f"{index_name}"
                    )

            except Exception as cleanup_error:
                print(
                    "BENCHMARK CLEANUP ERROR:",
                    repr(cleanup_error),
                )

        engine.dispose()