import hashlib
import math
import re
from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ml.v2_feature_extractor import build_v2_features
from app.models.ml_training_sample import MLTrainingSample
from app.models.ml_training_sample_v2 import MLTrainingSampleV2
from app.models.query import Query
from app.models.query_execution_sample import QueryExecutionSample
from app.models.query_plan import QueryPlan
from app.models.recommendation import Recommendation


STRING_LITERAL_PATTERN = re.compile(
    r"'(?:''|[^'])*'"
)

NUMBER_LITERAL_PATTERN = re.compile(
    r"(?<![A-Za-z0-9_])"
    r"-?\d+(?:\.\d+)?"
    r"(?![A-Za-z0-9_])"
)

BOOLEAN_LITERAL_PATTERN = re.compile(
    r"\b(TRUE|FALSE)\b",
    re.IGNORECASE,
)

NULL_LITERAL_PATTERN = re.compile(
    r"\bNULL\b",
    re.IGNORECASE,
)

IN_LIST_PATTERN = re.compile(
    r"\bIN\s*\([^()]*\)",
    re.IGNORECASE,
)

WHITESPACE_PATTERN = re.compile(
    r"\s+"
)


def normalize_query(
    query: str,
) -> str:
    return WHITESPACE_PATTERN.sub(
        " ",
        query.strip(),
    )


def fingerprint_query(
    query: str,
) -> str:
    normalized = normalize_query(
        query
    )

    fingerprint = normalized

    fingerprint = STRING_LITERAL_PATTERN.sub(
        "?",
        fingerprint,
    )

    fingerprint = IN_LIST_PATTERN.sub(
        "IN (?)",
        fingerprint,
    )

    fingerprint = NUMBER_LITERAL_PATTERN.sub(
        "?",
        fingerprint,
    )

    fingerprint = BOOLEAN_LITERAL_PATTERN.sub(
        "?",
        fingerprint,
    )

    fingerprint = NULL_LITERAL_PATTERN.sub(
        "?",
        fingerprint,
    )

    fingerprint = WHITESPACE_PATTERN.sub(
        " ",
        fingerprint,
    ).strip()

    return fingerprint


def build_query_hash(
    query: str,
) -> str:
    fingerprint = fingerprint_query(
        query
    )

    return hashlib.sha256(
        fingerprint.encode(
            "utf-8"
        )
    ).hexdigest()


def calculate_p95(
    values: list[float],
) -> float | None:
    if not values:
        return None

    sorted_values = sorted(
        values
    )

    index = (
        math.ceil(
            0.95 * len(sorted_values)
        )
        - 1
    )

    index = max(
        0,
        min(
            index,
            len(sorted_values) - 1,
        ),
    )

    return sorted_values[
        index
    ]


def refresh_query_latency_stats(
    db: Session,
    query_record: Query,
) -> None:
    samples = db.scalars(
        select(
            QueryExecutionSample.execution_time_ms
        ).where(
            QueryExecutionSample.query_id
            == query_record.id
        )
    ).all()

    values = [
        float(value)
        for value in samples
    ]

    if not values:
        query_record.min_latency_ms = None
        query_record.max_latency_ms = None
        query_record.p95_latency_ms = None
        return

    query_record.min_latency_ms = min(
        values
    )

    query_record.max_latency_ms = max(
        values
    )

    query_record.p95_latency_ms = (
        calculate_p95(
            values
        )
    )


def get_latency_sample_count(
    db: Session,
    query_id: int,
) -> int:
    sample_ids = db.scalars(
        select(
            QueryExecutionSample.id
        ).where(
            QueryExecutionSample.query_id
            == query_id
        )
    ).all()

    return len(
        sample_ids
    )


