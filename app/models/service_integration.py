"""Service Integration model - Tracks external service connections"""

import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from app.database import Base


class ServiceIntegration(Base):
    """External service integration for a project"""

    __tablename__ = "service_integrations"

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

    # Service details
    service_name = Column(String(100), nullable=False)  # 'webflow', 'stripe', 'mailchimp', etc.
    service_category = Column(
        String(50), nullable=False
    )  # 'website', 'payment', 'email', 'social_media', 'legal', 'analytics'

    # Connection details
    status = Column(
        String(50), default="pending", nullable=False
    )  # 'pending', 'connected', 'active', 'failed', 'disconnected'
    api_key = Column(Text, nullable=True)  # Encrypted in production
    api_credentials = Column(JSONB, nullable=True)  # Additional credentials (encrypted)

    # Configuration
    config = Column(JSONB, nullable=True)  # Service-specific configuration
    webhooks = Column(JSONB, nullable=True)  # Webhook URLs and configurations

    # Usage tracking
    last_used_at = Column(DateTime, nullable=True)
    usage_stats = Column(JSONB, nullable=True)  # API calls, costs, quotas

    # Error handling
    error_message = Column(Text, nullable=True)
    retry_count = Column(String(50), default="0", nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    project = relationship("ExecutionProject", back_populates="integrations")
    session = relationship("Session", back_populates="service_integrations")

    def __repr__(self) -> str:
        return f"<ServiceIntegration(id={self.id}, service={self.service_name}, status={self.status})>"
