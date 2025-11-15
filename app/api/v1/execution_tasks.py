"""ExecutionTask API endpoints"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.execution_task import (
    ExecutionTaskCreate,
    ExecutionTaskListResponse,
    ExecutionTaskResponse,
    ExecutionTaskUpdate,
)
from app.schemas.response import APIResponse
from app.services.event_service import EventService
from app.services.execution_project_service import ExecutionProjectService
from app.services.execution_task_service import ExecutionTaskService

router = APIRouter(prefix="/tasks", tags=["execution_tasks"])


@router.post("", response_model=APIResponse[ExecutionTaskResponse], status_code=201)
async def create_task(
    project_id: UUID, task_data: ExecutionTaskCreate, db: AsyncSession = Depends(get_db)
):
    """Create a new execution task"""
    project_service = ExecutionProjectService(db)
    task_service = ExecutionTaskService(db)
    event_service = EventService(db)

    # Verify project exists
    project = await project_service.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Create task
    task = await task_service.create_task(project_id, project.session_id, task_data)

    # Log event
    await event_service.log_event(
        event_type="execution.task_created",
        event_data={
            "task_name": task.task_name,
            "task_type": task.task_type,
            "priority": task.priority,
        },
        session_id=project.session_id,
        entity_type="execution_task",
        entity_id=task.id,
    )

    await db.commit()

    return APIResponse(data=ExecutionTaskResponse.model_validate(task))


@router.get("", response_model=APIResponse[ExecutionTaskListResponse])
async def list_tasks(
    project_id: Optional[UUID] = Query(None),
    session_id: Optional[UUID] = Query(None),
    status: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    """List execution tasks"""
    task_service = ExecutionTaskService(db)

    tasks = await task_service.list_tasks(
        project_id=project_id, session_id=session_id, status=status, limit=limit
    )

    return APIResponse(
        data=ExecutionTaskListResponse(
            tasks=[ExecutionTaskResponse.model_validate(t) for t in tasks], total=len(tasks)
        )
    )


@router.get("/{task_id}", response_model=APIResponse[ExecutionTaskResponse])
async def get_task(task_id: UUID, db: AsyncSession = Depends(get_db)):
    """Get task details"""
    task_service = ExecutionTaskService(db)

    task = await task_service.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    return APIResponse(data=ExecutionTaskResponse.model_validate(task))


@router.patch("/{task_id}", response_model=APIResponse[ExecutionTaskResponse])
async def update_task(
    task_id: UUID, task_data: ExecutionTaskUpdate, db: AsyncSession = Depends(get_db)
):
    """Update execution task"""
    task_service = ExecutionTaskService(db)
    event_service = EventService(db)

    task = await task_service.update_task(task_id, task_data)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    # Log event
    await event_service.log_event(
        event_type="execution.task_updated",
        event_data=task_data.model_dump(exclude_unset=True),
        session_id=task.session_id,
        entity_type="execution_task",
        entity_id=task.id,
    )

    await db.commit()

    return APIResponse(data=ExecutionTaskResponse.model_validate(task))
