from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Float, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class QueryExecutionSample(Base):
    __tablename__ = "query_execution_samples"

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

    execution_time_ms: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )