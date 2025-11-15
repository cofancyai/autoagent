"""Thinking Process model"""

import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from app.database import Base


class ThinkingProcess(Base):
    """AI reasoning/thinking process"""

    __tablename__ = "thinking_processes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(
        UUID(as_uuid=True),
        ForeignKey("sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    goal_id = Column(UUID(as_uuid=True), ForeignKey("goals.id"), nullable=True, index=True)
    process_type = Column(
        String(100), nullable=True
    )  # 'chain_of_thought', 'tree_of_thought', 'react'
    input_data = Column(JSONB, nullable=True)
    reasoning_steps = Column(JSONB, nullable=True)  # Array of thinking steps
    output_data = Column(JSONB, nullable=True)
    status = Column(String(50), default="running", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)

    # Relationships
    session = relationship("Session", back_populates="thinking_processes")
    goal = relationship("Goal", back_populates="thinking_processes")
    approval_checkpoints = relationship("ApprovalCheckpoint", back_populates="thinking_process")
    llm_api_calls = relationship("LLMAPICall", back_populates="thinking_process")

    def __repr__(self) -> str:
        return f"<ThinkingProcess(id={self.id}, type={self.process_type}, status={self.status})>"
