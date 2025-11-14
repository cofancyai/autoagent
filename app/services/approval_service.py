"""Approval management service"""

from typing import Optional, List
from uuid import UUID
from datetime import datetime
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.approval import ApprovalCheckpoint, Decision
from app.schemas.approval import ApprovalCheckpointCreate, DecisionCreate


class ApprovalService:
    """Service for managing approval checkpoints and decisions"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_checkpoint(
        self,
        session_id: UUID,
        checkpoint_data: ApprovalCheckpointCreate
    ) -> ApprovalCheckpoint:
        """Create a new approval checkpoint"""
        # Convert options to dict for JSONB storage
        options = [opt.model_dump() for opt in checkpoint_data.options]

        checkpoint = ApprovalCheckpoint(
            session_id=session_id,
            thinking_process_id=checkpoint_data.thinking_process_id,
            checkpoint_type=checkpoint_data.checkpoint_type,
            decision_needed=checkpoint_data.decision_needed,
            options=options,
            recommended_option=checkpoint_data.recommended_option,
            status="pending"
        )

        self.db.add(checkpoint)
        await self.db.flush()
        await self.db.refresh(checkpoint)

        return checkpoint

    async def get_checkpoint(
        self,
        checkpoint_id: UUID
    ) -> Optional[ApprovalCheckpoint]:
        """Get an approval checkpoint by ID with decision"""
        result = await self.db.execute(
            select(ApprovalCheckpoint)
            .options(selectinload(ApprovalCheckpoint.decision))
            .where(ApprovalCheckpoint.id == checkpoint_id)
        )
        return result.scalar_one_or_none()

    async def list_checkpoints(
        self,
        session_id: UUID,
        status: Optional[str] = None
    ) -> List[ApprovalCheckpoint]:
        """List approval checkpoints for a session"""
        query = (
            select(ApprovalCheckpoint)
            .options(selectinload(ApprovalCheckpoint.decision))
            .where(ApprovalCheckpoint.session_id == session_id)
        )

        if status:
            query = query.where(ApprovalCheckpoint.status == status)

        query = query.order_by(ApprovalCheckpoint.created_at.desc())

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def submit_decision(
        self,
        checkpoint_id: UUID,
        decision_data: DecisionCreate
    ) -> Optional[Decision]:
        """Submit a decision for an approval checkpoint"""
        # Get checkpoint
        checkpoint = await self.get_checkpoint(checkpoint_id)
        if not checkpoint:
            return None

        # Check if checkpoint is still pending
        if checkpoint.status != "pending":
            raise ValueError(f"Checkpoint is already {checkpoint.status}")

        # Check if decision already exists
        if checkpoint.decision:
            raise ValueError("Decision already submitted for this checkpoint")

        # Validate selected option
        if decision_data.selected_option < 0 or \
           decision_data.selected_option >= len(checkpoint.options):
            raise ValueError("Invalid option selected")

        # Create decision
        decision = Decision(
            approval_checkpoint_id=checkpoint_id,
            selected_option=decision_data.selected_option,
            modifications=decision_data.modifications,
            reasoning=decision_data.reasoning
        )

        self.db.add(decision)

        # Update checkpoint status
        checkpoint.status = "approved"
        checkpoint.updated_at = datetime.utcnow()

        await self.db.flush()
        await self.db.refresh(decision)

        return decision

    async def reject_checkpoint(
        self,
        checkpoint_id: UUID,
        reason: Optional[str] = None
    ) -> Optional[ApprovalCheckpoint]:
        """Reject an approval checkpoint"""
        checkpoint = await self.get_checkpoint(checkpoint_id)
        if not checkpoint:
            return None

        checkpoint.status = "rejected"
        checkpoint.updated_at = datetime.utcnow()

        # Store rejection reason in options metadata if provided
        if reason and checkpoint.options:
            checkpoint.options.append({"rejection_reason": reason})

        await self.db.flush()
        await self.db.refresh(checkpoint)

        return checkpoint

    async def get_pending_approvals_count(self, session_id: UUID) -> int:
        """Get count of pending approvals for a session"""
        result = await self.db.execute(
            select(func.count())
            .select_from(ApprovalCheckpoint)
            .where(
                ApprovalCheckpoint.session_id == session_id,
                ApprovalCheckpoint.status == "pending"
            )
        )
        return result.scalar()
