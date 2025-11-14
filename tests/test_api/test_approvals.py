"""Test approval API endpoints - CRITICAL PATH"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_approval_checkpoint(client: AsyncClient, test_session):
    """Test creating an approval checkpoint"""
    response = await client.post(
        f"/api/v1/sessions/{test_session.id}/approvals",
        json={
            "checkpoint_type": "tech_stack",
            "decision_needed": "Choose technology stack",
            "options": [
                {
                    "name": "Python + FastAPI",
                    "pros": ["Fast development", "Great for AI"],
                    "cons": ["Slower than compiled languages"]
                },
                {
                    "name": "Node.js + Express",
                    "pros": ["JavaScript everywhere"],
                    "cons": ["Less mature AI tooling"]
                }
            ],
            "recommended_option": 0
        }
    )

    assert response.status_code == 201
    data = response.json()
    assert data["data"]["checkpoint_type"] == "tech_stack"
    assert data["data"]["status"] == "pending"
    assert len(data["data"]["options"]) == 2


@pytest.mark.asyncio
async def test_submit_approval_decision(client: AsyncClient, test_session):
    """Test submitting a decision for an approval checkpoint"""
    # First create an approval
    create_response = await client.post(
        f"/api/v1/sessions/{test_session.id}/approvals",
        json={
            "checkpoint_type": "database_schema",
            "decision_needed": "Choose database schema",
            "options": [
                {"name": "Option 1", "pros": ["Pro1"], "cons": ["Con1"]},
                {"name": "Option 2", "pros": ["Pro2"], "cons": ["Con2"]}
            ],
            "recommended_option": 0
        }
    )
    approval_id = create_response.json()["data"]["id"]

    # Submit decision
    decision_response = await client.post(
        f"/api/v1/approvals/{approval_id}/decide",
        json={
            "selected_option": 1,
            "modifications": "Use PostgreSQL instead",
            "reasoning": "Better for our use case"
        }
    )

    assert decision_response.status_code == 200
    decision_data = decision_response.json()
    assert decision_data["data"]["selected_option"] == 1
    assert decision_data["data"]["modifications"] == "Use PostgreSQL instead"

    # Verify approval is now approved
    approval_response = await client.get(f"/api/v1/approvals/{approval_id}")
    assert approval_response.json()["data"]["status"] == "approved"


@pytest.mark.asyncio
async def test_list_pending_approvals(client: AsyncClient, test_session):
    """Test listing pending approvals"""
    # Create multiple approvals
    for i in range(3):
        await client.post(
            f"/api/v1/sessions/{test_session.id}/approvals",
            json={
                "checkpoint_type": f"checkpoint_{i}",
                "decision_needed": f"Decision {i}",
                "options": [
                    {"name": "Option A", "pros": [], "cons": []},
                    {"name": "Option B", "pros": [], "cons": []}
                ]
            }
        )

    # List pending approvals
    response = await client.get(
        f"/api/v1/sessions/{test_session.id}/approvals?status=pending"
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]["approvals"]) == 3


@pytest.mark.asyncio
async def test_cannot_submit_decision_twice(client: AsyncClient, test_session):
    """Test that we cannot submit a decision twice"""
    # Create approval
    create_response = await client.post(
        f"/api/v1/sessions/{test_session.id}/approvals",
        json={
            "checkpoint_type": "test",
            "decision_needed": "Test decision",
            "options": [
                {"name": "Option 1", "pros": [], "cons": []}
            ],
            "recommended_option": 0
        }
    )
    approval_id = create_response.json()["data"]["id"]

    # Submit first decision
    await client.post(
        f"/api/v1/approvals/{approval_id}/decide",
        json={"selected_option": 0}
    )

    # Try to submit second decision
    second_response = await client.post(
        f"/api/v1/approvals/{approval_id}/decide",
        json={"selected_option": 0}
    )

    assert second_response.status_code == 400


@pytest.mark.asyncio
async def test_reject_approval(client: AsyncClient, test_session):
    """Test rejecting an approval checkpoint"""
    # Create approval
    create_response = await client.post(
        f"/api/v1/sessions/{test_session.id}/approvals",
        json={
            "checkpoint_type": "test",
            "decision_needed": "Test decision",
            "options": [
                {"name": "Option 1", "pros": [], "cons": []}
            ]
        }
    )
    approval_id = create_response.json()["data"]["id"]

    # Reject approval
    reject_response = await client.patch(
        f"/api/v1/approvals/{approval_id}?status=rejected&reason=Need more options"
    )

    assert reject_response.status_code == 200
    data = reject_response.json()
    assert data["data"]["status"] == "rejected"
