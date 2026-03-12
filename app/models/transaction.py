import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, Float, DateTime, Index, Boolean
from sqlalchemy.dialects.postgresql import UUID

from app.db.database import Base


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String(100), nullable=False, index=True)
    amount = Column(Float, nullable=False)
    type = Column(String(50), nullable=False)
    status = Column(String(20), nullable=False, default="pending")
    idempotency_key = Column(String(255), unique=True, nullable=False, index=True)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    __table_args__ = (Index("ix_transactions_user_status", "user_id", "status"),)

    def __repr__(self) -> str:
        return (
            f"<Transaction(id={self.id}, user_id={self.user_id}, "
            f"amount={self.amount}, status={self.status})>"
        )
