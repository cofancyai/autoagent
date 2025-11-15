"""Execution Task schemas"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class ExecutionTaskCreate(BaseModel):
    """Schema for creating a new execution task"""

    project_id: UUID
    task_name: str = Field(..., description="Task name")
    task_type: str = Field(
        ..., description="Task type: website, mobile_app, legal, branding, social_media, payment"
    )
    description: Optional[str] = Field(None, description="Task description")
    assigned_agent: Optional[str] = Field(None, description="Agent assigned to this task")
    priority: int = Field(default=0, description="Task priority")
    dependencies: Optional[Dict[str, Any]] = Field(None, description="List of task IDs this depends on")
    task_config: Optional[Dict[str, Any]] = Field(None, description="Task-specific configuration")
    estimated_duration_hours: Optional[int] = None


class ExecutionTaskUpdate(BaseModel):
    """Schema for updating an execution task"""

    task_name: Optional[str] = None
    description: Optional[str] = None
    assigned_agent: Optional[str] = None
    status: Optional[str] = Field(
        None, description="Status: pending, in_progress, completed, failed, blocked"
    )
    progress_percentage: Optional[int] = None
    priority: Optional[int] = None
    blocking_tasks: Optional[Dict[str, Any]] = None
    task_config: Optional[Dict[str, Any]] = None
    execution_logs: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class ExecutionTaskResponse(BaseModel):
    """Schema for execution task response"""

    id: UUID
    project_id: UUID
    session_id: UUID
    task_name: str
    task_type: str
    description: Optional[str]
    assigned_agent: Optional[str]
    status: str
    progress_percentage: int
    priority: int
    dependencies: Optional[Dict[str, Any]]
    blocking_tasks: Optional[Dict[str, Any]]
    task_config: Optional[Dict[str, Any]]
    execution_logs: Optional[Dict[str, Any]]
    error_message: Optional[str]
    estimated_duration_hours: Optional[int]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ExecutionTaskListResponse(BaseModel):
    """Schema for execution task list"""

    tasks: List[ExecutionTaskResponse]
    total: int
