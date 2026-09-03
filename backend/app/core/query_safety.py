import re

from fastapi import HTTPException


FORBIDDEN_KEYWORDS = {
    "INSERT",
    "UPDATE",
    "DELETE",
    "DROP",
    "ALTER",
    "TRUNCATE",
    "CREATE",
    "GRANT",
    "REVOKE",
    "COPY",
    "VACUUM",
    "ANALYZE",
    "REINDEX",
    "CLUSTER",
    "REFRESH",
    "CALL",
    "DO",
    "MERGE",
}


def _remove_sql_comments(query: str) -> str:
    query = re.sub(
        r"--.*?$",
        "",
        query,
        flags=re.MULTILINE,
    )

    query = re.sub(
        r"/\*.*?\*/",
        "",
        query,
        flags=re.DOTALL,
    )

    return query


def _normalize_sql(query: str) -> str:
    query = _remove_sql_comments(query)

    return query.strip()


def validate_read_only_query(
    query: str,
) -> str:
    normalized = _normalize_sql(
        query,
    )

    if not normalized:
        raise HTTPException(
            status_code=400,
            detail="Query cannot be empty.",
        )

    upper_query = normalized.upper()

    if not (
        upper_query.startswith(
            "SELECT",
        )
        or upper_query.startswith(
            "WITH",
        )
    ):
        raise HTTPException(
            status_code=400,
            detail=(
                "Only read-only SELECT queries "
                "are allowed."
            ),
        )

    # Multiple SQL statements are not allowed.
    query_without_final_semicolon = (
        normalized.rstrip(";").strip()
    )

    if ";" in query_without_final_semicolon:
        raise HTTPException(
            status_code=400,
            detail=(
                "Multiple SQL statements "
                "are not allowed."
            ),
        )

    for keyword in FORBIDDEN_KEYWORDS:
        pattern = (
            rf"\b{re.escape(keyword)}\b"
        )

        if re.search(
            pattern,
            upper_query,
        ):
            raise HTTPException(
                status_code=400,
                detail=(
                    f"SQL operation '{keyword}' "
                    "is not allowed."
                ),
            )

    return query_without_final_semicolon