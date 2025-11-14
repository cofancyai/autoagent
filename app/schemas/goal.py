"""Goal schemas"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field


class GoalCreate(BaseModel):
    """Schema for creating a new goal"""
    description: str = Field(..., description="Goal description")
    priority: int = Field(default=0, description="Goal priority")


class GoalUpdate(BaseModel):
    """Schema for updating a goal"""
    description: Optional[str] = None
    status: Optional[str] = Field(
        None,
        description="Goal status: pending, in_progress, completed, failed"
    )
    priority: Optional[int] = None
    result: Optional[Dict[str, Any]] = None


class GoalResponse(BaseModel):
    """Schema for goal response"""
    id: UUID
    session_id: UUID
    description: str
    status: str
    priority: int
    result: Optional[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class GoalListResponse(BaseModel):
    """Schema for goal list"""
    goals: List[GoalResponse]
    total: int