def get_recommendation_history_stats(
    db: Session,
    query_id: int,
) -> dict[str, float | int | None]:
    recommendations = db.scalars(
        select(
            Recommendation
        )
        .where(
            Recommendation.query_id
            == query_id
        )
        .order_by(
            Recommendation.created_at.asc(),
            Recommendation.id.asc(),
        )
    ).all()

    if not recommendations:
        return {
            "total_runs": 0,
            "recommended_runs": 0,
            "success_rate": None,
            "avg_improvement_percent": None,
            "best_improvement_percent": None,
            "worst_improvement_percent": None,
            "avg_confidence": None,
            "latest_improvement_percent": None,
        }

    improvements = [
        float(
            item.improvement_percent
        )
        for item in recommendations
        if item.improvement_percent
        is not None
    ]

    confidences = [
        float(
            item.confidence
        )
        for item in recommendations
        if item.confidence
        is not None
    ]

    recommended_runs = sum(
        1
        for item in recommendations
        if item.status == "RECOMMENDED"
    )

    total_runs = len(
        recommendations
    )

    success_rate = (
        recommended_runs
        / total_runs
        * 100.0
        if total_runs > 0
        else None
    )

    latest = (
        recommendations[-1]
    )

    return {
        "total_runs": total_runs,
        "recommended_runs": recommended_runs,
        "success_rate": (
            round(
                success_rate,
                2,
            )
            if success_rate
            is not None
            else None
        ),
        "avg_improvement_percent": (
            round(
                sum(improvements)
                / len(improvements),
                2,
            )
            if improvements
            else None
        ),
        "best_improvement_percent": (
            round(
                max(improvements),
                2,
            )
            if improvements
            else None
        ),
        "worst_improvement_percent": (
            round(
                min(improvements),
                2,
            )
            if improvements
            else None
        ),
        "avg_confidence": (
            round(
                sum(confidences)
                / len(confidences),
                4,
            )
            if confidences
            else None
        ),
        "latest_improvement_percent": (
            round(
                float(
                    latest.improvement_percent
                ),
                2,
            )
            if latest.improvement_percent
            is not None
            else None
        ),
    }


def get_query_evaluation_context(
    db: Session,
    database_id: int,
    query_text: str,
) -> dict[str, Any]:
    """
    ML inference ve recommendation evaluator için
    mevcut query geçmişini hazırlar.

    Önemli:
    Bu fonksiyon benchmark yapılmadan önce çağrılır.
    Dolayısıyla current benchmark sonucunu feature olarak kullanmaz.
    """

    query_hash = build_query_hash(
        query_text
    )

    query_record = db.scalar(
        select(
            Query
        ).where(
            Query.database_id
            == database_id,
            Query.query_hash
            == query_hash,
        )
    )

    # ---------------------------------------------------------
    # QUERY DAHA ÖNCE GÖRÜLMEDİYSE
    # ---------------------------------------------------------

    if query_record is None:
        return {
            "query_id": None,
            "latency_sample_count": 0,
            "query_stats": {
                "total_calls": 0,
                "avg_latency_ms": None,
                "min_latency_ms": None,
                "max_latency_ms": None,
                "p95_latency_ms": None,
            },
            "recommendation_history": {
                "total_runs": 0,
                "recommended_runs": 0,
                "success_rate": None,
                "avg_improvement_percent": None,
                "avg_improvement": None,
                "best_improvement_percent": None,
                "worst_improvement_percent": None,
                "avg_confidence": None,
                "latest_improvement_percent": None,
            },
        }

    # ---------------------------------------------------------
    # LATENCY SAMPLES
    #
    # Query tablosundaki eski/null değerleri kullanmak yerine
    # gerçek execution sample kayıtlarından tekrar hesaplıyoruz.
    # ---------------------------------------------------------

    raw_samples = db.scalars(
        select(
            QueryExecutionSample.execution_time_ms
        )
        .where(
            QueryExecutionSample.query_id
            == query_record.id
        )
        .order_by(
            QueryExecutionSample.created_at.asc()
        )
    ).all()

    latency_values = [
        float(value)
        for value in raw_samples
        if value is not None
    ]

    latency_sample_count = len(
        latency_values
    )

    # ---------------------------------------------------------
    # LATENCY STATS
    # ---------------------------------------------------------

    if latency_values:
        avg_latency_ms = (
            sum(latency_values)
            / len(latency_values)
        )

        min_latency_ms = min(
            latency_values
        )

        max_latency_ms = max(
            latency_values
        )

        p95_latency_ms = calculate_p95(
            latency_values
        )

    else:
        avg_latency_ms = None
        min_latency_ms = None
        max_latency_ms = None
        p95_latency_ms = None

    # ---------------------------------------------------------
    # TOTAL CALLS
    #
    # Eski kayıtlarda total_calls NULL olabiliyorsa sample count
    # güvenli fallback olur.
    # ---------------------------------------------------------

    stored_total_calls = (
        query_record.total_calls
        or 0
    )

    total_calls = max(
        int(stored_total_calls),
        latency_sample_count,
    )

    # ---------------------------------------------------------
    # QUERY TABLOSUNU DA SENKRONIZE ET
    # ---------------------------------------------------------

    query_record.total_calls = (
        total_calls
    )

    query_record.avg_latency_ms = (
        avg_latency_ms
    )

    query_record.min_latency_ms = (
        min_latency_ms
    )

    query_record.max_latency_ms = (
        max_latency_ms
    )

    query_record.p95_latency_ms = (
        p95_latency_ms
    )

    db.flush()

    # ---------------------------------------------------------
    # RECOMMENDATION HISTORY
    # ---------------------------------------------------------

    recommendation_history = (
        get_recommendation_history_stats(
            db=db,
            query_id=query_record.id,
        )
    )

    if recommendation_history is None:
        recommendation_history = {
            "total_runs": 0,
            "recommended_runs": 0,
            "success_rate": None,
            "avg_improvement_percent": None,
            "best_improvement_percent": None,
            "worst_improvement_percent": None,
            "avg_confidence": None,
            "latest_improvement_percent": None,
        }

    # ML predictor tarafında kullandığımız isimle
    # geriye uyumlu alias oluşturuyoruz.
    recommendation_history[
        "avg_improvement"
    ] = recommendation_history.get(
        "avg_improvement_percent"
    )

    # ---------------------------------------------------------
    # FINAL CONTEXT
    # ---------------------------------------------------------

    return {
        "query_id": (
            query_record.id
        ),
        "latency_sample_count": (
            latency_sample_count
        ),
        "query_stats": {
            "total_calls": (
                total_calls
            ),
            "avg_latency_ms": (
                round(
                    avg_latency_ms,
                    3,
                )
                if avg_latency_ms
                is not None
                else None
            ),
            "min_latency_ms": (
                round(
                    min_latency_ms,
                    3,
                )
                if min_latency_ms
                is not None
                else None
            ),
            "max_latency_ms": (
                round(
                    max_latency_ms,
                    3,
                )
                if max_latency_ms
                is not None
                else None
            ),
            "p95_latency_ms": (
                round(
                    p95_latency_ms,
                    3,
                )
                if p95_latency_ms
                is not None
                else None
            ),
        },
        "recommendation_history": (
            recommendation_history
        ),
    }


