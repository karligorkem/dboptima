from __future__ import annotations
from app.core.query_safety import validate_read_only_query

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import create_engine, select, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.analyzers.plan_analyzer import find_sequential_scans
from app.analyzers.recommendation_evaluator import evaluate_benchmark
from app.benchmark.index_benchmark import benchmark_index_candidate
from app.collectors.explain_collector import collect_explain_plan
from app.db.dependencies import get_db
from app.ml.candidate_predictor import predict_candidate
from app.models.database_connection import DatabaseConnection
from app.recommenders.index_advisor import generate_index_recommendations
from app.schemas.database_connection import (
    DatabaseConnectionCreate,
    DatabaseConnectionResponse,
)
from app.services.optimization_service import (
    get_query_evaluation_context,
    persist_optimization_result,
)


router = APIRouter(
    prefix="/api/databases",
    tags=["databases"],
)


# ============================================================
# REQUEST SCHEMAS
# ============================================================


class ExplainRequest(BaseModel):
    query: str = Field(min_length=1)


class BenchmarkRequest(BaseModel):
    query: str = Field(min_length=1)
    create_index_sql: str = Field(min_length=1)
    index_name: str = Field(min_length=1)
    schema_name: str = Field(
        default="public",
        min_length=1,
    )


# ============================================================
# DATABASE HELPERS
# ============================================================


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


def get_database_or_404(
    database_id: int,
    db: Session,
) -> DatabaseConnection:
    connection = db.get(
        DatabaseConnection,
        database_id,
    )

    if connection is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Database connection not found.",
        )

    return connection



# ============================================================
# CREATE DATABASE CONNECTION
# ============================================================


@router.post(
    "",
    response_model=DatabaseConnectionResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_database_connection(
    payload: DatabaseConnectionCreate,
    db: Session = Depends(get_db),
) -> DatabaseConnection:
    connection = DatabaseConnection(
        name=payload.name,
        host=payload.host,
        port=payload.port,
        database_name=payload.database_name,
        username=payload.username,
        password=payload.password,
    )

    db.add(connection)
    db.commit()
    db.refresh(connection)

    return connection


# ============================================================
# LIST DATABASE CONNECTIONS
# ============================================================


@router.get(
    "",
    response_model=list[DatabaseConnectionResponse],
)
def list_database_connections(
    db: Session = Depends(get_db),
) -> list[DatabaseConnection]:
    statement = select(
        DatabaseConnection
    ).order_by(
        DatabaseConnection.id
    )

    connections = db.scalars(
        statement
    ).all()

    return list(connections)


# ============================================================
# GET DATABASE CONNECTION
# ============================================================


@router.get(
    "/{database_id}",
    response_model=DatabaseConnectionResponse,
)
def get_database_connection(
    database_id: int,
    db: Session = Depends(get_db),
) -> DatabaseConnection:
    return get_database_or_404(
        database_id=database_id,
        db=db,
    )


# ============================================================
# TEST DATABASE CONNECTION
# ============================================================


@router.post(
    "/{database_id}/test"
)
def test_database_connection(
    database_id: int,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    connection = get_database_or_404(
        database_id=database_id,
        db=db,
    )

    engine = create_engine(
        build_target_database_url(
            connection
        ),
        pool_pre_ping=True,
        connect_args={
            "connect_timeout": 5,
        },
    )

    try:
        with engine.connect() as target:
            result = target.execute(
                text(
                    """
                    SELECT
                        current_database() AS database_name,
                        current_user AS username,
                        version() AS version
                    """
                )
            ).mappings().one()

        return {
            "success": True,
            "database_id": connection.id,
            "database_name": result[
                "database_name"
            ],
            "username": result[
                "username"
            ],
            "version": result[
                "version"
            ],
        }

    except SQLAlchemyError as exc:
        print(
            "DATABASE CONNECTION ERROR:",
            repr(exc),
        )

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Database connection failed: "
                f"{exc}"
            ),
        ) from exc

    finally:
        engine.dispose()


# ============================================================
# ANALYZE QUERY
# ============================================================


@router.post(
    "/{database_id}/analyze-query"
)
def analyze_query(
    database_id: int,
    payload: ExplainRequest,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    connection = get_database_or_404(
        database_id=database_id,
        db=db,
    )

    query = validate_read_only_query(
        payload.query
    )

    try:

        # ----------------------------------------------------
        # 1. EXPLAIN ANALYZE
        # ----------------------------------------------------

        explain_result = collect_explain_plan(
            connection=connection,
            query=query,
        )

        plan = explain_result.get(
            "plan",
            {},
        )

        # ----------------------------------------------------
        # 2. FIND SEQUENTIAL SCANS
        # ----------------------------------------------------

        sequential_scans = find_sequential_scans(
            plan
        )

        # ----------------------------------------------------
        # 3. GENERATE INDEX CANDIDATES
        # ----------------------------------------------------

        recommendations = generate_index_recommendations(
            connection=connection,
            sequential_scans=sequential_scans,
            query=query,
        )

        # ----------------------------------------------------
        # 4. RESPONSE
        # ----------------------------------------------------

        return {
            "database_id": database_id,
            "query": query,
            "execution_time_ms": (
                explain_result.get(
                    "execution_time"
                )
            ),
            "planning_time_ms": (
                explain_result.get(
                    "planning_time"
                )
            ),
            "plan": plan,
            "issues": sequential_scans,
            "candidate_count": len(
                recommendations
            ),
            "candidates": recommendations,
        }

    except SQLAlchemyError as exc:
        print(
            "QUERY ANALYSIS ERROR:",
            repr(exc),
        )

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Query analysis failed: "
                f"{exc}"
            ),
        ) from exc

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


# ============================================================
# MANUAL INDEX BENCHMARK
# ============================================================


@router.post(
    "/{database_id}/benchmark-index"
)
def benchmark_index(
    database_id: int,
    payload: BenchmarkRequest,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    connection = get_database_or_404(
        database_id=database_id,
        db=db,
    )

    query = validate_read_only_query(
        payload.query
    )

    try:
        benchmark_result = benchmark_index_candidate(
            connection=connection,
            query=query,
            create_index_sql=(
                payload.create_index_sql
            ),
            index_name=(
                payload.index_name
            ),
            schema_name=(
                payload.schema_name
            ),
        )

        decision = evaluate_benchmark(
            benchmark_result
        )

        return {
            "database_id": database_id,
            "query": query,
            "benchmark": benchmark_result,
            "decision": decision,
        }

    except SQLAlchemyError as exc:
        print(
            "BENCHMARK ERROR:",
            repr(exc),
        )

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Index benchmark failed: "
                f"{exc}"
            ),
        ) from exc

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


# ============================================================
# AUTOMATIC QUERY OPTIMIZATION
# ============================================================


