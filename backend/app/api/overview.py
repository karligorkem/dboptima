from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.db.dependencies import get_db


router = APIRouter(
    prefix="/api/overview",
    tags=["overview"],
)


@router.get(
    "/{database_id}",
)
def get_database_overview(
    database_id: int,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    try:
        # ====================================================
        # 1. DATABASE
        # ====================================================

        database = db.execute(
            text(
                """
                SELECT
                    id,
                    name,
                    host,
                    port,
                    database_name,
                    username,
                    created_at
                FROM database_connections
                WHERE id = :database_id
                """
            ),
            {
                "database_id": database_id,
            },
        ).mappings().one_or_none()

        if database is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Database connection not found.",
            )

        # ====================================================
        # 2. QUERY SUMMARY
        # ====================================================

        query_summary = db.execute(
            text(
                """
                SELECT
                    COUNT(*) AS analyzed_queries,
                    COALESCE(
                        SUM(total_calls),
                        0
                    ) AS total_calls
                FROM queries
                WHERE database_id = :database_id
                """
            ),
            {
                "database_id": database_id,
            },
        ).mappings().one()

        # ====================================================
        # 3. LATENCY SAMPLE COUNT
        # ====================================================

        latency_summary = db.execute(
            text(
                """
                SELECT
                    COUNT(qes.id) AS latency_sample_count
                FROM query_execution_samples qes
                JOIN queries q
                    ON q.id = qes.query_id
                WHERE q.database_id = :database_id
                """
            ),
            {
                "database_id": database_id,
            },
        ).mappings().one()

        # ====================================================
        # 4. RECOMMENDATION SUMMARY
        # ====================================================

        recommendation_summary = db.execute(
            text(
                """
                SELECT
                    COUNT(r.id) AS total_recommendations,

                    COUNT(r.id)
                        FILTER (
                            WHERE r.status = 'RECOMMENDED'
                        )
                        AS recommended_count,

                    COUNT(r.id)
                        FILTER (
                            WHERE r.status = 'REVIEW'
                        )
                        AS review_count,

                    COUNT(r.id)
                        FILTER (
                            WHERE r.status = 'REJECTED'
                        )
                        AS rejected_count,

                    COALESCE(
                        AVG(r.improvement_percent)
                            FILTER (
                                WHERE
                                    r.improvement_percent
                                    IS NOT NULL
                            ),
                        0
                    ) AS average_measured_gain,

                    COALESCE(
                        percentile_cont(0.5)
                        WITHIN GROUP (
                            ORDER BY
                                r.improvement_percent
                        )
                        FILTER (
                            WHERE
                                r.improvement_percent
                                IS NOT NULL
                        ),
                        0
                    ) AS median_measured_gain,

                    COALESCE(
                        AVG(r.confidence)
                            FILTER (
                                WHERE
                                    r.confidence
                                    IS NOT NULL
                            ),
                        0
                    ) AS average_confidence

                FROM recommendations r
                JOIN queries q
                    ON q.id = r.query_id
                WHERE q.database_id = :database_id
                """
            ),
            {
                "database_id": database_id,
            },
        ).mappings().one()

        # ====================================================
        # 5. RECENT OPTIMIZATIONS
        # ====================================================

        recent_rows = db.execute(
            text(
                """
                SELECT
                    r.id,
                    r.query_id,
                    q.normalized_query,
                    r.recommendation_type,
                    r.sql_command,
                    r.reason,
                    r.status,
                    r.confidence,
                    r.before_ms,
                    r.after_ms,
                    r.improvement_ms,
                    r.improvement_percent,
                    r.created_at
                FROM recommendations r
                JOIN queries q
                    ON q.id = r.query_id
                WHERE q.database_id = :database_id
                ORDER BY
                    r.created_at DESC,
                    r.id DESC
                LIMIT 10
                """
            ),
            {
                "database_id": database_id,
            },
        ).mappings().all()

        recent_optimizations: list[
            dict[str, Any]
        ] = []

        for row in recent_rows:
            recent_optimizations.append(
                {
                    "recommendation_id": (
                        row[
                            "id"
                        ]
                    ),
                    "query_id": (
                        row[
                            "query_id"
                        ]
                    ),
                    "query": (
                        row[
                            "normalized_query"
                        ]
                    ),
                    "type": (
                        row[
                            "recommendation_type"
                        ]
                    ),
                    "sql_command": (
                        row[
                            "sql_command"
                        ]
                    ),
                    "reason": (
                        row[
                            "reason"
                        ]
                    ),
                    "status": (
                        row[
                            "status"
                        ]
                    ),
                    "confidence": (
                        float(
                            row[
                                "confidence"
                            ]
                        )
                        if row[
                            "confidence"
                        ]
                        is not None
                        else None
                    ),
                    "before_ms": (
                        float(
                            row[
                                "before_ms"
                            ]
                        )
                        if row[
                            "before_ms"
                        ]
                        is not None
                        else None
                    ),
                    "after_ms": (
                        float(
                            row[
                                "after_ms"
                            ]
                        )
                        if row[
                            "after_ms"
                        ]
                        is not None
                        else None
                    ),
                    "improvement_ms": (
                        float(
                            row[
                                "improvement_ms"
                            ]
                        )
                        if row[
                            "improvement_ms"
                        ]
                        is not None
                        else None
                    ),
                    "improvement_percent": (
                        float(
                            row[
                                "improvement_percent"
                            ]
                        )
                        if row[
                            "improvement_percent"
                        ]
                        is not None
                        else None
                    ),
                    "created_at": (
                        row[
                            "created_at"
                        ].isoformat()
                        if row[
                            "created_at"
                        ]
                        is not None
                        else None
                    ),
                }
            )

        # ====================================================
        # 6. LATEST RECOMMENDATION
        # ====================================================

        latest_recommendation = (
            recent_optimizations[0]
            if recent_optimizations
            else None
        )

        # ====================================================
        # 7. RESPONSE
        # ====================================================

        return {
            "database": {
                "id": database["id"],
                "name": database["name"],
                "host": database["host"],
                "port": database["port"],
                "database_name": (
                    database[
                        "database_name"
                    ]
                ),
                "username": (
                    database[
                        "username"
                    ]
                ),
            },

            "metrics": {
                "analyzed_queries": int(
                    query_summary[
                        "analyzed_queries"
                    ]
                    or 0
                ),

                "total_calls": int(
                    query_summary[
                        "total_calls"
                    ]
                    or 0
                ),

                "latency_sample_count": int(
                    latency_summary[
                        "latency_sample_count"
                    ]
                    or 0
                ),

                "total_recommendations": int(
                    recommendation_summary[
                        "total_recommendations"
                    ]
                    or 0
                ),

                "recommended_count": int(
                    recommendation_summary[
                        "recommended_count"
                    ]
                    or 0
                ),

                "review_count": int(
                    recommendation_summary[
                        "review_count"
                    ]
                    or 0
                ),

                "rejected_count": int(
                    recommendation_summary[
                        "rejected_count"
                    ]
                    or 0
                ),

                "average_measured_gain": round(
                    float(
                        recommendation_summary[
                            "average_measured_gain"
                        ]
                        or 0
                    ),
                    2,
                ),

                "median_measured_gain": round(
                    float(
                        recommendation_summary[
                            "median_measured_gain"
                        ]
                        or 0
                    ),
                    2,
                ),

                "average_confidence": round(
                    float(
                        recommendation_summary[
                            "average_confidence"
                        ]
                        or 0
                    ),
                    4,
                ),
            },

            "latest_recommendation": (
                latest_recommendation
            ),

            "recent_optimizations": (
                recent_optimizations
            ),
        }

    except HTTPException:
        raise

    except SQLAlchemyError as exc:
        print(
            "OVERVIEW ERROR:",
            repr(exc),
        )

        raise HTTPException(
            status_code=(
                status.HTTP_500_INTERNAL_SERVER_ERROR
            ),
            detail=(
                "Failed to load overview data."
            ),
        ) from exc