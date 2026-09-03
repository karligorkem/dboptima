from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db.dependencies import get_db


router = APIRouter(
    prefix="/api/workload",
    tags=["workload"],
)


@router.get("/{database_id}")
def get_workload(
    database_id: int,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    sort: str = Query(default="p95"),
    db: Session = Depends(get_db),
):
    allowed_sorts = {
        "p95": "q.p95_latency_ms DESC NULLS LAST",
        "avg": "q.avg_latency_ms DESC NULLS LAST",
        "calls": "q.total_calls DESC NULLS LAST",
        "max": "q.max_latency_ms DESC NULLS LAST",
        "recent": "q.last_seen DESC NULLS LAST",
    }

    order_by = allowed_sorts.get(
        sort,
        allowed_sorts["p95"],
    )

    params = {
        "database_id": database_id,
        "limit": limit,
        "offset": offset,
    }

    count_query = text(
        """
        SELECT COUNT(*)
        FROM queries q
        WHERE q.database_id = :database_id
        """
    )

    metrics_query = text(
        """
        SELECT
            COUNT(*) AS query_count,

            COALESCE(
                SUM(q.total_calls),
                0
            ) AS total_calls,

            COALESCE(
                AVG(q.avg_latency_ms),
                0
            ) AS average_query_latency_ms,

            COALESCE(
                AVG(q.p95_latency_ms),
                0
            ) AS average_p95_latency_ms,

            COALESCE(
                MAX(q.max_latency_ms),
                0
            ) AS worst_latency_ms,

            MAX(q.last_seen) AS last_activity_at

        FROM queries q
        WHERE q.database_id = :database_id
        """
    )

    rows_query = text(
        f"""
        SELECT
            q.id AS query_id,
            q.query_hash,
            q.normalized_query AS query,

            q.total_calls,
            q.avg_latency_ms,
            q.min_latency_ms,
            q.max_latency_ms,
            q.p95_latency_ms,

            q.first_seen,
            q.last_seen,

            (
                SELECT COUNT(*)
                FROM query_execution_samples s
                WHERE s.query_id = q.id
            ) AS latency_sample_count,

            (
                SELECT COUNT(*)
                FROM recommendations r
                WHERE r.query_id = q.id
            ) AS recommendation_count,

            (
                SELECT COUNT(*)
                FROM recommendations r
                WHERE r.query_id = q.id
                AND r.status = 'RECOMMENDED'
            ) AS recommended_count,

            (
                SELECT MAX(r.improvement_percent)
                FROM recommendations r
                WHERE r.query_id = q.id
            ) AS best_measured_gain,

            (
                SELECT r.status
                FROM recommendations r
                WHERE r.query_id = q.id
                ORDER BY r.created_at DESC, r.id DESC
                LIMIT 1
            ) AS latest_status,

            (
                SELECT r.improvement_percent
                FROM recommendations r
                WHERE r.query_id = q.id
                ORDER BY r.created_at DESC, r.id DESC
                LIMIT 1
            ) AS latest_measured_gain,

            (
                SELECT r.confidence
                FROM recommendations r
                WHERE r.query_id = q.id
                ORDER BY r.created_at DESC, r.id DESC
                LIMIT 1
            ) AS latest_confidence

        FROM queries q

        WHERE q.database_id = :database_id

        ORDER BY {order_by}

        LIMIT :limit
        OFFSET :offset
        """
    )

    total = db.execute(
        count_query,
        params,
    ).scalar_one()

    metrics = db.execute(
        metrics_query,
        params,
    ).mappings().one()

    rows = db.execute(
        rows_query,
        params,
    ).mappings().all()

    items = []

    for row in rows:
        item = dict(row)

        for field in (
            "avg_latency_ms",
            "min_latency_ms",
            "max_latency_ms",
            "p95_latency_ms",
            "best_measured_gain",
            "latest_measured_gain",
            "latest_confidence",
        ):
            value = item.get(field)

            if value is not None:
                item[field] = round(
                    float(value),
                    4,
                )

        items.append(item)

    return {
        "database_id": database_id,

        "metrics": {
            "query_count": int(
                metrics["query_count"] or 0
            ),

            "total_calls": int(
                metrics["total_calls"] or 0
            ),

            "average_query_latency_ms": round(
                float(
                    metrics["average_query_latency_ms"]
                    or 0
                ),
                3,
            ),

            "average_p95_latency_ms": round(
                float(
                    metrics["average_p95_latency_ms"]
                    or 0
                ),
                3,
            ),

            "worst_latency_ms": round(
                float(
                    metrics["worst_latency_ms"]
                    or 0
                ),
                3,
            ),

            "last_activity_at":
                metrics["last_activity_at"],
        },

        "pagination": {
            "total": total,
            "limit": limit,
            "offset": offset,
        },

        "sort": sort,

        "items": items,
    }