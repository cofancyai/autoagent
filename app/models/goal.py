"""Goal model"""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Integer
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.database import Base


class Goal(Base):
    """Agent goal/task"""

    __tablename__ = "goals"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(
        UUID(as_uuid=True),
        ForeignKey("sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    description = Column(Text, nullable=False)
    status = Column(
        String(50),
        default="pending",
        nullable=False
    )  # 'pending', 'in_progress', 'completed', 'failed'
    priority = Column(Integer, default=0, nullable=False)
    result = Column(JSONB, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )

    # Relationships
    session = relationship("Session", back_populates="goals")
    thinking_processes = relationship(
        "ThinkingProcess",
        back_populates="goal"
    )
    execution_logs = relationship(
        "ExecutionLog",
        back_populates="goal"
    )

    def __repr__(self) -> str:
        return f"<Goal(id={self.id}, description={self.description[:50]}, status={self.status})>"
