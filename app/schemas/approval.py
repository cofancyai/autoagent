"""Approval schemas"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class OptionSchema(BaseModel):
    """Schema for an approval option"""

    name: str = Field(..., description="Option name")
    pros: List[str] = Field(default_factory=list, description="Pros of this option")
    cons: List[str] = Field(default_factory=list, description="Cons of this option")
    description: Optional[str] = Field(None, description="Detailed description")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class ApprovalCheckpointCreate(BaseModel):
    """Schema for creating an approval checkpoint"""

    checkpoint_type: str = Field(
        ..., description="Type of checkpoint: tech_stack, architecture, database_schema, etc."
    )
    decision_needed: str = Field(..., description="Description of the decision needed")
    options: List[OptionSchema] = Field(..., description="List of options to choose from")
    recommended_option: Optional[int] = Field(None, description="Index of the recommended option")
    thinking_process_id: Optional[UUID] = Field(None, description="Associated thinking process ID")


class DecisionCreate(BaseModel):
    """Schema for submitting a decision"""

    selected_option: int = Field(..., description="Index of the selected option")
    modifications: Optional[str] = Field(
        None, description="Any modifications to the selected option"
    )
    reasoning: Optional[str] = Field(None, description="Reasoning for the decision")


class DecisionResponse(BaseModel):
    """Schema for decision response"""

    id: UUID
    approval_checkpoint_id: UUID
    selected_option: int
    modifications: Optional[str]
    reasoning: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


class ApprovalCheckpointResponse(BaseModel):
    """Schema for approval checkpoint response"""

    id: UUID
    session_id: UUID
    thinking_process_id: Optional[UUID]
    checkpoint_type: str
    decision_needed: str
    options: List[Dict[str, Any]]
    recommended_option: Optional[int]
    status: str
    decision: Optional[DecisionResponse] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ApprovalListResponse(BaseModel):
    """Schema for approval list"""

    approvals: List[ApprovalCheckpointResponse]
    total: int
