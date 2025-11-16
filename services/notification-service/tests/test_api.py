"""Tests for Notification API endpoints"""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_root_endpoint():
    """Test root endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "notification-service"
    assert data["status"] == "running"


def test_health_endpoint():
    """Test health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "email" in data
    assert "push" in data
    assert "kafka" in data


def test_get_providers_endpoint():
    """Test get providers endpoint"""
    response = client.get("/api/v1/notifications/providers")
    assert response.status_code == 200
    data = response.json()
    assert "email" in data
    assert "push" in data
    assert "kafka" in data


def test_test_email_validation():
    """Test email validation"""
    # Invalid email
    response = client.post(
        "/api/v1/notifications/test-email",
        json={
            "to_email": "invalid-email",
            "subject": "Test",
            "body": "Test"
        }
    )
    assert response.status_code == 422

    # Missing subject
    response = client.post(
        "/api/v1/notifications/test-email",
        json={
            "to_email": "user@example.com",
            "body": "Test"
        }
    )
    assert response.status_code == 422


def test_test_push_validation():
    """Test push validation"""
    # Missing device token
    response = client.post(
        "/api/v1/notifications/test-push",
        json={
            "title": "Test",
            "body": "Test"
        }
    )
    assert response.status_code == 422

    # Missing title
    response = client.post(
        "/api/v1/notifications/test-push",
        json={
            "device_token": "token",
            "body": "Test"
        }
    )
    assert response.status_code == 422
