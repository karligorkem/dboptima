from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class MLTrainingSample(Base):
    __tablename__ = "ml_training_samples"

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
    )

    query_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("queries.id"),
        nullable=False,
        index=True,
    )

    recommendation_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("recommendations.id"),
        nullable=True,
        index=True,
    )

    total_calls: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        default=0,
    )

    latency_sample_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
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

    filter_column_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    index_column_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
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

    historical_success_rate: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    historical_avg_improvement: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    historical_avg_confidence: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    decision_confidence: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    decision_status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )