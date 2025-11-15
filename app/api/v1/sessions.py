"""Session API endpoints"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.response import APIResponse
from app.schemas.session import SessionCreate, SessionListResponse, SessionResponse, SessionUpdate
from app.services.event_service import EventService
from app.services.session_service import SessionService

router = APIRouter(prefix="/sessions", tags=["sessions"])


@router.post("", response_model=APIResponse[SessionResponse], status_code=201)
async def create_session(session_data: SessionCreate, db: AsyncSession = Depends(get_db)):
    """Create a new session"""
    session_service = SessionService(db)
    event_service = EventService(db)

    # Create session
    session = await session_service.create_session(session_data)

    # Log event
    await event_service.log_session_event(
        session_id=session.id,
        event_type="session.created",
        event_data={"title": session.title, "status": session.status},
    )

    await db.commit()

    return APIResponse(data=SessionResponse.model_validate(session))


@router.get("", response_model=APIResponse[SessionListResponse])
async def list_sessions(
    user_id: Optional[UUID] = Query(None),
    status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """List sessions with pagination"""
    session_service = SessionService(db)

    sessions, total = await session_service.list_sessions(
        user_id=user_id, status=status, page=page, limit=limit
    )

    return APIResponse(
        data=SessionListResponse(
            sessions=[SessionResponse.model_validate(s) for s in sessions],
            total=total,
            page=page,
            limit=limit,
        )
    )


@router.get("/{session_id}", response_model=APIResponse[SessionResponse])
async def get_session(session_id: UUID, db: AsyncSession = Depends(get_db)):
    """Get session details"""
    session_service = SessionService(db)

    session = await session_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    return APIResponse(data=SessionResponse.model_validate(session))


@router.patch("/{session_id}", response_model=APIResponse[SessionResponse])
async def update_session(
    session_id: UUID, session_data: SessionUpdate, db: AsyncSession = Depends(get_db)
):
    """Update session"""
    session_service = SessionService(db)
    event_service = EventService(db)

    session = await session_service.update_session(session_id, session_data)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Log event
    await event_service.log_session_event(
        session_id=session.id,
        event_type="session.updated",
        event_data=session_data.model_dump(exclude_unset=True),
    )

    await db.commit()

    return APIResponse(data=SessionResponse.model_validate(session))


@router.delete("/{session_id}", status_code=204)
async def delete_session(session_id: UUID, db: AsyncSession = Depends(get_db)):
    """Delete session"""
    session_service = SessionService(db)
    event_service = EventService(db)

    # Log event before deletion
    await event_service.log_session_event(
        session_id=session_id,
        event_type="session.deleted",
        event_data={"session_id": str(session_id)},
    )

    deleted = await session_service.delete_session(session_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Session not found")

    await db.commit()
