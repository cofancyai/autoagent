"""Execution Project model - Tracks complete business creation projects"""

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import Column, DateTime, ForeignKey, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from app.database import Base


class ExecutionProject(Base):
    """Business execution project"""

    __tablename__ = "execution_projects"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(
        UUID(as_uuid=True),
        ForeignKey("sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Project details
    project_name = Column(String(255), nullable=False)
    business_type = Column(String(100), nullable=False)  # 'saas', 'ecommerce', 'agency', etc.
    description = Column(Text, nullable=True)

    # Financial tracking
    total_budget = Column(Numeric(10, 2), nullable=True)
    spent_amount = Column(Numeric(10, 2), default=0.0, nullable=False)

    # Status tracking
    status = Column(
        String(50), default="planning", nullable=False
    )  # 'planning', 'in_progress', 'completed', 'failed', 'paused'
    progress_percentage = Column(Numeric(5, 2), default=0.0, nullable=False)

    # Timeline
    estimated_completion_date = Column(DateTime, nullable=True)
    actual_completion_date = Column(DateTime, nullable=True)

    # Metadata
    requirements = Column(JSONB, nullable=True)  # Original user requirements
    execution_plan = Column(JSONB, nullable=True)  # AI-generated execution plan
    results = Column(JSONB, nullable=True)  # Final deliverables and outcomes

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    session = relationship("Session", back_populates="execution_projects")
    tasks = relationship("ExecutionTask", back_populates="project", cascade="all, delete-orphan")
    assets = relationship("CreatedAsset", back_populates="project", cascade="all, delete-orphan")
    integrations = relationship("ServiceIntegration", back_populates="project", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<ExecutionProject(id={self.id}, name={self.project_name}, status={self.status})>"
