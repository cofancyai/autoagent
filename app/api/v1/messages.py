"""Message API endpoints"""

from typing import Any, Dict, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.message import MessageCreate, MessageListResponse, MessageResponse
from app.schemas.response import APIResponse
from app.services.event_service import EventService
from app.services.message_service import MessageService
from app.services.session_service import SessionService
from app.services.thinking_agent_service import ThinkingAgentService

router = APIRouter(prefix="/sessions/{session_id}/messages", tags=["messages"])


@router.post("", response_model=APIResponse, status_code=201)
async def create_message(
    session_id: UUID, message_data: MessageCreate, db: AsyncSession = Depends(get_db)
):
    """
    Send a message in a session

    If the message is from a user, the AI will automatically analyze it
    and generate strategic options, creating an approval checkpoint.
    """
    session_service = SessionService(db)
    message_service = MessageService(db)
    event_service = EventService(db)
    thinking_service = ThinkingAgentService(db)

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
        entity_id=message.id,
    )

    await db.commit()

    # Build response
    response_data: Dict[str, Any] = {
        "message": MessageResponse.model_validate(message),
    }

    # If this is a user message, trigger AI thinking
    if message.role == "user":
        # Capture message ID before try block to avoid accessing expired object after rollback
        message_id = str(message.id)

        try:
            approval = await thinking_service.process_user_message(session_id, message)

            if approval:
                response_data["approval_checkpoint"] = {
                    "id": str(approval.id),
                    "checkpoint_type": approval.checkpoint_type,
                    "decision_needed": approval.decision_needed,
                    "options_count": len(approval.options),
                    "recommended_option": approval.recommended_option,
                }
        except Exception as e:
            # Log error but don't fail the message creation
            # Use captured message_id to avoid greenlet error after rollback
            await event_service.log_event(
                event_type="ai.processing_error",
                event_data={"error": str(e), "message_id": message_id},
                session_id=session_id,
            )
            # Optionally add error info to response
            response_data["ai_processing"] = {"status": "failed", "error": str(e)}

    return APIResponse(data=response_data)


@router.get("", response_model=APIResponse[MessageListResponse])
async def list_messages(
    session_id: UUID,
    limit: int = Query(50, ge=1, le=100),
    before_id: Optional[UUID] = Query(None),
    db: AsyncSession = Depends(get_db),
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
        session_id=session_id, limit=limit, before_id=before_id
    )

    return APIResponse(
        data=MessageListResponse(
            messages=[MessageResponse.model_validate(m) for m in messages], has_more=has_more
        )
    )
