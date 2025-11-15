"""ExecutionProject service for managing business execution projects"""

from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ExecutionProject
from app.schemas.execution_project import ExecutionProjectCreate, ExecutionProjectUpdate


class ExecutionProjectService:
    """Service for managing execution projects"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_project(
        self, session_id: UUID, project_data: ExecutionProjectCreate
    ) -> ExecutionProject:
        """Create a new execution project"""
        project = ExecutionProject(
            id=uuid4(),
            session_id=session_id,
            project_name=project_data.project_name,
            business_type=project_data.business_type,
            description=project_data.description,
            total_budget=project_data.total_budget,
            spent_amount=Decimal("0.00"),
            status="planning",
            progress_percentage=Decimal("0.00"),
            estimated_completion_date=project_data.estimated_completion_date,
            requirements=project_data.requirements,
            execution_plan=project_data.execution_plan,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        self.db.add(project)
        await self.db.flush()
        await self.db.refresh(project)
        return project

    async def get_project(self, project_id: UUID) -> Optional[ExecutionProject]:
        """Get project by ID"""
        result = await self.db.execute(select(ExecutionProject).where(ExecutionProject.id == project_id))
        return result.scalars().first()

    async def list_projects(
        self, session_id: Optional[UUID] = None, status: Optional[str] = None, limit: int = 50
    ) -> List[ExecutionProject]:
        """List execution projects with optional filters"""
        query = select(ExecutionProject).order_by(ExecutionProject.created_at.desc())

        if session_id:
            query = query.where(ExecutionProject.session_id == session_id)
        if status:
            query = query.where(ExecutionProject.status == status)

        query = query.limit(limit)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def update_project(
        self, project_id: UUID, project_data: ExecutionProjectUpdate
    ) -> Optional[ExecutionProject]:
        """Update execution project"""
        project = await self.get_project(project_id)
        if not project:
            return None

        # Update fields if provided
        update_dict = project_data.model_dump(exclude_unset=True)
        for field, value in update_dict.items():
            setattr(project, field, value)

        project.updated_at = datetime.utcnow()

        await self.db.flush()
        await self.db.refresh(project)
        return project

    async def update_progress(
        self, project_id: UUID, progress_percentage: Decimal, spent_amount: Optional[Decimal] = None
    ) -> Optional[ExecutionProject]:
        """Update project progress"""
        project = await self.get_project(project_id)
        if not project:
            return None

        project.progress_percentage = progress_percentage
        if spent_amount is not None:
            project.spent_amount = spent_amount

        # Auto-update status based on progress
        if progress_percentage >= 100:
            project.status = "completed"
            project.actual_completion_date = datetime.utcnow()
        elif progress_percentage > 0:
            project.status = "in_progress"

        project.updated_at = datetime.utcnow()

        await self.db.flush()
        await self.db.refresh(project)
        return project

    async def delete_project(self, project_id: UUID) -> bool:
        """Delete execution project"""
        project = await self.get_project(project_id)
        if not project:
            return False

        await self.db.delete(project)
        await self.db.flush()
        return True
