from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class Query(Base):
    __tablename__ = "queries"

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
    )

    database_id: Mapped[int] = mapped_column(
        ForeignKey("database_connections.id"),
        nullable=False,
        index=True,
    )

    query_hash: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        index=True,
    )

    normalized_query: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    total_calls: Mapped[int] = mapped_column(
        BigInteger,
        default=0,
        nullable=False,
    )

    avg_latency_ms: Mapped[float] = mapped_column(
        Float,
        default=0.0,
        nullable=False,
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

    first_seen: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    last_seen: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )