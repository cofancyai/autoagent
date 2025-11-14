"""Session model"""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.database import Base


class Session(Base):
    """Conversation session/context"""

    __tablename__ = "sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True)
    title = Column(String(500), nullable=True)
    status = Column(String(50), default="active", nullable=False, index=True)
    context = Column(JSONB, nullable=True)  # Free-form context data
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )

    # Relationships
    user = relationship("User", back_populates="sessions")
    messages = relationship(
        "Message",
        back_populates="session",
        cascade="all, delete-orphan"
    )
    goals = relationship(
        "Goal",
        back_populates="session",
        cascade="all, delete-orphan"
    )
    thinking_processes = relationship(
        "ThinkingProcess",
        back_populates="session",
        cascade="all, delete-orphan"
    )
    approval_checkpoints = relationship(
        "ApprovalCheckpoint",
        back_populates="session",
        cascade="all, delete-orphan"
    )
    execution_logs = relationship(
        "ExecutionLog",
        back_populates="session",
        cascade="all, delete-orphan"
    )
    llm_api_calls = relationship(
        "LLMAPICall",
        back_populates="session",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Session(id={self.id}, title={self.title}, status={self.status})>"
