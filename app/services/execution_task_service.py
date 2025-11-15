"""ExecutionTask service for managing execution tasks"""

from datetime import datetime
from typing import List, Optional
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ExecutionTask
from app.schemas.execution_task import ExecutionTaskCreate, ExecutionTaskUpdate


class ExecutionTaskService:
    """Service for managing execution tasks"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_task(
        self, project_id: UUID, session_id: UUID, task_data: ExecutionTaskCreate
    ) -> ExecutionTask:
        """Create a new execution task"""
        task = ExecutionTask(
            id=uuid4(),
            project_id=project_id,
            session_id=session_id,
            task_name=task_data.task_name,
            task_type=task_data.task_type,
            description=task_data.description,
            assigned_agent=task_data.assigned_agent,
            status="pending",
            progress_percentage=0,
            priority=task_data.priority or 1,
            dependencies=task_data.dependencies,
            blocking_tasks=task_data.blocking_tasks,
            task_config=task_data.task_config,
            execution_logs=[],
            estimated_duration_hours=task_data.estimated_duration_hours,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        self.db.add(task)
        await self.db.flush()
        await self.db.refresh(task)
        return task

    async def get_task(self, task_id: UUID) -> Optional[ExecutionTask]:
        """Get task by ID"""
        result = await self.db.execute(select(ExecutionTask).where(ExecutionTask.id == task_id))
        return result.scalars().first()

    async def list_tasks(
        self,
        project_id: Optional[UUID] = None,
        session_id: Optional[UUID] = None,
        status: Optional[str] = None,
        limit: int = 100,
    ) -> List[ExecutionTask]:
        """List execution tasks with optional filters"""
        query = select(ExecutionTask).order_by(ExecutionTask.priority.desc(), ExecutionTask.created_at)

        if project_id:
            query = query.where(ExecutionTask.project_id == project_id)
        if session_id:
            query = query.where(ExecutionTask.session_id == session_id)
        if status:
            query = query.where(ExecutionTask.status == status)

        query = query.limit(limit)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def update_task(self, task_id: UUID, task_data: ExecutionTaskUpdate) -> Optional[ExecutionTask]:
        """Update execution task"""
        task = await self.get_task(task_id)
        if not task:
            return None

        # Update fields if provided
        update_dict = task_data.model_dump(exclude_unset=True)
        for field, value in update_dict.items():
            setattr(task, field, value)

        task.updated_at = datetime.utcnow()

        await self.db.flush()
        await self.db.refresh(task)
        return task

    async def update_progress(
        self, task_id: UUID, progress_percentage: int, log_entry: Optional[str] = None
    ) -> Optional[ExecutionTask]:
        """Update task progress"""
        task = await self.get_task(task_id)
        if not task:
            return None

        task.progress_percentage = progress_percentage

        # Add log entry
        if log_entry:
            if task.execution_logs is None:
                task.execution_logs = []
            task.execution_logs.append(
                {"timestamp": datetime.utcnow().isoformat(), "message": log_entry}
            )

        # Auto-update status based on progress
        if progress_percentage >= 100:
            task.status = "completed"
            task.completed_at = datetime.utcnow()
        elif progress_percentage > 0 and task.status == "pending":
            task.status = "in_progress"
            task.started_at = datetime.utcnow()

        task.updated_at = datetime.utcnow()

        await self.db.flush()
        await self.db.refresh(task)
        return task

    async def mark_failed(self, task_id: UUID, error_message: str) -> Optional[ExecutionTask]:
        """Mark task as failed"""
        task = await self.get_task(task_id)
        if not task:
            return None

        task.status = "failed"
        task.error_message = error_message
        task.updated_at = datetime.utcnow()

        await self.db.flush()
        await self.db.refresh(task)
        return task

    async def get_ready_tasks(self, project_id: UUID) -> List[ExecutionTask]:
        """Get tasks that are ready to execute (pending, no blocking dependencies)"""
        all_tasks = await self.list_tasks(project_id=project_id)

        # Get completed task IDs
        completed_ids = {str(t.id) for t in all_tasks if t.status == "completed"}

        ready_tasks = []
        for task in all_tasks:
            if task.status != "pending":
                continue

            # Check if all dependencies are completed
            if task.dependencies:
                deps = task.dependencies if isinstance(task.dependencies, list) else []
                if all(dep_id in completed_ids for dep_id in deps):
                    ready_tasks.append(task)
            else:
                ready_tasks.append(task)

        return ready_tasks
