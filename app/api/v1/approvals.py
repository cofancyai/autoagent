"""Approval API endpoints"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.approval import (
    ApprovalCheckpointCreate,
    ApprovalCheckpointResponse,
    ApprovalListResponse,
    DecisionCreate,
    DecisionResponse,
)
from app.schemas.response import APIResponse
from app.services.approval_service import ApprovalService
from app.services.event_service import EventService
from app.services.session_service import SessionService

router = APIRouter(tags=["approvals"])


@router.post(
    "/sessions/{session_id}/approvals",
    response_model=APIResponse[ApprovalCheckpointResponse],
    status_code=201,
)
async def create_approval_checkpoint(
    session_id: UUID, approval_data: ApprovalCheckpointCreate, db: AsyncSession = Depends(get_db)
):
    """Create a new approval checkpoint"""
    session_service = SessionService(db)
    approval_service = ApprovalService(db)
    event_service = EventService(db)

    # Verify session exists
    session = await session_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Create checkpoint
    checkpoint = await approval_service.create_checkpoint(session_id, approval_data)

    # Log event
    await event_service.log_approval_event(
        session_id=session_id,
        approval_id=checkpoint.id,
        event_type="approval.created",
        event_data={
            "checkpoint_type": checkpoint.checkpoint_type,
            "options_count": len(checkpoint.options),
        },
    )

    await db.commit()

    return APIResponse(data=ApprovalCheckpointResponse.model_validate(checkpoint))


@router.get("/sessions/{session_id}/approvals", response_model=APIResponse[ApprovalListResponse])
async def list_approvals(
    session_id: UUID, status: Optional[str] = Query(None), db: AsyncSession = Depends(get_db)
):
    """List approval checkpoints for a session"""
    session_service = SessionService(db)
    approval_service = ApprovalService(db)

    # Verify session exists
    session = await session_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Get approvals
    approvals = await approval_service.list_checkpoints(session_id=session_id, status=status)

    return APIResponse(
        data=ApprovalListResponse(
            approvals=[ApprovalCheckpointResponse.model_validate(a) for a in approvals],
            total=len(approvals),
        )
    )


@router.get("/approvals/{approval_id}", response_model=APIResponse[ApprovalCheckpointResponse])
async def get_approval(approval_id: UUID, db: AsyncSession = Depends(get_db)):
    """Get approval checkpoint details"""
    approval_service = ApprovalService(db)

    checkpoint = await approval_service.get_checkpoint(approval_id)
    if not checkpoint:
        raise HTTPException(status_code=404, detail="Approval checkpoint not found")

    return APIResponse(data=ApprovalCheckpointResponse.model_validate(checkpoint))


@router.post("/approvals/{approval_id}/decide", response_model=APIResponse[DecisionResponse])
async def submit_decision(
    approval_id: UUID, decision_data: DecisionCreate, db: AsyncSession = Depends(get_db)
):
    """Submit a decision for an approval checkpoint"""
    approval_service = ApprovalService(db)
    event_service = EventService(db)

    try:
        decision = await approval_service.submit_decision(approval_id, decision_data)
        if not decision:
            raise HTTPException(status_code=404, detail="Approval checkpoint not found")

        # Get checkpoint for logging
        checkpoint = await approval_service.get_checkpoint(approval_id)

        # Log event
        await event_service.log_approval_event(
            session_id=checkpoint.session_id,
            approval_id=approval_id,
            event_type="approval.decided",
            event_data={
                "selected_option": decision.selected_option,
                "has_modifications": decision.modifications is not None,
            },
        )

        await db.commit()

        return APIResponse(data=DecisionResponse.model_validate(decision))

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.patch("/approvals/{approval_id}", response_model=APIResponse[ApprovalCheckpointResponse])
async def update_approval_status(
    approval_id: UUID,
    status: str = Query(..., description="New status: rejected, etc."),
    reason: Optional[str] = Query(None, description="Reason for status change"),
    db: AsyncSession = Depends(get_db),
):
    """Update approval checkpoint status (e.g., reject)"""
    approval_service = ApprovalService(db)
    event_service = EventService(db)

    if status == "rejected":
        checkpoint = await approval_service.reject_checkpoint(approval_id, reason)
        if not checkpoint:
            raise HTTPException(status_code=404, detail="Approval checkpoint not found")

        # Log event
        await event_service.log_approval_event(
            session_id=checkpoint.session_id,
            approval_id=approval_id,
            event_type="approval.rejected",
            event_data={"reason": reason},
        )

        await db.commit()

        return APIResponse(data=ApprovalCheckpointResponse.model_validate(checkpoint))
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported status: {status}")
