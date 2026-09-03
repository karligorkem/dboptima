from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Float, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class QueryPlan(Base):
    __tablename__ = "query_plans"

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
    )

    query_id: Mapped[int] = mapped_column(
        ForeignKey("queries.id"),
        nullable=False,
        index=True,
    )

    plan_json: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
    )

    total_cost: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    plan_rows: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )