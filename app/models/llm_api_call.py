"""LLM API Call model"""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Integer, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class LLMAPICall(Base):
    """Log of LLM API calls for monitoring and cost tracking"""

    __tablename__ = "llm_api_calls"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(
        UUID(as_uuid=True),
        ForeignKey("sessions.id"),
        nullable=True,
        index=True
    )
    thinking_process_id = Column(
        UUID(as_uuid=True),
        ForeignKey("thinking_processes.id"),
        nullable=True,
        index=True
    )
    provider = Column(String(50), nullable=False)  # 'anthropic', 'openai', 'custom'
    model = Column(String(100), nullable=False)
    prompt_tokens = Column(Integer, nullable=True)
    completion_tokens = Column(Integer, nullable=True)
    total_cost = Column(Numeric(10, 6), nullable=True)
    latency_ms = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Relationships
    session = relationship("Session", back_populates="llm_api_calls")
    thinking_process = relationship("ThinkingProcess", back_populates="llm_api_calls")

    def __repr__(self) -> str:
        return f"<LLMAPICall(id={self.id}, provider={self.provider}, model={self.model})>"
