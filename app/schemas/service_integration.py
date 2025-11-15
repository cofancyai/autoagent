"""Service Integration schemas"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class ServiceIntegrationCreate(BaseModel):
    """Schema for creating a new service integration"""

    project_id: UUID
    service_name: str = Field(..., description="Service name (webflow, stripe, mailchimp, etc.)")
    service_category: str = Field(
        ..., description="Category: website, payment, email, social_media, legal, analytics"
    )
    api_key: Optional[str] = Field(None, description="API key")
    api_credentials: Optional[Dict[str, Any]] = Field(None, description="Additional credentials")
    config: Optional[Dict[str, Any]] = Field(None, description="Service-specific configuration")
    webhooks: Optional[Dict[str, Any]] = Field(None, description="Webhook configurations")


class ServiceIntegrationUpdate(BaseModel):
    """Schema for updating a service integration"""

    service_name: Optional[str] = None
    service_category: Optional[str] = None
    status: Optional[str] = Field(
        None, description="Status: pending, connected, active, failed, disconnected"
    )
    api_key: Optional[str] = None
    api_credentials: Optional[Dict[str, Any]] = None
    config: Optional[Dict[str, Any]] = None
    webhooks: Optional[Dict[str, Any]] = None
    last_used_at: Optional[datetime] = None
    usage_stats: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    retry_count: Optional[str] = None


class ServiceIntegrationResponse(BaseModel):
    """Schema for service integration response"""

    id: UUID
    project_id: UUID
    session_id: UUID
    service_name: str
    service_category: str
    status: str
    api_key: Optional[str]
    api_credentials: Optional[Dict[str, Any]]
    config: Optional[Dict[str, Any]]
    webhooks: Optional[Dict[str, Any]]
    last_used_at: Optional[datetime]
    usage_stats: Optional[Dict[str, Any]]
    error_message: Optional[str]
    retry_count: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ServiceIntegrationListResponse(BaseModel):
    """Schema for service integration list"""

    integrations: List[ServiceIntegrationResponse]
    total: int
