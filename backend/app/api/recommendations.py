from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db.dependencies import get_db


router = APIRouter(
    prefix="/api/recommendations",
    tags=["recommendations"],
)


@router.get("/{database_id}")
def get_recommendations(
    database_id: int,
    status: str | None = Query(default=None),
    latest_only: bool = Query(default=True),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    params = {
        "database_id": database_id,
        "limit": limit,
        "offset": offset,
    }

    status_filter = ""

    if status:
        status_filter = """
            AND recommendation_status = :status
        """
        params["status"] = status.upper()

    if latest_only:
        base_cte = """
        WITH recommendation_rows AS (
            SELECT
                r.id AS recommendation_id,
                r.query_id,
                q.normalized_query AS query,
                r.recommendation_type AS type,
                r.sql_command,
                r.reason,
                r.status AS recommendation_status,
                r.confidence,
                r.before_ms,
                r.after_ms,
                r.improvement_ms,
                r.improvement_percent,
                r.created_at,
                ROW_NUMBER() OVER (
                    PARTITION BY r.query_id
                    ORDER BY r.created_at DESC, r.id DESC
                ) AS row_number
            FROM recommendations r
            JOIN queries q
                ON q.id = r.query_id
            WHERE q.database_id = :database_id
        )
        """
        latest_filter = """
            AND row_number = 1
        """
    else:
        base_cte = """
        WITH recommendation_rows AS (
            SELECT
                r.id AS recommendation_id,
                r.query_id,
                q.normalized_query AS query,
                r.recommendation_type AS type,
                r.sql_command,
                r.reason,
                r.status AS recommendation_status,
                r.confidence,
                r.before_ms,
                r.after_ms,
                r.improvement_ms,
                r.improvement_percent,
                r.created_at,
                1 AS row_number
            FROM recommendations r
            JOIN queries q
                ON q.id = r.query_id
            WHERE q.database_id = :database_id
        )
        """
        latest_filter = ""

    count_query = text(
        f"""
        {base_cte}

        SELECT COUNT(*)
        FROM recommendation_rows
        WHERE 1 = 1
        {latest_filter}
        {status_filter}
        """
    )

    rows_query = text(
        f"""
        {base_cte}

        SELECT
            recommendation_id,
            query_id,
            query,
            type,
            sql_command,
            reason,
            recommendation_status AS status,
            confidence,
            before_ms,
            after_ms,
            improvement_ms,
            improvement_percent,
            created_at
        FROM recommendation_rows
        WHERE 1 = 1
        {latest_filter}
        {status_filter}
        ORDER BY created_at DESC, recommendation_id DESC
        LIMIT :limit
        OFFSET :offset
        """
    )

    total = db.execute(
        count_query,
        params,
    ).scalar_one()

    rows = db.execute(
        rows_query,
        params,
    ).mappings().all()

    return {
        "database_id": database_id,
        "latest_only": latest_only,
        "total": total,
        "limit": limit,
        "offset": offset,
        "items": [
            dict(row)
            for row in rows
        ],
    }