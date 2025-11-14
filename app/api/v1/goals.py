"""Goal API endpoints"""

from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.goal_service import GoalService
from app.services.session_service import SessionService
from app.services.event_service import EventService
from app.schemas.goal import (
    GoalCreate,
    GoalUpdate,
    GoalResponse,
    GoalListResponse
)
from app.schemas.response import APIResponse

router = APIRouter(tags=["goals"])


@router.post(
    "/sessions/{session_id}/goals",
    response_model=APIResponse[GoalResponse],
    status_code=201
)
async def create_goal(
    session_id: UUID,
    goal_data: GoalCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new goal for a session"""
    session_service = SessionService(db)
    goal_service = GoalService(db)
    event_service = EventService(db)

    # Verify session exists
    session = await session_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Create goal
    goal = await goal_service.create_goal(session_id, goal_data)

    # Log event
    await event_service.log_goal_event(
        session_id=session_id,
        goal_id=goal.id,
        event_type="goal.created",
        event_data={"description": goal.description, "priority": goal.priority}
    )

    await db.commit()

    return APIResponse(data=GoalResponse.model_validate(goal))


@router.get(
    "/sessions/{session_id}/goals",
    response_model=APIResponse[GoalListResponse]
)
async def list_goals(
    session_id: UUID,
    status: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """List goals for a session"""
    session_service = SessionService(db)
    goal_service = GoalService(db)

    # Verify session exists
    session = await session_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Get goals
    goals = await goal_service.list_goals(session_id=session_id, status=status)

    return APIResponse(
        data=GoalListResponse(
            goals=[GoalResponse.model_validate(g) for g in goals],
            total=len(goals)
        )
    )


@router.get("/goals/{goal_id}", response_model=APIResponse[GoalResponse])
async def get_goal(
    goal_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get goal details"""
    goal_service = GoalService(db)

    goal = await goal_service.get_goal(goal_id)
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")

    return APIResponse(data=GoalResponse.model_validate(goal))


@router.patch("/goals/{goal_id}", response_model=APIResponse[GoalResponse])
async def update_goal(
    goal_id: UUID,
    goal_data: GoalUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update a goal"""
    goal_service = GoalService(db)
    event_service = EventService(db)

    goal = await goal_service.update_goal(goal_id, goal_data)
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")

    # Log event
    await event_service.log_goal_event(
        session_id=goal.session_id,
        goal_id=goal.id,
        event_type="goal.updated",
        event_data=goal_data.model_dump(exclude_unset=True)
    )

    await db.commit()

    return APIResponse(data=GoalResponse.model_validate(goal))
