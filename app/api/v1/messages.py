"""Message API endpoints"""

from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.message_service import MessageService
from app.services.session_service import SessionService
from app.services.event_service import EventService
from app.schemas.message import (
    MessageCreate,
    MessageResponse,
    MessageListResponse
)
from app.schemas.response import APIResponse

router = APIRouter(prefix="/sessions/{session_id}/messages", tags=["messages"])


@router.post("", response_model=APIResponse[MessageResponse], status_code=201)
async def create_message(
    session_id: UUID,
    message_data: MessageCreate,
    db: AsyncSession = Depends(get_db)
):
    """Send a message in a session"""
    session_service = SessionService(db)
    message_service = MessageService(db)
    event_service = EventService(db)

    # Verify session exists
    session = await session_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Create message
    message = await message_service.create_message(session_id, message_data)

    # Log event
    await event_service.log_event(
        event_type="message.created",
        event_data={"role": message.role, "content_length": len(message.content)},
        session_id=session_id,
        entity_type="message",
        entity_id=message.id
    )

    await db.commit()

    return APIResponse(data=MessageResponse.model_validate(message))


@router.get("", response_model=APIResponse[MessageListResponse])
async def list_messages(
    session_id: UUID,
    limit: int = Query(50, ge=1, le=100),
    before_id: Optional[UUID] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """Get conversation history"""
    session_service = SessionService(db)
    message_service = MessageService(db)

    # Verify session exists
    session = await session_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Get messages
    messages, has_more = await message_service.list_messages(
        session_id=session_id,
        limit=limit,
        before_id=before_id
    )

    return APIResponse(
        data=MessageListResponse(
            messages=[MessageResponse.model_validate(m) for m in messages],
            has_more=has_more
        )
    )