@router.post(
    "/{database_id}/optimize-query"
)
def optimize_query(
    database_id: int,
    payload: ExplainRequest,
    db: Session = Depends(get_db),
) -> dict[str, Any]:

    connection = get_database_or_404(
        database_id=database_id,
        db=db,
    )

    # ========================================================
    # 0. VALIDATE QUERY
    # ========================================================
    # Keep validation outside the broad try/except below so
    # FastAPI HTTPException responses stay as 400 responses.
    query = validate_read_only_query(
        payload.query
    )

    try:
        print(
            "OPTIMIZATION STARTED:",
            query,
        )

        # ====================================================
        # 1. BASELINE EXPLAIN
        # ====================================================

        explain_result = collect_explain_plan(
            connection=connection,
            query=query,
        )

        print(
            "EXPLAIN RESULT:",
            explain_result,
        )

        plan = explain_result.get(
            "plan",
            {},
        )

        # ====================================================
        # 2. PLAN ANALYSIS
        # ====================================================

        sequential_scans = (
            find_sequential_scans(
                plan
            )
        )

        print(
            "SEQUENTIAL SCANS:",
            sequential_scans,
        )

        # ====================================================
        # 3. INDEX CANDIDATE GENERATION
        # ====================================================

        recommendations = (
            generate_index_recommendations(
                connection=connection,
                sequential_scans=(
                    sequential_scans
                ),
                query=query,
            )
        )

        print(
            "INDEX RECOMMENDATIONS:",
            recommendations,
        )

        # ====================================================
        # 4. QUERY HISTORY / EVALUATION CONTEXT
        # ====================================================

        evaluation_context = (
            get_query_evaluation_context(
                db=db,
                database_id=database_id,
                query_text=query,
            )
        )

        # V2 SQL structure features için gerçek SQL'i
        # inference context içine ekliyoruz.
        evaluation_context["query"] = query

        print(
            "EVALUATION CONTEXT:",
            evaluation_context,
        )

        # ====================================================
        # 5. V2 ML PRE-BENCHMARK RANKING
        # ====================================================

        ranked_candidates: list[
            dict[str, Any]
        ] = []

        for recommendation in recommendations:

            ml_prediction = (
                predict_candidate(
                    explain_result=(
                        explain_result
                    ),
                    evaluation_context=(
                        evaluation_context
                    ),
                    recommendation=(
                        recommendation
                    ),
                )
            )

            predicted_improvement = float(
                ml_prediction.get(
                    "predicted_improvement_percent",
                    0.0,
                )
                or 0.0
            )

            ranked_candidates.append(
                {
                    "recommendation": (
                        recommendation
                    ),
                    "ml_prediction": (
                        ml_prediction
                    ),
                    "predicted_improvement_percent": (
                        predicted_improvement
                    ),
                }
            )

        # ----------------------------------------------------
        # En yüksek beklenen kazanç önce benchmark edilir.
        # ----------------------------------------------------

        ranked_candidates.sort(
            key=lambda item: (
                item[
                    "predicted_improvement_percent"
                ]
            ),
            reverse=True,
        )

        print()
        print(
            "V2 ML CANDIDATE RANKING:"
        )

        for rank, item in enumerate(
            ranked_candidates,
            start=1,
        ):

            recommendation = (
                item["recommendation"]
            )

            ml_prediction = (
                item["ml_prediction"]
            )

            print(
                {
                    "rank": rank,
                    "index_name": (
                        recommendation.get(
                            "index_name"
                        )
                    ),
                    "model_version": (
                        ml_prediction.get(
                            "model_version"
                        )
                    ),
                    "predicted_improvement": (
                        ml_prediction.get(
                            "predicted_improvement_percent"
                        )
                    ),
                    "predicted_status": (
                        ml_prediction.get(
                            "predicted_status"
                        )
                    ),
                    "benchmark_priority": (
                        ml_prediction.get(
                            "benchmark_priority"
                        )
                    ),
                }
            )

        # ====================================================
        # 6. BENCHMARK IN V2 RANK ORDER
        # ====================================================

        benchmark_results: list[
            dict[str, Any]
        ] = []

        for rank, ranked_item in enumerate(
            ranked_candidates,
            start=1,
        ):

            recommendation = (
                ranked_item[
                    "recommendation"
                ]
            )

            ml_prediction = (
                ranked_item[
                    "ml_prediction"
                ]
            )

            print()
            print(
                "BENCHMARKING RANKED CANDIDATE:",
                {
                    "rank": rank,
                    "index_name": (
                        recommendation.get(
                            "index_name"
                        )
                    ),
                    "predicted_improvement": (
                        ml_prediction.get(
                            "predicted_improvement_percent"
                        )
                    ),
                    "priority": (
                        ml_prediction.get(
                            "benchmark_priority"
                        )
                    ),
                },
            )

            # ------------------------------------------------
            # 6A. REAL POSTGRESQL BENCHMARK
            # ------------------------------------------------

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

            print(
                "BENCHMARK RESULT:",
                benchmark,
            )

            # ------------------------------------------------
            # 6B. FINAL DETERMINISTIC DECISION
            # ------------------------------------------------

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

            print(
                "BENCHMARK DECISION:",
                decision,
            )

            # ------------------------------------------------
            # 6C. PREDICTION VS ACTUAL
            # ------------------------------------------------

            actual_improvement = float(
                benchmark.get(
                    "improvement_percent",
                    0.0,
                )
                or 0.0
            )

            predicted_improvement = float(
                ml_prediction.get(
                    "predicted_improvement_percent",
                    0.0,
                )
                or 0.0
            )

            prediction_error = abs(
                actual_improvement
                - predicted_improvement
            )

            print(
                "ML VS ACTUAL:",
                {
                    "rank": rank,
                    "model_version": (
                        ml_prediction.get(
                            "model_version"
                        )
                    ),
                    "predicted": (
                        predicted_improvement
                    ),
                    "actual": (
                        actual_improvement
                    ),
                    "absolute_error": (
                        prediction_error
                    ),
                },
            )

            # ------------------------------------------------
            # 6D. COLLECT RESULT
            # ------------------------------------------------

            benchmark_results.append(
                {
                    "ml_rank": rank,

                    "recommendation": (
                        recommendation
                    ),

                    "ml_prediction": (
                        ml_prediction
                    ),

                    "benchmark": (
                        benchmark
                    ),

                    "decision": (
                        decision
                    ),

                    "prediction_error_percent": (
                        round(
                            prediction_error,
                            2,
                        )
                    ),
                }
            )

        # ====================================================
        # 7. ACTUAL RESULT RANK
        # ====================================================

        actual_sorted_results = sorted(
            benchmark_results,
            key=lambda item: float(
                item[
                    "benchmark"
                ].get(
                    "improvement_percent",
                    0.0,
                )
                or 0.0
            ),
            reverse=True,
        )

        for actual_rank, item in enumerate(
            actual_sorted_results,
            start=1,
        ):
            item["actual_rank"] = (
                actual_rank
            )

        # ----------------------------------------------------
        # API'de en iyi GERÇEK sonucu üstte gösteriyoruz.
        #
        # ml_rank ayrıca korunuyor.
        # Böylece:
        #
        # ML ne sıraladı?
        # Gerçek benchmark ne sıraladı?
        #
        # karşılaştırabiliyoruz.
        # ----------------------------------------------------

        benchmark_results = (
            actual_sorted_results
        )

        # ====================================================
        # 8. PERSIST RESULT
        # ====================================================

        persistence = (
            persist_optimization_result(
                db=db,
                database_id=database_id,
                query_text=query,
                explain_result=(
                    explain_result
                ),
                benchmark_results=(
                    benchmark_results
                ),
            )
        )

        print(
            "PERSISTENCE RESULT:",
            persistence,
        )

        # ====================================================
        # 9. RESPONSE
        # ====================================================

        return {
            "database_id": (
                database_id
            ),

            "query": query,

            "ml_model": {
                "version": "v2-final",
                "feature_schema": "v2",
                "ranking_enabled": True,
            },

            "baseline": {
                "execution_time_ms": (
                    explain_result.get(
                        "execution_time"
                    )
                ),
                "planning_time_ms": (
                    explain_result.get(
                        "planning_time"
                    )
                ),
            },

            "issues": (
                sequential_scans
            ),

            "candidate_count": len(
                benchmark_results
            ),

            "evaluation_context": (
                evaluation_context
            ),

            "candidates": (
                benchmark_results
            ),

            "persistence": (
                persistence
            ),
        }

    # ========================================================
    # SQLALCHEMY ERROR
    # ========================================================

    except SQLAlchemyError as exc:

        db.rollback()

        print(
            "OPTIMIZATION ERROR:",
            repr(exc),
        )

        raise HTTPException(
            status_code=(
                status.HTTP_400_BAD_REQUEST
            ),
            detail=(
                "Automatic query optimization "
                f"failed: {exc}"
            ),
        ) from exc

    # ========================================================
    # VALUE ERROR
    # ========================================================

    except ValueError as exc:

        db.rollback()

        print(
            "OPTIMIZATION VALUE ERROR:",
            repr(exc),
        )

        raise HTTPException(
            status_code=(
                status.HTTP_400_BAD_REQUEST
            ),
            detail=str(exc),
        ) from exc

    # ========================================================
    # UNEXPECTED ERROR
    # ========================================================

    except Exception as exc:

        db.rollback()

        print(
            "UNEXPECTED OPTIMIZATION ERROR:",
            repr(exc),
        )

        raise HTTPException(
            status_code=(
                status.HTTP_500_INTERNAL_SERVER_ERROR
            ),
            detail=(
                "Unexpected optimization error: "
                f"{exc}"
            ),
        ) from exc
