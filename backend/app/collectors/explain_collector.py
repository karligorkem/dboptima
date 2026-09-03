from typing import Any

from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

from app.models.database_connection import DatabaseConnection


def build_target_database_url(
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


def collect_explain_plan(
    connection: DatabaseConnection,
    query: str,
) -> dict[str, Any]:
    database_url = build_target_database_url(connection)

    engine = create_engine(
        database_url,
        pool_pre_ping=True,
        connect_args={
            "connect_timeout": 5,
        },
    )

    try:
        explain_query = (
            "EXPLAIN "
            "(ANALYZE, BUFFERS, VERBOSE, FORMAT JSON) "
            f"{query}"
        )

        with engine.connect() as target:
            result = target.execute(
                text(explain_query)
            ).scalar_one()

        if not result:
            raise ValueError(
                "PostgreSQL returned an empty execution plan."
            )

        plan_document = result[0]

        if "Plan" not in plan_document:
            raise ValueError(
                "Execution plan does not contain a Plan object."
            )

        return {
            "plan": plan_document["Plan"],
            "planning_time": plan_document.get(
                "Planning Time"
            ),
            "execution_time": plan_document.get(
                "Execution Time"
            ),
        }

    except SQLAlchemyError:
        raise

    finally:
        engine.dispose()