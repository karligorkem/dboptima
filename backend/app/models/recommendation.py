from datetime import datetime

from sqlalchemy import (
    BigInteger,
    DateTime,
    Float,
    ForeignKey,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class Recommendation(Base):
    __tablename__ = "recommendations"

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

    recommendation_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    sql_command: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    reason: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    confidence: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="PENDING",
    )

    before_ms: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    after_ms: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    improvement_ms: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    improvement_percent: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )