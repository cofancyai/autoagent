"""Goal management service"""

from typing import List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.goal import Goal
from app.schemas.goal import GoalCreate, GoalUpdate


class GoalService:
    """Service for managing goals/tasks"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_goal(self, session_id: UUID, goal_data: GoalCreate) -> Goal:
        """Create a new goal"""
        goal = Goal(
            session_id=session_id,
            description=goal_data.description,
            priority=goal_data.priority,
            status="pending",
        )

        self.db.add(goal)
        await self.db.flush()
        await self.db.refresh(goal)

        return goal

    async def get_goal(self, goal_id: UUID) -> Optional[Goal]:
        """Get a goal by ID"""
        result = await self.db.execute(select(Goal).where(Goal.id == goal_id))
        return result.scalar_one_or_none()

    async def list_goals(self, session_id: UUID, status: Optional[str] = None) -> List[Goal]:
        """List goals for a session"""
        query = select(Goal).where(Goal.session_id == session_id)

        if status:
            query = query.where(Goal.status == status)

        query = query.order_by(Goal.priority.desc(), Goal.created_at.asc())

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def update_goal(self, goal_id: UUID, goal_data: GoalUpdate) -> Optional[Goal]:
        """Update a goal"""
        goal = await self.get_goal(goal_id)
        if not goal:
            return None

        # Update fields
        update_data = goal_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(goal, field, value)

        await self.db.flush()
        await self.db.refresh(goal)

        return goal

    async def mark_goal_completed(self, goal_id: UUID, result: dict) -> Optional[Goal]:
        """Mark a goal as completed with result"""
        goal = await self.get_goal(goal_id)
        if not goal:
            return None

        goal.status = "completed"
        goal.result = result

        await self.db.flush()
        await self.db.refresh(goal)

        return goal

    async def mark_goal_failed(self, goal_id: UUID, error: str) -> Optional[Goal]:
        """Mark a goal as failed"""
        goal = await self.get_goal(goal_id)
        if not goal:
            return None

        goal.status = "failed"
        goal.result = {"error": error}

        await self.db.flush()
        await self.db.refresh(goal)

        return goal
