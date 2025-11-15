"""Message schemas"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class MessageCreate(BaseModel):
    """Schema for creating a new message"""

    role: str = Field(..., description="Message role: user, assistant, system")
    content: str = Field(..., description="Message content")
    extra_data: Optional[Dict[str, Any]] = Field(None, description="Optional extra data")


class MessageResponse(BaseModel):
    """Schema for message response"""

    id: UUID
    session_id: UUID
    role: str
    content: str
    extra_data: Optional[Dict[str, Any]]
    created_at: datetime

    model_config = {"from_attributes": True}


class MessageListResponse(BaseModel):
    """Schema for message list"""

    messages: List[MessageResponse]
    has_more: bool
