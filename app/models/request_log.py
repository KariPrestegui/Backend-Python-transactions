import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, Text, DateTime
from sqlalchemy.dialects.postgresql import UUID

from app.db.database import Base


class RequestLog(Base):
    __tablename__ = "request_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    request_text = Column(Text, nullable=False)
    response_text = Column(Text, nullable=False)
    model_used = Column(String(100), nullable=False, default="simulated")
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    def __repr__(self) -> str:
        return (
            f"<RequestLog(id={self.id}, model={self.model_used}, "
            f"created_at={self.created_at})>"
        )