def get_or_create_query_record(
    db: Session,
    database_id: int,
    query_text: str,
    execution_time_ms: float | None,
) -> Query:
    normalized_query = normalize_query(
        query_text
    )

    query_hash = build_query_hash(
        normalized_query
    )

    existing_query = db.scalar(
        select(
            Query
        ).where(
            Query.database_id
            == database_id,
            Query.query_hash
            == query_hash,
        )
    )

    now = datetime.utcnow()

    if existing_query is None:
        query_record = Query(
            database_id=database_id,
            query_hash=query_hash,
            normalized_query=normalized_query,
            total_calls=1,
            avg_latency_ms=(
                execution_time_ms
                if execution_time_ms
                is not None
                else 0.0
            ),
            min_latency_ms=execution_time_ms,
            max_latency_ms=execution_time_ms,
            p95_latency_ms=execution_time_ms,
            first_seen=now,
            last_seen=now,
        )

        db.add(
            query_record
        )

        db.flush()

        if execution_time_ms is not None:
            sample = QueryExecutionSample(
                query_id=query_record.id,
                execution_time_ms=(
                    execution_time_ms
                ),
            )

            db.add(
                sample
            )

            db.flush()

        return query_record

    old_total_calls = (
        existing_query.total_calls
        or 0
    )

    old_average = (
        existing_query.avg_latency_ms
        or 0.0
    )

    new_total_calls = (
        old_total_calls
        + 1
    )

    if execution_time_ms is not None:
        if old_total_calls == 0:
            new_average = (
                execution_time_ms
            )
        else:
            new_average = (
                (
                    old_average
                    * old_total_calls
                )
                + execution_time_ms
            ) / new_total_calls

        existing_query.avg_latency_ms = (
            new_average
        )

        sample = QueryExecutionSample(
            query_id=existing_query.id,
            execution_time_ms=(
                execution_time_ms
            ),
        )

        db.add(
            sample
        )

        db.flush()

    existing_query.total_calls = (
        new_total_calls
    )

    existing_query.last_seen = (
        now
    )

    refresh_query_latency_stats(
        db=db,
        query_record=(
            existing_query
        ),
    )

    db.flush()

    return existing_query


