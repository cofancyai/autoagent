"""Session schemas"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field


class SessionCreate(BaseModel):
    """Schema for creating a new session"""
    title: Optional[str] = Field(None, max_length=500, description="Session title")
    context: Optional[Dict[str, Any]] = Field(None, description="Session context data")
    user_id: Optional[UUID] = Field(None, description="User ID")


class SessionUpdate(BaseModel):
    """Schema for updating a session"""
    title: Optional[str] = Field(None, max_length=500)
    status: Optional[str] = Field(None, description="Session status: active, paused, completed")
    context: Optional[Dict[str, Any]] = None


class SessionResponse(BaseModel):
    """Schema for session response"""
    id: UUID
    user_id: Optional[UUID]
    title: Optional[str]
    status: str
    context: Optional[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class SessionListResponse(BaseModel):
    """Schema for paginated session list"""
    sessions: List[SessionResponse]
    total: int
    page: int
    limit: int
