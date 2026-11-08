from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.db.database import get_db
from app.security.jwt import verify_merchant_access_token
from app.api import refunds as refunds_api


PAYMENT_ID = "63213223-8109-4ee4-8567-fcc14c13bb27"
TRANSACTION_HASH = "0x" + "a" * 64


@pytest.fixture
def client():
    def override_get_db():
        yield object()

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[verify_merchant_access_token] = (
        lambda: {
            "sub": "merchant",
            "role": "merchant",
            "wallet_address": "0x" + "1" * 40
        }
    )

    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.clear()


@pytest.fixture
def refund():
    return SimpleNamespace(
        payment_id=PAYMENT_ID,
        amount=Decimal("0.00100000"),
        from_address="0x" + "1" * 40,
        to_address="0x" + "2" * 40,
        transaction_hash=None,
        status="pending"
    )


def test_create_refund_success(client, refund):
    with patch.object(refunds_api, "create_refund", return_value=refund):
        response = client.post(
            "/api/refunds/",
            json={"payment_id": PAYMENT_ID}
        )

    assert response.status_code == 200
    assert response.json()["payment_id"] == PAYMENT_ID
    assert response.json()["status"] == "pending"
    assert response.json()["network"] == "sepolia"


def test_create_refund_payment_not_found(client):
    with patch.object(
        refunds_api,
        "create_refund",
        side_effect=ValueError("Payment not found")
    ):
        response = client.post(
            "/api/refunds/",
            json={"payment_id": PAYMENT_ID}
        )

    assert response.status_code == 400
    assert response.json()["detail"] == "Payment not found"


def test_prepare_refund_success(client):
    prepared_data = {
        "payment_id": PAYMENT_ID,
        "from": "0x" + "1" * 40,
        "to": "0x" + "2" * 40,
        "value_wei": 1000000000000000,
        "chain_id": 11155111,
        "estimated_gas": 21000,
        "estimated_gas_fee_wei": 100000000000,
        "status": "awaiting_merchant_approval",
        "network": "sepolia"
    }

    with patch.object(
        refunds_api,
        "prepare_refund",
        return_value=prepared_data
    ):
        response = client.post(
            f"/api/refunds/{PAYMENT_ID}/prepare"
        )

    assert response.status_code == 200
    assert response.json()["payment_id"] == PAYMENT_ID
    assert response.json()["chain_id"] == 11155111
    assert response.json()["status"] == "awaiting_merchant_approval"


def test_prepare_refund_not_found(client):
    with patch.object(
        refunds_api,
        "prepare_refund",
        side_effect=ValueError("Refund not found")
    ):
        response = client.post(
            f"/api/refunds/{PAYMENT_ID}/prepare"
        )

    assert response.status_code == 400
    assert response.json()["detail"] == "Refund not found"


def test_save_refund_transaction_success(client, refund):
    refund.transaction_hash = TRANSACTION_HASH
    refund.status = "confirmed"

    with patch.object(
        refunds_api,
        "save_refund_transaction",
        return_value=refund
    ):
        response = client.post(
            "/api/refunds/save-transaction",
            json={
                "payment_id": PAYMENT_ID,
                "transaction_hash": TRANSACTION_HASH
            }
        )

    assert response.status_code == 200
    assert response.json()["payment_id"] == PAYMENT_ID
    assert response.json()["transaction_hash"] == TRANSACTION_HASH
    assert response.json()["status"] == "confirmed"
    assert response.json()["network"] == "sepolia"


def test_save_refund_transaction_not_found(client):
    with patch.object(
        refunds_api,
        "save_refund_transaction",
        side_effect=ValueError("Refund not found")
    ):
        response = client.post(
            "/api/refunds/save-transaction",
            json={
                "payment_id": PAYMENT_ID,
                "transaction_hash": TRANSACTION_HASH
            }
        )

    assert response.status_code == 400
    assert response.json()["detail"] == "Refund not found"


def test_save_refund_transaction_invalid_hash(client):
    response = client.post(
        "/api/refunds/save-transaction",
        json={
            "payment_id": PAYMENT_ID,
            "transaction_hash": "invalid_hash"
        }
    )

    assert response.status_code == 422


def test_create_refund_without_merchant_token():
    def override_get_db():
        yield object()

    app.dependency_overrides[get_db] = override_get_db

    try:
        with TestClient(app) as test_client:
            response = test_client.post(
                "/api/refunds/",
                json={"payment_id": PAYMENT_ID}
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 401
    assert response.json()["detail"] == (
        "Missing merchant authentication token"
    )