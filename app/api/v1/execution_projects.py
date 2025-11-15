"""ExecutionProject API endpoints"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.execution_project import (
    ExecutionProjectCreate,
    ExecutionProjectListResponse,
    ExecutionProjectResponse,
    ExecutionProjectUpdate,
)
from app.schemas.response import APIResponse
from app.services.event_service import EventService
from app.services.execution_project_service import ExecutionProjectService
from app.services.session_service import SessionService

router = APIRouter(prefix="/projects", tags=["execution_projects"])


@router.post("", response_model=APIResponse[ExecutionProjectResponse], status_code=201)
async def create_project(
    session_id: UUID, project_data: ExecutionProjectCreate, db: AsyncSession = Depends(get_db)
):
    """Create a new execution project"""
    session_service = SessionService(db)
    project_service = ExecutionProjectService(db)
    event_service = EventService(db)

    # Verify session exists
    session = await session_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Create project
    project = await project_service.create_project(session_id, project_data)

    # Log event
    await event_service.log_event(
        event_type="execution.project_created",
        event_data={
            "project_name": project.project_name,
            "business_type": project.business_type,
            "total_budget": str(project.total_budget) if project.total_budget else None,
        },
        session_id=session_id,
        entity_type="execution_project",
        entity_id=project.id,
    )

    await db.commit()

    return APIResponse(data=ExecutionProjectResponse.model_validate(project))


@router.get("", response_model=APIResponse[ExecutionProjectListResponse])
async def list_projects(
    session_id: Optional[UUID] = Query(None),
    status: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """List execution projects"""
    project_service = ExecutionProjectService(db)

    projects = await project_service.list_projects(session_id=session_id, status=status, limit=limit)

    return APIResponse(
        data=ExecutionProjectListResponse(
            projects=[ExecutionProjectResponse.model_validate(p) for p in projects],
            total=len(projects),
        )
    )


@router.get("/{project_id}", response_model=APIResponse[ExecutionProjectResponse])
async def get_project(project_id: UUID, db: AsyncSession = Depends(get_db)):
    """Get project details"""
    project_service = ExecutionProjectService(db)

    project = await project_service.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    return APIResponse(data=ExecutionProjectResponse.model_validate(project))


@router.patch("/{project_id}", response_model=APIResponse[ExecutionProjectResponse])
async def update_project(
    project_id: UUID, project_data: ExecutionProjectUpdate, db: AsyncSession = Depends(get_db)
):
    """Update execution project"""
    project_service = ExecutionProjectService(db)
    event_service = EventService(db)

    project = await project_service.update_project(project_id, project_data)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Log event
    await event_service.log_event(
        event_type="execution.project_updated",
        event_data=project_data.model_dump(exclude_unset=True),
        session_id=project.session_id,
        entity_type="execution_project",
        entity_id=project.id,
    )

    await db.commit()

    return APIResponse(data=ExecutionProjectResponse.model_validate(project))


@router.delete("/{project_id}", status_code=204)
async def delete_project(project_id: UUID, db: AsyncSession = Depends(get_db)):
    """Delete execution project"""
    project_service = ExecutionProjectService(db)
    event_service = EventService(db)

    project = await project_service.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Log event before deletion
    await event_service.log_event(
        event_type="execution.project_deleted",
        event_data={"project_id": str(project_id), "project_name": project.project_name},
        session_id=project.session_id,
    )

    deleted = await project_service.delete_project(project_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Project not found")

    await db.commit()
