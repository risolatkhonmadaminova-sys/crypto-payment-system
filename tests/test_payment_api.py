
from decimal import Decimal
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.db.database import get_db
from app.security.api_key import verify_api_key
from app.api import payments as payments_api


# --------------------------------------------------
# Test data
# --------------------------------------------------

API_KEY = "test-api-key"

PAYMENT_ID = "test-payment-123"

PAYMENT_DATA = {
    "customer_id": 1,
    "order_id": "ORDER-TEST-001",
    "amount": "0.001",
    "currency": "ETH"
}


def create_mock_payment():
    return SimpleNamespace(
        payment_id=PAYMENT_ID,
        customer_id=1,
        order_id="ORDER-TEST-001",
        amount=Decimal("0.001"),
        currency="ETH",
        wallet_address="0x1234567890123456789012345678901234567890",
        status="awaiting_customer_approval"
    )


# --------------------------------------------------
# Fixtures
# --------------------------------------------------

@pytest.fixture
def client():

    def override_get_db():
        yield object()

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[verify_api_key] = lambda: API_KEY

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


# --------------------------------------------------
# Test 1: Create payment
# --------------------------------------------------

def test_create_payment_success(client, monkeypatch):

    def mock_create_payment(db, payment, idempotency_key):
        return create_mock_payment()

    monkeypatch.setattr(
        payments_api,
        "create_payment",
        mock_create_payment
    )

    response = client.post(
        "/api/payments",
        json=PAYMENT_DATA,
        headers={
            "Idempotency-Key": "test-key-001"
        }
    )

    assert response.status_code == 201

    data = response.json()

    assert data["payment_id"] == PAYMENT_ID
    assert data["customer_id"] == 1
    assert data["order_id"] == "ORDER-TEST-001"
    assert data["currency"] == "ETH"
    assert data["status"] == "awaiting_customer_approval"
    assert data["message"] == "Payment request created successfully"


# --------------------------------------------------
# Test 2: Get all payments
# --------------------------------------------------

def test_get_all_payments(client, monkeypatch):

    mock_payment = create_mock_payment()

    def mock_get_payments(db, skip, limit):
        return [mock_payment]

    monkeypatch.setattr(
        payments_api,
        "get_payments",
        mock_get_payments
    )

    response = client.get("/api/payments")

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert data[0]["payment_id"] == PAYMENT_ID
    assert data[0]["customer_id"] == 1
    assert data[0]["currency"] == "ETH"


# --------------------------------------------------
# Test 3: Get one payment
# --------------------------------------------------

def test_get_payment_success(client, monkeypatch):

    mock_payment = create_mock_payment()

    def mock_get_payment(db, payment_id):
        return mock_payment

    monkeypatch.setattr(
        payments_api,
        "get_payment",
        mock_get_payment
    )

    response = client.get(
        f"/api/payments/{PAYMENT_ID}"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["payment_id"] == PAYMENT_ID
    assert data["order_id"] == "ORDER-TEST-001"
    assert data["wallet_address"] == mock_payment.wallet_address


# --------------------------------------------------
# Test 4: Update payment status
# --------------------------------------------------

def test_update_payment_status_success(client, monkeypatch):

    mock_payment = create_mock_payment()
    mock_payment.status = "pending_confirmation"

    def mock_update_payment_status(db, payment_id, new_status):
        return mock_payment

    monkeypatch.setattr(
        payments_api,
        "update_payment_status",
        mock_update_payment_status
    )

    response = client.patch(
        f"/api/payments/{PAYMENT_ID}/status",
        json={
            "status": "pending_confirmation"
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert data["payment_id"] == PAYMENT_ID
    assert data["status"] == "pending_confirmation"


# --------------------------------------------------
# Test 5: Missing API Key
# --------------------------------------------------

def test_missing_api_key(client):

    app.dependency_overrides.pop(verify_api_key)

    response = client.get("/api/payments")

    assert response.status_code == 401

    assert response.json()["detail"] == (
        "Invalid or missing API Key"
    )

    app.dependency_overrides[verify_api_key] = lambda: API_KEY


# --------------------------------------------------
# Test 6: Missing Idempotency-Key
# --------------------------------------------------

def test_missing_idempotency_key(client):

    response = client.post(
        "/api/payments",
        json=PAYMENT_DATA
    )

    assert response.status_code == 422


# --------------------------------------------------
# Test 7: Invalid payment amount
# --------------------------------------------------

def test_invalid_payment_amount(client):

    invalid_data = {
        "customer_id": 1,
        "order_id": "ORDER-TEST-002",
        "amount": "-0.001",
        "currency": "ETH"
    }

    response = client.post(
        "/api/payments",
        json=invalid_data,
        headers={
            "Idempotency-Key": "test-key-002"
        }
    )

    assert response.status_code == 422