def persist_optimization_result(
    db: Session,
    database_id: int,
    query_text: str,
    explain_result: dict[str, Any],
    benchmark_results: list[dict[str, Any]],
) -> dict[str, Any]:
    execution_time_ms = explain_result.get(
        "execution_time"
    )

    query_record = get_or_create_query_record(
        db=db,
        database_id=database_id,
        query_text=query_text,
        execution_time_ms=execution_time_ms,
    )

    # Current request icindeki recommendation'lar kaydedilmeden once
    # history snapshot alinir. V1 ve V2 ayni temiz history'yi kullanir.
    historical_context = get_recommendation_history_stats(
        db=db,
        query_id=query_record.id,
    )

    plan = explain_result.get(
        "plan",
        {},
    )

    plan_record = QueryPlan(
        query_id=query_record.id,
        plan_json=plan,
        total_cost=plan.get(
            "Total Cost"
        ),
        plan_rows=plan.get(
            "Plan Rows"
        ),
    )

    db.add(
        plan_record
    )
    db.flush()

    recommendation_records: list[Recommendation] = []
    ml_training_records: list[MLTrainingSample] = []
    ml_training_v2_records: list[MLTrainingSampleV2] = []

    latency_sample_count = get_latency_sample_count(
        db=db,
        query_id=query_record.id,
    )

    for item in benchmark_results:
        recommendation = item[
            "recommendation"
        ]
        benchmark = item[
            "benchmark"
        ]
        decision = item[
            "decision"
        ]

        recommendation_record = Recommendation(
            query_id=query_record.id,
            recommendation_type=recommendation[
                "type"
            ],
            sql_command=recommendation[
                "sql_command"
            ],
            reason=decision[
                "reason"
            ],
            confidence=decision[
                "confidence"
            ],
            status=decision[
                "status"
            ],
            before_ms=benchmark.get(
                "before_ms"
            ),
            after_ms=benchmark.get(
                "after_ms"
            ),
            improvement_ms=benchmark.get(
                "improvement_ms"
            ),
            improvement_percent=benchmark.get(
                "improvement_percent"
            ),
        )

        db.add(
            recommendation_record
        )
        # recommendation_id icin flush; commit degildir.
        db.flush()

        recommendation_records.append(
            recommendation_record
        )

        candidate_columns = (
            recommendation.get(
                "columns",
                [],
            )
            or []
        )

        # V1'in mevcut training semantics'ini koruyoruz.
        filter_columns = recommendation.get(
            "filter_columns"
        )
        if filter_columns is None:
            filter_columns = candidate_columns

        # -----------------------------
        # V1 training sample
        # -----------------------------
        ml_sample = MLTrainingSample(
            query_id=query_record.id,
            recommendation_id=recommendation_record.id,
            total_calls=query_record.total_calls,
            latency_sample_count=latency_sample_count,
            avg_latency_ms=query_record.avg_latency_ms,
            min_latency_ms=query_record.min_latency_ms,
            max_latency_ms=query_record.max_latency_ms,
            p95_latency_ms=query_record.p95_latency_ms,
            plan_total_cost=plan.get(
                "Total Cost"
            ),
            plan_rows=plan.get(
                "Plan Rows"
            ),
            filter_column_count=len(
                filter_columns
            ),
            index_column_count=len(
                candidate_columns
            ),
            benchmark_before_ms=benchmark.get(
                "before_ms"
            ),
            benchmark_after_ms=benchmark.get(
                "after_ms"
            ),
            improvement_percent=benchmark.get(
                "improvement_percent"
            ),
            benchmark_stability=decision.get(
                "benchmark_stability"
            ),
            historical_success_rate=historical_context.get(
                "success_rate"
            ),
            historical_avg_improvement=historical_context.get(
                "avg_improvement_percent"
            ),
            historical_avg_confidence=historical_context.get(
                "avg_confidence"
            ),
            decision_confidence=decision.get(
                "confidence"
            ),
            decision_status=decision.get(
                "status",
                "UNKNOWN",
            ),
        )

        db.add(
            ml_sample
        )
        ml_training_records.append(
            ml_sample
        )

        # -----------------------------
        # V2 feature extraction
        # -----------------------------
        v2_features = build_v2_features(
            query=query_text,
            explain_result=explain_result,
            recommendation=recommendation,
        )

        # -----------------------------
        # V2 training sample
        # -----------------------------
        ml_sample_v2 = MLTrainingSampleV2(
            query_id=query_record.id,
            recommendation_id=recommendation_record.id,
            total_calls=query_record.total_calls,
            latency_sample_count=latency_sample_count,
            avg_latency_ms=query_record.avg_latency_ms,
            min_latency_ms=query_record.min_latency_ms,
            max_latency_ms=query_record.max_latency_ms,
            p95_latency_ms=query_record.p95_latency_ms,
            plan_total_cost=plan.get(
                "Total Cost"
            ),
            plan_rows=plan.get(
                "Plan Rows"
            ),
            seq_scan_count=v2_features.get(
                "seq_scan_count"
            ),
            actual_rows=v2_features.get(
                "actual_rows"
            ),
            rows_removed_by_filter=v2_features.get(
                "rows_removed_by_filter"
            ),
            actual_total_time_ms=v2_features.get(
                "actual_total_time_ms"
            ),
            actual_loops=v2_features.get(
                "actual_loops"
            ),
            scan_selectivity_ratio=v2_features.get(
                "scan_selectivity_ratio"
            ),
            removed_to_returned_ratio=v2_features.get(
                "removed_to_returned_ratio"
            ),
            equality_filter_count=v2_features.get(
                "equality_filter_count"
            ),
            range_filter_count=v2_features.get(
                "range_filter_count"
            ),
            like_filter_count=v2_features.get(
                "like_filter_count"
            ),
            has_order_by=v2_features.get(
                "has_order_by"
            ),
            has_limit=v2_features.get(
                "has_limit"
            ),
            candidate_column_count=v2_features.get(
                "candidate_column_count_v2"
            ),
            candidate_has_order_column=v2_features.get(
                "candidate_has_order_column"
            ),
            source_actual_rows=v2_features.get(
                "source_actual_rows"
            ),
            source_rows_removed_by_filter=v2_features.get(
                "source_rows_removed_by_filter"
            ),
            historical_success_rate=historical_context.get(
                "success_rate"
            ),
            historical_avg_improvement=historical_context.get(
                "avg_improvement_percent"
            ),
            benchmark_before_ms=benchmark.get(
                "before_ms"
            ),
            benchmark_after_ms=benchmark.get(
                "after_ms"
            ),
            improvement_percent=benchmark.get(
                "improvement_percent"
            ),
            benchmark_stability=decision.get(
                "benchmark_stability"
            ),
            decision_confidence=decision.get(
                "confidence"
            ),
            decision_status=decision.get(
                "status",
                "UNKNOWN",
            ),
        )

        db.add(
            ml_sample_v2
        )
        ml_training_v2_records.append(
            ml_sample_v2
        )

    # Plan + Recommendation + V1 + V2 tek transaction.
    db.commit()

    db.refresh(
        query_record
    )

    for record in recommendation_records:
        db.refresh(
            record
        )

    for record in ml_training_records:
        db.refresh(
            record
        )

    for record in ml_training_v2_records:
        db.refresh(
            record
        )

    latency_sample_count = get_latency_sample_count(
        db=db,
        query_id=query_record.id,
    )

    # Post-run history sadece response icindir; training feature degildir.
    recommendation_history = get_recommendation_history_stats(
        db=db,
        query_id=query_record.id,
    )

    return {
        "query_id": query_record.id,
        "query_total_calls": query_record.total_calls,
        "query_latency_sample_count": latency_sample_count,
        "query_avg_latency_ms": (
            round(
                query_record.avg_latency_ms,
                3,
            )
            if query_record.avg_latency_ms is not None
            else None
        ),
        "query_min_latency_ms": (
            round(
                query_record.min_latency_ms,
                3,
            )
            if query_record.min_latency_ms is not None
            else None
        ),
        "query_max_latency_ms": (
            round(
                query_record.max_latency_ms,
                3,
            )
            if query_record.max_latency_ms is not None
            else None
        ),
        "query_p95_latency_ms": (
            round(
                query_record.p95_latency_ms,
                3,
            )
            if query_record.p95_latency_ms is not None
            else None
        ),
        "query_fingerprint": fingerprint_query(
            query_text
        ),
        "recommendation_history": recommendation_history,
        "recommendation_ids": [
            record.id
            for record in recommendation_records
        ],
        "ml_training_sample_ids": [
            record.id
            for record in ml_training_records
        ],
        "ml_training_sample_v2_ids": [
            record.id
            for record in ml_training_v2_records
        ],
    }

