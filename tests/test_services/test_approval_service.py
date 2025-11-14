"""Test approval service - CRITICAL BUSINESS LOGIC"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.approval_service import ApprovalService
from app.schemas.approval import ApprovalCheckpointCreate, DecisionCreate, OptionSchema


@pytest.mark.asyncio
async def test_create_checkpoint(db_session: AsyncSession, test_session):
    """Test creating an approval checkpoint"""
    service = ApprovalService(db_session)

    checkpoint_data = ApprovalCheckpointCreate(
        checkpoint_type="tech_stack",
        decision_needed="Choose technology stack",
        options=[
            OptionSchema(
                name="Python + FastAPI",
                pros=["Fast development"],
                cons=["Slower runtime"]
            )
        ],
        recommended_option=0
    )

    checkpoint = await service.create_checkpoint(test_session.id, checkpoint_data)

    assert checkpoint.id is not None
    assert checkpoint.status == "pending"
    assert checkpoint.checkpoint_type == "tech_stack"
    assert len(checkpoint.options) == 1


@pytest.mark.asyncio
async def test_submit_decision(db_session: AsyncSession, test_session):
    """Test submitting a decision for an approval"""
    service = ApprovalService(db_session)

    # Create checkpoint
    checkpoint_data = ApprovalCheckpointCreate(
        checkpoint_type="test",
        decision_needed="Test",
        options=[
            OptionSchema(name="Option 1", pros=[], cons=[]),
            OptionSchema(name="Option 2", pros=[], cons=[])
        ],
        recommended_option=0
    )
    checkpoint = await service.create_checkpoint(test_session.id, checkpoint_data)
    await db_session.commit()

    # Submit decision
    decision_data = DecisionCreate(
        selected_option=1,
        modifications="Some changes",
        reasoning="Makes sense"
    )
    decision = await service.submit_decision(checkpoint.id, decision_data)
    await db_session.commit()

    assert decision is not None
    assert decision.selected_option == 1
    assert decision.modifications == "Some changes"

    # Check checkpoint is approved
    updated_checkpoint = await service.get_checkpoint(checkpoint.id)
    assert updated_checkpoint.status == "approved"


@pytest.mark.asyncio
async def test_cannot_submit_duplicate_decision(db_session: AsyncSession, test_session):
    """Test that duplicate decisions are prevented"""
    service = ApprovalService(db_session)

    # Create checkpoint and submit decision
    checkpoint_data = ApprovalCheckpointCreate(
        checkpoint_type="test",
        decision_needed="Test",
        options=[OptionSchema(name="Option 1", pros=[], cons=[])]
    )
    checkpoint = await service.create_checkpoint(test_session.id, checkpoint_data)
    await db_session.commit()

    decision_data = DecisionCreate(selected_option=0)
    await service.submit_decision(checkpoint.id, decision_data)
    await db_session.commit()

    # Try to submit again
    with pytest.raises(ValueError, match="Decision already submitted"):
        await service.submit_decision(checkpoint.id, decision_data)


@pytest.mark.asyncio
async def test_get_pending_approvals_count(db_session: AsyncSession, test_session):
    """Test counting pending approvals"""
    service = ApprovalService(db_session)

    # Create multiple checkpoints
    for i in range(3):
        checkpoint_data = ApprovalCheckpointCreate(
            checkpoint_type=f"test_{i}",
            decision_needed="Test",
            options=[OptionSchema(name="Option", pros=[], cons=[])]
        )
        await service.create_checkpoint(test_session.id, checkpoint_data)

    await db_session.commit()

    count = await service.get_pending_approvals_count(test_session.id)
    assert count == 3
