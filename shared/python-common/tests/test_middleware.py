"""
Tests for middleware components.
"""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from middleware.correlation_id import CorrelationIdMiddleware, get_correlation_id
from middleware.error_handler import (
    BadRequestException,
    CinemaException,
    NotFoundException,
    setup_error_handlers,
)


@pytest.fixture
def app():
    """Create test FastAPI app."""
    app = FastAPI()
    app.add_middleware(CorrelationIdMiddleware)
    setup_error_handlers(app)

    @app.get("/test")
    async def test_endpoint():
        return {"correlation_id": get_correlation_id()}

    @app.get("/error/not-found")
    async def error_not_found():
        raise NotFoundException("Resource not found")

    @app.get("/error/bad-request")
    async def error_bad_request():
        raise BadRequestException("Invalid input")

    @app.get("/error/custom")
    async def error_custom():
        raise CinemaException(
            message="Custom error",
            status_code=418,
            error_code="TEAPOT",
        )

    return app


@pytest.fixture
def client(app):
    """Create test client."""
    return TestClient(app)


def test_correlation_id_generated(client):
    """Test that correlation ID is generated if not provided."""
    response = client.get("/test")

    assert response.status_code == 200
    assert "X-Correlation-ID" in response.headers
    assert response.json()["correlation_id"] is not None


def test_correlation_id_propagated(client):
    """Test that correlation ID is propagated from request."""
    correlation_id = "test-correlation-123"

    response = client.get(
        "/test",
        headers={"X-Correlation-ID": correlation_id}
    )

    assert response.status_code == 200
    assert response.headers["X-Correlation-ID"] == correlation_id
    assert response.json()["correlation_id"] == correlation_id


def test_not_found_exception(client):
    """Test NotFoundException handling."""
    response = client.get("/error/not-found")

    assert response.status_code == 404
    data = response.json()
    assert data["error"] == "NOT_FOUND"
    assert data["message"] == "Resource not found"
    assert "correlation_id" in data


def test_bad_request_exception(client):
    """Test BadRequestException handling."""
    response = client.get("/error/bad-request")

    assert response.status_code == 400
    data = response.json()
    assert data["error"] == "BAD_REQUEST"
    assert data["message"] == "Invalid input"


def test_custom_exception(client):
    """Test custom CinemaException handling."""
    response = client.get("/error/custom")

    assert response.status_code == 418
    data = response.json()
    assert data["error"] == "TEAPOT"
    assert data["message"] == "Custom error"
