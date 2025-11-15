"""Execution Project schemas"""

from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class ExecutionProjectCreate(BaseModel):
    """Schema for creating a new execution project"""

    project_name: str = Field(..., description="Project name")
    business_type: str = Field(..., description="Business type (saas, ecommerce, agency, etc.)")
    description: Optional[str] = Field(None, description="Project description")
    total_budget: Optional[Decimal] = Field(None, description="Total budget for the project")
    requirements: Optional[Dict[str, Any]] = Field(None, description="Project requirements")


class ExecutionProjectUpdate(BaseModel):
    """Schema for updating an execution project"""

    project_name: Optional[str] = None
    description: Optional[str] = None
    total_budget: Optional[Decimal] = None
    spent_amount: Optional[Decimal] = None
    status: Optional[str] = Field(None, description="Status: planning, in_progress, completed, failed, paused")
    progress_percentage: Optional[Decimal] = None
    estimated_completion_date: Optional[datetime] = None
    actual_completion_date: Optional[datetime] = None
    execution_plan: Optional[Dict[str, Any]] = None
    results: Optional[Dict[str, Any]] = None


class ExecutionProjectResponse(BaseModel):
    """Schema for execution project response"""

    id: UUID
    session_id: UUID
    project_name: str
    business_type: str
    description: Optional[str]
    total_budget: Optional[Decimal]
    spent_amount: Decimal
    status: str
    progress_percentage: Decimal
    estimated_completion_date: Optional[datetime]
    actual_completion_date: Optional[datetime]
    requirements: Optional[Dict[str, Any]]
    execution_plan: Optional[Dict[str, Any]]
    results: Optional[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ExecutionProjectListResponse(BaseModel):
    """Schema for execution project list"""

    projects: List[ExecutionProjectResponse]
    total: int
