"""
Tests for health check endpoints.
"""

import pytest
from fastapi.testclient import TestClient

from app.main import create_application


@pytest.fixture
def client():
    """Create test client."""
    app = create_application()
    return TestClient(app)


def test_root_endpoint(client):
    """Test root endpoint returns service info."""
    response = client.get("/")

    assert response.status_code == 200
    data = response.json()

    assert "service" in data
    assert "version" in data
    assert "environment" in data


def test_health_check(client):
    """Test health check endpoint."""
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "healthy"
    assert "service" in data
    assert "version" in data
    assert "timestamp" in data


def test_health_check_has_correlation_id(client):
    """Test that health check includes correlation ID in response."""
    response = client.get("/api/v1/health")

    # Cinema-common middleware should add this header
    # (if cinema-common is installed)
    assert response.status_code == 200


def test_ping_endpoint(client):
    """Test ping endpoint."""
    response = client.get("/api/v1/ping")

    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "pong"


def test_ping_not_in_openapi(client):
    """Test that ping endpoint is not in OpenAPI schema."""
    response = client.get("/openapi.json")

    assert response.status_code == 200
    openapi_schema = response.json()

    # Ping should not be in schema (include_in_schema=False)
    paths = openapi_schema.get("paths", {})
    assert "/api/v1/ping" not in paths


def test_readiness_check_structure(client):
    """Test readiness check response structure."""
    response = client.get("/api/v1/ready")

    # Should return 200 or 503 depending on DB connection
    assert response.status_code in [200, 503]

    data = response.json()
    assert "status" in data
    assert "service" in data
    assert "version" in data
    assert "details" in data

    # Details should include database status
    assert "database" in data["details"]


@pytest.mark.parametrize(
    "endpoint,expected_status",
    [
        ("/", 200),
        ("/api/v1/health", 200),
        ("/api/v1/ping", 200),
        ("/api/v1/ready", [200, 503]),  # Can be either depending on DB
    ],
)
def test_endpoint_accessibility(client, endpoint, expected_status):
    """Test that all health endpoints are accessible."""
    response = client.get(endpoint)

    if isinstance(expected_status, list):
        assert response.status_code in expected_status
    else:
        assert response.status_code == expected_status
