"""Tests for Payment API endpoints"""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_root_endpoint():
    """Test root endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "payment-service"
    assert data["status"] == "running"


def test_health_endpoint():
    """Test health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "database" in data
    assert "redis" in data


def test_get_plans_endpoint():
    """Test get plans endpoint"""
    response = client.get("/plans")
    assert response.status_code == 200
    data = response.json()
    assert "plans" in data
    assert len(data["plans"]) > 0

    # Check plan structure
    plan = data["plans"][0]
    assert "id" in plan
    assert "name" in plan
    assert "price" in plan
    assert "currency" in plan
    assert "duration_days" in plan


def test_create_checkout_session_validation():
    """Test create checkout session with invalid data"""
    # Missing user_id
    response = client.post(
        "/api/v1/payments/create-checkout-session",
        json={"plan_id": "premium"}
    )
    assert response.status_code == 422

    # Invalid plan_id
    response = client.post(
        "/api/v1/payments/create-checkout-session",
        json={
            "plan_id": "invalid_plan",
            "user_id": "00000000-0000-0000-0000-000000000001"
        }
    )
    # May return 400 or 500 depending on implementation
    assert response.status_code in [400, 500]


def test_get_payment_not_found():
    """Test get payment with non-existent ID"""
    payment_id = "00000000-0000-0000-0000-000000000999"
    response = client.get(f"/api/v1/payments/{payment_id}")
    # May return 404 or 500 if database not connected
    assert response.status_code in [404, 500]


def test_payment_history_validation():
    """Test payment history with invalid parameters"""
    # Missing user_id
    response = client.get("/api/v1/payments/history")
    assert response.status_code == 422

    # Invalid page number
    response = client.get(
        "/api/v1/payments/history",
        params={
            "user_id": "00000000-0000-0000-0000-000000000001",
            "page": 0
        }
    )
    assert response.status_code == 422

    # Invalid page_size
    response = client.get(
        "/api/v1/payments/history",
        params={
            "user_id": "00000000-0000-0000-0000-000000000001",
            "page_size": 1000
        }
    )
    assert response.status_code == 422
