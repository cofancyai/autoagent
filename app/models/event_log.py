"""Event Log model"""

import uuid
from datetime import datetime

from sqlalchemy import BigInteger, Column, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB, UUID

from app.database import Base


class EventLog(Base):
    """Complete audit trail of all events"""

    __tablename__ = "event_log"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    event_id = Column(
        UUID(as_uuid=True), unique=True, nullable=False, default=uuid.uuid4, index=True
    )
    session_id = Column(UUID(as_uuid=True), ForeignKey("sessions.id"), nullable=True, index=True)
    entity_type = Column(
        String(50), nullable=True, index=True
    )  # 'session', 'goal', 'approval', 'thinking_process'
    entity_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    event_type = Column(String(100), nullable=False, index=True)
    event_data = Column(JSONB, nullable=False)
    actor_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )  # Who triggered the event
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    def __repr__(self) -> str:
        return f"<EventLog(id={self.id}, event_type={self.event_type}, entity_type={self.entity_type})>"
