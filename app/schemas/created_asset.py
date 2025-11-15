"""Created Asset schemas"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class CreatedAssetCreate(BaseModel):
    """Schema for creating a new asset"""

    project_id: UUID
    task_id: Optional[UUID] = None
    asset_name: str = Field(..., description="Asset name")
    asset_type: str = Field(
        ...,
        description="Asset type: website, mobile_app, logo, legal_document, social_profile, payment_gateway",
    )
    description: Optional[str] = None
    url: Optional[str] = Field(None, description="URL to access the asset")
    file_path: Optional[str] = Field(None, description="Local file path")
    credentials: Optional[Dict[str, Any]] = Field(None, description="Login credentials")
    asset_metadata: Optional[Dict[str, Any]] = Field(None, description="Asset-specific metadata")
    external_id: Optional[str] = Field(None, description="ID in external service")
    external_service: Optional[str] = Field(None, description="External service name")


class CreatedAssetUpdate(BaseModel):
    """Schema for updating an asset"""

    asset_name: Optional[str] = None
    description: Optional[str] = None
    url: Optional[str] = None
    file_path: Optional[str] = None
    credentials: Optional[Dict[str, Any]] = None
    asset_metadata: Optional[Dict[str, Any]] = None
    deployment_status: Optional[str] = Field(None, description="Status: draft, deployed, live, archived")
    external_id: Optional[str] = None
    external_service: Optional[str] = None


class CreatedAssetResponse(BaseModel):
    """Schema for asset response"""

    id: UUID
    project_id: UUID
    task_id: Optional[UUID]
    session_id: UUID
    asset_name: str
    asset_type: str
    description: Optional[str]
    url: Optional[str]
    file_path: Optional[str]
    credentials: Optional[Dict[str, Any]]
    asset_metadata: Optional[Dict[str, Any]]
    deployment_status: str
    external_id: Optional[str]
    external_service: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CreatedAssetListResponse(BaseModel):
    """Schema for asset list"""

    assets: List[CreatedAssetResponse]
    total: int
