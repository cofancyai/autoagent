"""Created Asset model - Tracks assets created during project execution"""

import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from app.database import Base


class CreatedAsset(Base):
    """Asset created during project execution"""

    __tablename__ = "created_assets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(
        UUID(as_uuid=True),
        ForeignKey("execution_projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    task_id = Column(
        UUID(as_uuid=True),
        ForeignKey("execution_tasks.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    session_id = Column(
        UUID(as_uuid=True),
        ForeignKey("sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Asset details
    asset_name = Column(String(255), nullable=False)
    asset_type = Column(
        String(100), nullable=False
    )  # 'website', 'mobile_app', 'logo', 'legal_document', 'social_profile', 'payment_gateway'
    description = Column(Text, nullable=True)

    # Access information
    url = Column(Text, nullable=True)  # URL to access the asset (website, social profile, etc.)
    file_path = Column(Text, nullable=True)  # Local file path if applicable
    credentials = Column(JSONB, nullable=True)  # Login credentials (encrypted in production)

    # Metadata
    asset_metadata = Column(JSONB, nullable=True)  # Asset-specific metadata
    deployment_status = Column(
        String(50), default="draft", nullable=False
    )  # 'draft', 'deployed', 'live', 'archived'

    # External references
    external_id = Column(String(255), nullable=True)  # ID in external service
    external_service = Column(String(100), nullable=True)  # Webflow, Stripe, etc.

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    project = relationship("ExecutionProject", back_populates="assets")
    task = relationship("ExecutionTask", back_populates="assets")
    session = relationship("Session", back_populates="created_assets")

    def __repr__(self) -> str:
        return f"<CreatedAsset(id={self.id}, name={self.asset_name}, type={self.asset_type})>"
