from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db.dependencies import get_db


router = APIRouter(
    prefix="/api/benchmarks",
    tags=["benchmarks"],
)


@router.get("/{database_id}")
def get_benchmarks(
    database_id: int,
    status: str | None = Query(default=None),
    limit: int = Query(default=25, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    params: dict[str, object] = {
        "database_id": database_id,
        "limit": limit,
        "offset": offset,
    }

    status_filter = ""

    if status:
        status_filter = """
            AND r.status = :status
        """
        params["status"] = status.upper()

    metrics_query = text(
        f"""
        SELECT
            COUNT(*) AS total_runs,

            COUNT(*) FILTER (
                WHERE r.before_ms IS NOT NULL
                AND r.after_ms IS NOT NULL
            ) AS measured_runs,

            COUNT(*) FILTER (
                WHERE r.improvement_percent > 0
            ) AS improved_runs,

            COUNT(*) FILTER (
                WHERE r.status = 'RECOMMENDED'
            ) AS recommended_runs,

            COUNT(*) FILTER (
                WHERE r.status = 'REVIEW'
            ) AS review_runs,

            COUNT(*) FILTER (
                WHERE r.status = 'REJECTED'
            ) AS rejected_runs,

            COALESCE(
                AVG(r.before_ms)
                FILTER (
                    WHERE r.before_ms IS NOT NULL
                ),
                0
            ) AS average_before_ms,

            COALESCE(
                AVG(r.after_ms)
                FILTER (
                    WHERE r.after_ms IS NOT NULL
                ),
                0
            ) AS average_after_ms,

            COALESCE(
                AVG(r.improvement_percent)
                FILTER (
                    WHERE r.improvement_percent IS NOT NULL
                ),
                0
            ) AS average_gain_percent,

            COALESCE(
                percentile_cont(0.5)
                WITHIN GROUP (
                    ORDER BY r.improvement_percent
                )
                FILTER (
                    WHERE r.improvement_percent IS NOT NULL
                ),
                0
            ) AS median_gain_percent,

            COALESCE(
                MAX(r.improvement_percent)
                FILTER (
                    WHERE r.improvement_percent IS NOT NULL
                ),
                0
            ) AS best_gain_percent,

            COALESCE(
                AVG(r.confidence)
                FILTER (
                    WHERE r.confidence IS NOT NULL
                ),
                0
            ) AS average_confidence

        FROM recommendations r
        JOIN queries q
            ON q.id = r.query_id

        WHERE q.database_id = :database_id
        {status_filter}
        """
    )

    count_query = text(
        f"""
        SELECT COUNT(*)
        FROM recommendations r
        JOIN queries q
            ON q.id = r.query_id
        WHERE q.database_id = :database_id
        {status_filter}
        """
    )

    rows_query = text(
        f"""
        SELECT
            r.id AS benchmark_id,
            r.query_id,
            q.normalized_query AS query,
            r.recommendation_type AS recommendation_type,
            r.sql_command,
            r.status,
            r.confidence,
            r.before_ms,
            r.after_ms,
            r.improvement_ms,
            r.improvement_percent,
            r.reason,
            r.created_at

        FROM recommendations r
        JOIN queries q
            ON q.id = r.query_id

        WHERE q.database_id = :database_id
        {status_filter}

        ORDER BY
            r.created_at DESC,
            r.id DESC

        LIMIT :limit
        OFFSET :offset
        """
    )

    metrics = db.execute(
        metrics_query,
        params,
    ).mappings().one()

    total = db.execute(
        count_query,
        params,
    ).scalar_one()

    rows = db.execute(
        rows_query,
        params,
    ).mappings().all()

    total_runs = int(
        metrics["total_runs"] or 0
    )

    improved_runs = int(
        metrics["improved_runs"] or 0
    )

    success_rate = (
        (
            improved_runs /
            total_runs
        ) * 100
        if total_runs > 0
        else 0
    )

    return {
        "database_id": database_id,

        "metrics": {
            "total_runs": total_runs,
            "measured_runs": int(
                metrics["measured_runs"] or 0
            ),
            "improved_runs": improved_runs,
            "success_rate": round(
                success_rate,
                2,
            ),

            "recommended_runs": int(
                metrics["recommended_runs"] or 0
            ),
            "review_runs": int(
                metrics["review_runs"] or 0
            ),
            "rejected_runs": int(
                metrics["rejected_runs"] or 0
            ),

            "average_before_ms": round(
                float(
                    metrics["average_before_ms"]
                    or 0
                ),
                3,
            ),

            "average_after_ms": round(
                float(
                    metrics["average_after_ms"]
                    or 0
                ),
                3,
            ),

            "average_gain_percent": round(
                float(
                    metrics["average_gain_percent"]
                    or 0
                ),
                2,
            ),

            "median_gain_percent": round(
                float(
                    metrics["median_gain_percent"]
                    or 0
                ),
                2,
            ),

            "best_gain_percent": round(
                float(
                    metrics["best_gain_percent"]
                    or 0
                ),
                2,
            ),

            "average_confidence": round(
                float(
                    metrics["average_confidence"]
                    or 0
                ),
                4,
            ),
        },

        "pagination": {
            "total": total,
            "limit": limit,
            "offset": offset,
        },

        "items": [
            dict(row)
            for row in rows
        ],
    }