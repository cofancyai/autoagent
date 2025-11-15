"""Execution Task model - Individual tasks within execution projects"""

import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from app.database import Base


class ExecutionTask(Base):
    """Individual task within an execution project"""

    __tablename__ = "execution_tasks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(
        UUID(as_uuid=True),
        ForeignKey("execution_projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    session_id = Column(
        UUID(as_uuid=True),
        ForeignKey("sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Task details
    task_name = Column(String(255), nullable=False)
    task_type = Column(
        String(100), nullable=False
    )  # 'website', 'mobile_app', 'legal', 'branding', 'social_media', 'payment'
    description = Column(Text, nullable=True)

    # Agent assignment
    assigned_agent = Column(String(100), nullable=True)  # Which execution agent handles this

    # Status tracking
    status = Column(
        String(50), default="pending", nullable=False
    )  # 'pending', 'in_progress', 'completed', 'failed', 'blocked'
    progress_percentage = Column(Integer, default=0, nullable=False)

    # Priority and dependencies
    priority = Column(Integer, default=0, nullable=False)
    dependencies = Column(JSONB, nullable=True)  # List of task IDs this depends on
    blocking_tasks = Column(JSONB, nullable=True)  # List of task IDs blocked by this

    # Execution details
    task_config = Column(JSONB, nullable=True)  # Task-specific configuration
    execution_logs = Column(JSONB, nullable=True)  # Detailed execution logs
    error_message = Column(Text, nullable=True)

    # Timeline
    estimated_duration_hours = Column(Integer, nullable=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    project = relationship("ExecutionProject", back_populates="tasks")
    session = relationship("Session", back_populates="execution_tasks")
    assets = relationship("CreatedAsset", back_populates="task", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<ExecutionTask(id={self.id}, name={self.task_name}, type={self.task_type}, status={self.status})>"
