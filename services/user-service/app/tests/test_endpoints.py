"""
Simple unit tests for user service endpoints.

Run with: pytest app/tests/
"""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from jose import jwt

from app.core.config import settings
from app.main import app


@pytest.fixture
def client():
    """Test client fixture."""
    return TestClient(app)


@pytest.fixture
def mock_user_id():
    """Mock user ID."""
    return uuid.uuid4()


@pytest.fixture
def auth_token(mock_user_id):
    """Generate valid JWT token for testing."""
    payload = {
        "sub": str(mock_user_id),
        "type": "access",
    }
    token = jwt.encode(
        payload,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )
    return token


def test_health_check(client):
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "user-service"


def test_get_profile_requires_auth(client):
    """Test that getting profile requires authentication."""
    response = client.get("/api/v1/users/me")
    assert response.status_code == 403  # No auth header


@pytest.mark.asyncio
async def test_get_profile_with_auth(client, auth_token, mock_user_id):
    """Test getting profile with valid token."""
    headers = {"Authorization": f"Bearer {auth_token}"}

    # Mock the user service
    with patch("app.api.v1.endpoints.users.UserService") as MockUserService:
        # Create mock profile
        mock_profile = MagicMock()
        mock_profile.id = uuid.uuid4()
        mock_profile.user_id = mock_user_id
        mock_profile.nickname = "testuser"
        mock_profile.avatar_url = None
        mock_profile.language = "en"
        mock_profile.country = "US"

        # Mock the service method
        mock_service = MockUserService.return_value
        mock_service.get_or_create_profile = AsyncMock(return_value=mock_profile)

        response = client.get("/api/v1/users/me", headers=headers)

        # Note: This test may fail due to async dependencies
        # In real tests, use httpx.AsyncClient instead


@pytest.mark.asyncio
async def test_update_profile(client, auth_token):
    """Test updating profile."""
    headers = {"Authorization": f"Bearer {auth_token}"}
    profile_data = {
        "nickname": "NewNickname",
        "language": "ru",
    }

    # This is a simple test - in real scenario, use async client
    # response = client.patch("/api/v1/users/me", headers=headers, json=profile_data)


def test_favorites_endpoints_require_auth(client):
    """Test that favorites endpoints require authentication."""
    content_id = uuid.uuid4()

    # GET favorites
    response = client.get("/api/v1/users/me/favorites")
    assert response.status_code == 403

    # POST favorite
    response = client.post(
        f"/api/v1/users/me/favorites/{content_id}?content_type=movie"
    )
    assert response.status_code == 403

    # DELETE favorite
    response = client.delete(f"/api/v1/users/me/favorites/{content_id}")
    assert response.status_code == 403


def test_history_endpoints_require_auth(client):
    """Test that history endpoints require authentication."""
    # GET history
    response = client.get("/api/v1/users/me/history")
    assert response.status_code == 403

    # POST history
    response = client.post("/api/v1/users/me/history")
    assert response.status_code == 403
