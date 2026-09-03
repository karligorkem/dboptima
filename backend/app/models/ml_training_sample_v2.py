from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class MLTrainingSampleV2(Base):
    __tablename__ = "ml_training_samples_v2"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    query_id: Mapped[int] = mapped_column(
        ForeignKey(
            "queries.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    recommendation_id: Mapped[int] = mapped_column(
        ForeignKey(
            "recommendations.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    total_calls: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    latency_sample_count: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    avg_latency_ms: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    min_latency_ms: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    max_latency_ms: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    p95_latency_ms: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    plan_total_cost: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    plan_rows: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    seq_scan_count: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    actual_rows: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    rows_removed_by_filter: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    actual_total_time_ms: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    actual_loops: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    scan_selectivity_ratio: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    removed_to_returned_ratio: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    equality_filter_count: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    range_filter_count: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    like_filter_count: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    has_order_by: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    has_limit: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    candidate_column_count: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    candidate_has_order_column: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    source_actual_rows: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    source_rows_removed_by_filter: Mapped[
        float | None
    ] = mapped_column(
        Float,
        nullable=True,
    )

    historical_success_rate: Mapped[
        float | None
    ] = mapped_column(
        Float,
        nullable=True,
    )

    historical_avg_improvement: Mapped[
        float | None
    ] = mapped_column(
        Float,
        nullable=True,
    )

    benchmark_before_ms: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    benchmark_after_ms: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    improvement_percent: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    benchmark_stability: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    decision_confidence: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    decision_status: Mapped[str | None] = mapped_column(
        String(30),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )