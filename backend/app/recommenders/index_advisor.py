import re
from typing import Any

from sqlalchemy import create_engine, text

from app.models.database_connection import DatabaseConnection


FILTER_COLUMN_PATTERN = re.compile(
    r"""
    (?:
        [A-Za-z_][A-Za-z0-9_]*\.
    )?
    "?([A-Za-z_][A-Za-z0-9_]*)"?
    \s*
    \)?
    \s*
    (?:
        ::\s*
        [A-Za-z_][A-Za-z0-9_]*
        (?:\[\])?
    )?
    \s*
    (
        <=
        | >=
        | <>
        | !=
        | =
        | <
        | >
        | IN\b
        | LIKE\b
        | ILIKE\b
    )
    """,
    re.IGNORECASE | re.VERBOSE,
)


ORDER_BY_PATTERN = re.compile(
    r"""
    ORDER\s+BY\s+
    ([A-Za-z_][A-Za-z0-9_.]*)
    (?:\s+(ASC|DESC))?
    """,
    re.IGNORECASE | re.VERBOSE,
)


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


def extract_filter_columns(
    filter_expression: str | None,
) -> list[str]:
    if not filter_expression:
        return []

    matches = FILTER_COLUMN_PATTERN.findall(
        filter_expression
    )

    columns: list[str] = []

    ignored_names = {
        "text",
        "varchar",
        "character",
        "integer",
        "bigint",
        "smallint",
        "numeric",
        "decimal",
        "boolean",
        "date",
        "timestamp",
        "timestamptz",
        "uuid",
        "json",
        "jsonb",
    }

    for column, _operator in matches:
        normalized_column = column.lower()

        if normalized_column in ignored_names:
            continue

        if column not in columns:
            columns.append(column)

    return columns


def extract_order_by(
    query: str,
) -> tuple[str | None, str]:
    match = ORDER_BY_PATTERN.search(query)

    if match is None:
        return None, "ASC"

    raw_column = match.group(1)

    direction = (
        match.group(2) or "ASC"
    ).upper()

    column = raw_column.split(".")[-1]

    return column, direction


def get_existing_indexes(
    connection: DatabaseConnection,
    schema_name: str,
    table_name: str,
) -> list[dict[str, Any]]:
    engine = create_engine(
        build_target_database_url(connection),
        pool_pre_ping=True,
        connect_args={
            "connect_timeout": 5,
        },
    )

    sql = text(
        """
        SELECT
            indexname,
            indexdef
        FROM pg_indexes
        WHERE schemaname = :schema_name
          AND tablename = :table_name
        ORDER BY indexname
        """
    )

    try:
        with engine.connect() as target:
            rows = target.execute(
                sql,
                {
                    "schema_name": schema_name,
                    "table_name": table_name,
                },
            ).mappings().all()

        return [
            {
                "index_name": row["indexname"],
                "index_definition": row["indexdef"],
            }
            for row in rows
        ]

    finally:
        engine.dispose()


def normalize_index_definition(
    definition: str,
) -> str:
    return (
        definition
        .lower()
        .replace('"', "")
        .replace(" ", "")
    )


def index_covers_columns(
    indexes: list[dict[str, Any]],
    columns: list[str],
) -> bool:
    if not columns:
        return False

    expected = ",".join(
        column.lower()
        for column in columns
    )

    for index in indexes:
        definition = normalize_index_definition(
            index["index_definition"]
        )

        if f"({expected}" in definition:
            return True

    return False


def build_index_name(
    table_name: str,
    columns: list[str],
) -> str:
    suffix = "_".join(columns)

    index_name = (
        f"idx_{table_name}_{suffix}"
    )

    return index_name[:63]


def build_create_index_sql(
    schema_name: str,
    table_name: str,
    columns: list[str],
    order_by_column: str | None,
    order_direction: str,
) -> str:
    parts: list[str] = []

    for column in columns:
        if (
            order_by_column
            and column == order_by_column
        ):
            parts.append(
                f'"{column}" {order_direction}'
            )
        else:
            parts.append(
                f'"{column}"'
            )

    column_sql = ", ".join(parts)

    index_name = build_index_name(
        table_name=table_name,
        columns=columns,
    )

    return (
        f'CREATE INDEX "{index_name}" '
        f'ON "{schema_name}"."{table_name}" '
        f"({column_sql});"
    )


def generate_index_recommendations(
    connection: DatabaseConnection,
    sequential_scans: list[dict[str, Any]],
    query: str | None = None,
) -> list[dict[str, Any]]:
    recommendations: list[
        dict[str, Any]
    ] = []

    order_by_column: str | None = None
    order_direction = "ASC"

    if query:
        (
            order_by_column,
            order_direction,
        ) = extract_order_by(query)

    for scan in sequential_scans:
        table_name = scan.get(
            "relation_name"
        )

        schema_name = (
            scan.get("schema")
            or "public"
        )

        filter_expression = scan.get(
            "filter"
        )

        if not table_name:
            continue

        filter_columns = (
            extract_filter_columns(
                filter_expression
            )
        )

        if not filter_columns:
            continue

        candidate_columns = list(
            filter_columns
        )

        if (
            order_by_column
            and order_by_column
            not in candidate_columns
        ):
            candidate_columns.append(
                order_by_column
            )

        indexes = get_existing_indexes(
            connection=connection,
            schema_name=schema_name,
            table_name=table_name,
        )

        if index_covers_columns(
            indexes=indexes,
            columns=candidate_columns,
        ):
            continue

        index_name = build_index_name(
            table_name=table_name,
            columns=candidate_columns,
        )

        sql_command = (
            build_create_index_sql(
                schema_name=schema_name,
                table_name=table_name,
                columns=candidate_columns,
                order_by_column=(
                    order_by_column
                ),
                order_direction=(
                    order_direction
                ),
            )
        )

        recommendations.append(
            {
                "type": "INDEX",
                "schema": schema_name,
                "table": table_name,
                "columns": candidate_columns,
                "index_name": index_name,
                "sql_command": sql_command,
                "reason": (
                    f"{scan.get('node_type')} "
                    f"detected on "
                    f"{schema_name}."
                    f"{table_name}. "
                    f"Filter columns: "
                    f"{filter_columns}. "
                    f"Order column: "
                    f"{order_by_column}. "
                    f"No matching composite "
                    f"index was detected."
                ),
                "source": {
                    "node_type": (
                        scan.get(
                            "node_type"
                        )
                    ),
                    "filter": (
                        filter_expression
                    ),
                    "plan_rows": (
                        scan.get(
                            "plan_rows"
                        )
                    ),
                    "actual_rows": (
                        scan.get(
                            "actual_rows"
                        )
                    ),
                    "actual_total_time": (
                        scan.get(
                            "actual_total_time"
                        )
                    ),
                    "rows_removed_by_filter": (
                        scan.get(
                            "rows_removed_by_filter"
                        )
                    ),
                },
            }
        )

    return recommendations