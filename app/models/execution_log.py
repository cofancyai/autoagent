"""Execution Log model"""

import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from app.database import Base


class ExecutionLog(Base):
    """Log of executed actions"""

    __tablename__ = "execution_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(
        UUID(as_uuid=True),
        ForeignKey("sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    goal_id = Column(UUID(as_uuid=True), ForeignKey("goals.id"), nullable=True, index=True)
    action = Column(String(200), nullable=False)
    status = Column(String(50), nullable=True)  # 'started', 'completed', 'failed'
    input_data = Column(JSONB, nullable=True)
    output_data = Column(JSONB, nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Relationships
    session = relationship("Session", back_populates="execution_logs")
    goal = relationship("Goal", back_populates="execution_logs")

    def __repr__(self) -> str:
        return f"<ExecutionLog(id={self.id}, action={self.action}, status={self.status})>"
