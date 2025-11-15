"""Approval models"""

import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from app.database import Base


class ApprovalCheckpoint(Base):
    """Approval checkpoint for user decisions"""

    __tablename__ = "approval_checkpoints"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(
        UUID(as_uuid=True),
        ForeignKey("sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    thinking_process_id = Column(
        UUID(as_uuid=True), ForeignKey("thinking_processes.id"), nullable=True, index=True
    )
    checkpoint_type = Column(
        String(100), nullable=False
    )  # 'tech_stack', 'architecture', 'schema', etc.
    decision_needed = Column(Text, nullable=False)
    options = Column(JSONB, nullable=False)  # Array of options with pros/cons
    recommended_option = Column(Integer, nullable=True)
    status = Column(
        String(20), default="pending", nullable=False, index=True
    )  # 'pending', 'approved', 'rejected', 'modified'
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    session = relationship("Session", back_populates="approval_checkpoints")
    thinking_process = relationship("ThinkingProcess", back_populates="approval_checkpoints")
    decision = relationship(
        "Decision",
        back_populates="approval_checkpoint",
        uselist=False,
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return (
            f"<ApprovalCheckpoint(id={self.id}, type={self.checkpoint_type}, status={self.status})>"
        )


class Decision(Base):
    """User's decision on an approval checkpoint"""

    __tablename__ = "decisions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    approval_checkpoint_id = Column(
        UUID(as_uuid=True),
        ForeignKey("approval_checkpoints.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    selected_option = Column(Integer, nullable=False)
    modifications = Column(Text, nullable=True)  # User modifications to the option
    reasoning = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    approval_checkpoint = relationship("ApprovalCheckpoint", back_populates="decision")

    def __repr__(self) -> str:
        return f"<Decision(id={self.id}, selected_option={self.selected_option})>"
