"""Test session API endpoints"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_session(client: AsyncClient):
    """Test creating a new session"""
    response = await client.post(
        "/api/v1/sessions",
        json={"title": "My First Session"}
    )

    assert response.status_code == 201
    data = response.json()
    assert "data" in data
    assert data["data"]["title"] == "My First Session"
    assert data["data"]["status"] == "active"


@pytest.mark.asyncio
async def test_get_session(client: AsyncClient, test_session):
    """Test getting session details"""
    response = await client.get(f"/api/v1/sessions/{test_session.id}")

    assert response.status_code == 200
    data = response.json()
    assert data["data"]["id"] == str(test_session.id)
    assert data["data"]["title"] == test_session.title


@pytest.mark.asyncio
async def test_update_session(client: AsyncClient, test_session):
    """Test updating a session"""
    response = await client.patch(
        f"/api/v1/sessions/{test_session.id}",
        json={"status": "paused"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["data"]["status"] == "paused"


@pytest.mark.asyncio
async def test_list_sessions(client: AsyncClient, test_session):
    """Test listing sessions"""
    response = await client.get("/api/v1/sessions")

    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert "sessions" in data["data"]
    assert len(data["data"]["sessions"]) > 0


@pytest.mark.asyncio
async def test_delete_session(client: AsyncClient, test_session):
    """Test deleting a session"""
    response = await client.delete(f"/api/v1/sessions/{test_session.id}")

    assert response.status_code == 204

    # Verify deleted
    get_response = await client.get(f"/api/v1/sessions/{test_session.id}")
    assert get_response.status_code == 404
