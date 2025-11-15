"""ServiceIntegration API endpoints"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.response import APIResponse
from app.schemas.service_integration import (
    ServiceIntegrationCreate,
    ServiceIntegrationListResponse,
    ServiceIntegrationResponse,
    ServiceIntegrationUpdate,
)
from app.services.event_service import EventService
from app.services.execution_project_service import ExecutionProjectService
from app.services.service_integration_service import ServiceIntegrationService

router = APIRouter(prefix="/integrations", tags=["service_integrations"])


@router.post("", response_model=APIResponse[ServiceIntegrationResponse], status_code=201)
async def create_integration(
    integration_data: ServiceIntegrationCreate, db: AsyncSession = Depends(get_db)
):
    """Create a new service integration"""
    project_service = ExecutionProjectService(db)
    integration_service = ServiceIntegrationService(db)
    event_service = EventService(db)

    # Verify project exists
    project = await project_service.get_project(integration_data.project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Create integration
    integration = await integration_service.create_integration(
        integration_data.project_id, project.session_id, integration_data
    )

    # Log event
    await event_service.log_event(
        event_type="execution.integration_created",
        event_data={
            "service_name": integration.service_name,
            "service_category": integration.service_category,
        },
        session_id=project.session_id,
        entity_type="service_integration",
        entity_id=integration.id,
    )

    await db.commit()

    return APIResponse(data=ServiceIntegrationResponse.model_validate(integration))


@router.get("", response_model=APIResponse[ServiceIntegrationListResponse])
async def list_integrations(
    project_id: Optional[UUID] = Query(None),
    session_id: Optional[UUID] = Query(None),
    service_category: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    """List service integrations"""
    integration_service = ServiceIntegrationService(db)

    integrations = await integration_service.list_integrations(
        project_id=project_id,
        session_id=session_id,
        service_category=service_category,
        status=status,
        limit=limit,
    )

    return APIResponse(
        data=ServiceIntegrationListResponse(
            integrations=[ServiceIntegrationResponse.model_validate(i) for i in integrations],
            total=len(integrations),
        )
    )


@router.get("/{integration_id}", response_model=APIResponse[ServiceIntegrationResponse])
async def get_integration(integration_id: UUID, db: AsyncSession = Depends(get_db)):
    """Get integration details"""
    integration_service = ServiceIntegrationService(db)

    integration = await integration_service.get_integration(integration_id)
    if not integration:
        raise HTTPException(status_code=404, detail="Integration not found")

    return APIResponse(data=ServiceIntegrationResponse.model_validate(integration))


@router.patch("/{integration_id}", response_model=APIResponse[ServiceIntegrationResponse])
async def update_integration(
    integration_id: UUID,
    integration_data: ServiceIntegrationUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update service integration"""
    integration_service = ServiceIntegrationService(db)
    event_service = EventService(db)

    integration = await integration_service.update_integration(integration_id, integration_data)
    if not integration:
        raise HTTPException(status_code=404, detail="Integration not found")

    # Log event
    await event_service.log_event(
        event_type="execution.integration_updated",
        event_data=integration_data.model_dump(exclude_unset=True),
        session_id=integration.session_id,
        entity_type="service_integration",
        entity_id=integration.id,
    )

    await db.commit()

    return APIResponse(data=ServiceIntegrationResponse.model_validate(integration))


@router.delete("/{integration_id}", status_code=204)
async def delete_integration(integration_id: UUID, db: AsyncSession = Depends(get_db)):
    """Delete service integration"""
    integration_service = ServiceIntegrationService(db)
    event_service = EventService(db)

    integration = await integration_service.get_integration(integration_id)
    if not integration:
        raise HTTPException(status_code=404, detail="Integration not found")

    # Log event before deletion
    await event_service.log_event(
        event_type="execution.integration_deleted",
        event_data={"integration_id": str(integration_id), "service_name": integration.service_name},
        session_id=integration.session_id,
    )

    deleted = await integration_service.delete_integration(integration_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Integration not found")

    await db.commit()
