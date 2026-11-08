
import pytest

from fastapi.testclient import TestClient

from app.main import app
from app.db.database import get_db
from app.api import wallet as wallet_api
from app.services.wallet_service import (
    WalletChallengeNotFoundError,
    WalletChallengeExpiredError,
    WalletChallengeAlreadyUsedError,
    WalletSignatureInvalidError,
    CustomerNotFoundError,
    WalletAlreadyLinkedError
)

from app.security.rate_limiter import limiter


# --------------------------------------------------
# Test data
# --------------------------------------------------

WALLET_ADDRESS = "0x1234567890123456789012345678901234567890"

CUSTOMER_ID = 1

NONCE = "test-nonce-123456"

SIGNATURE = "0x" + "a" * 130

CHALLENGE_DATA = {
    "customer_id": CUSTOMER_ID,
    "wallet_address": WALLET_ADDRESS
}

VERIFICATION_DATA = {
    "customer_id": CUSTOMER_ID,
    "nonce": NONCE,
    "signature": SIGNATURE
}

TEST_ACCESS_TOKEN = "test-access-token"


# --------------------------------------------------
# Fixtures
# --------------------------------------------------

@pytest.fixture
def client():

    def override_get_db():
        yield object()

    app.dependency_overrides[get_db] = override_get_db

    # Reset rate limiter storage before each test.
    limiter._storage.reset()

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


# --------------------------------------------------
# Test 1: Create wallet challenge successfully
# --------------------------------------------------

def test_create_wallet_challenge_success(client, monkeypatch):

    def mock_create_challenge(*args, **kwargs):
        return {
            "nonce": NONCE,
            "message": "Test wallet verification message",
            "expires_at": "2026-11-07T22:00:00+00:00"
        }

    monkeypatch.setattr(
        wallet_api,
        "create_wallet_challenge",
        mock_create_challenge
    )

    response = client.post(
        "/api/wallet/challenge",
        json=CHALLENGE_DATA
    )

    assert response.status_code == 200

    data = response.json()

    assert data["nonce"] == NONCE
    assert data["message"] == "Test wallet verification message"
    assert "expires_at" in data


# --------------------------------------------------
# Test 2: Invalid wallet address
# --------------------------------------------------

def test_create_wallet_challenge_invalid_address(client):

    invalid_data = {
        "customer_id": CUSTOMER_ID,
        "wallet_address": "invalid-wallet-address"
    }

    response = client.post(
        "/api/wallet/challenge",
        json=invalid_data
    )

    assert response.status_code == 422


# --------------------------------------------------
# Test 3: Wallet challenge service error
# --------------------------------------------------

def test_create_wallet_challenge_value_error(client, monkeypatch):

    def mock_create_challenge(*args, **kwargs):
        raise ValueError("Invalid Ethereum wallet address")

    monkeypatch.setattr(
        wallet_api,
        "create_wallet_challenge",
        mock_create_challenge
    )

    response = client.post(
        "/api/wallet/challenge",
        json=CHALLENGE_DATA
    )

    assert response.status_code == 400

    assert response.json()["detail"] == (
        "Invalid Ethereum wallet address"
    )


# --------------------------------------------------
# Test 4: Verify wallet successfully
# --------------------------------------------------

def test_verify_wallet_success(client, monkeypatch):

    def mock_verify_wallet(
        db,
        customer_id,
        nonce,
        signature
    ):
        return {
            "verified": True,
            "wallet_address": WALLET_ADDRESS,
            "message": "Wallet verified and linked to customer successfully",
            "access_token": TEST_ACCESS_TOKEN,
            "token_type": "bearer"
        }

    monkeypatch.setattr(
        wallet_api,
        "verify_wallet_signature",
        mock_verify_wallet
    )

    response = client.post(
        "/api/wallet/verify",
        json=VERIFICATION_DATA
    )

    assert response.status_code == 200

    data = response.json()

    assert data["verified"] is True
    assert data["wallet_address"] == WALLET_ADDRESS
    assert data["message"] == (
        "Wallet verified and linked to customer successfully"
    )
    assert data["access_token"] == TEST_ACCESS_TOKEN
    assert data["token_type"] == "bearer"


# --------------------------------------------------
# Test 5: Wallet challenge not found
# --------------------------------------------------

def test_verify_wallet_challenge_not_found(client, monkeypatch):

    def mock_verify_wallet(*args, **kwargs):
        raise WalletChallengeNotFoundError(
            "Wallet challenge not found"
        )

    monkeypatch.setattr(
        wallet_api,
        "verify_wallet_signature",
        mock_verify_wallet
    )

    response = client.post(
        "/api/wallet/verify",
        json=VERIFICATION_DATA
    )

    assert response.status_code == 404

    assert response.json()["detail"] == (
        "Wallet challenge not found"
    )


# --------------------------------------------------
# Test 6: Wallet challenge already used
# --------------------------------------------------

def test_verify_wallet_challenge_already_used(client, monkeypatch):

    def mock_verify_wallet(*args, **kwargs):
        raise WalletChallengeAlreadyUsedError(
            "This wallet challenge has already been used"
        )

    monkeypatch.setattr(
        wallet_api,
        "verify_wallet_signature",
        mock_verify_wallet
    )

    response = client.post(
        "/api/wallet/verify",
        json=VERIFICATION_DATA
    )

    assert response.status_code == 409

    assert response.json()["detail"] == (
        "This wallet challenge has already been used"
    )


# --------------------------------------------------
# Test 7: Wallet challenge expired
# --------------------------------------------------

def test_verify_wallet_challenge_expired(client, monkeypatch):

    def mock_verify_wallet(*args, **kwargs):
        raise WalletChallengeExpiredError(
            "Wallet challenge has expired"
        )

    monkeypatch.setattr(
        wallet_api,
        "verify_wallet_signature",
        mock_verify_wallet
    )

    response = client.post(
        "/api/wallet/verify",
        json=VERIFICATION_DATA
    )

    assert response.status_code == 410

    assert response.json()["detail"] == (
        "Wallet challenge has expired"
    )


# --------------------------------------------------
# Test 8: Invalid wallet signature
# --------------------------------------------------

def test_verify_wallet_invalid_signature(client, monkeypatch):

    def mock_verify_wallet(*args, **kwargs):
        raise WalletSignatureInvalidError(
            "Invalid wallet signature"
        )

    monkeypatch.setattr(
        wallet_api,
        "verify_wallet_signature",
        mock_verify_wallet
    )

    response = client.post(
        "/api/wallet/verify",
        json=VERIFICATION_DATA
    )

    assert response.status_code == 400

    assert response.json()["detail"] == (
        "Invalid wallet signature"
    )


# --------------------------------------------------
# Test 9: Customer not found
# --------------------------------------------------

def test_verify_wallet_customer_not_found(client, monkeypatch):

    def mock_verify_wallet(*args, **kwargs):
        raise CustomerNotFoundError(
            "Customer not found"
        )

    monkeypatch.setattr(
        wallet_api,
        "verify_wallet_signature",
        mock_verify_wallet
    )

    response = client.post(
        "/api/wallet/verify",
        json=VERIFICATION_DATA
    )

    assert response.status_code == 404

    assert response.json()["detail"] == (
        "Customer not found"
    )


# --------------------------------------------------
# Test 10: Wallet already linked
# --------------------------------------------------

def test_verify_wallet_already_linked(client, monkeypatch):

    def mock_verify_wallet(*args, **kwargs):
        raise WalletAlreadyLinkedError(
            "This wallet is already linked to another customer"
        )

    monkeypatch.setattr(
        wallet_api,
        "verify_wallet_signature",
        mock_verify_wallet
    )

    response = client.post(
        "/api/wallet/verify",
        json=VERIFICATION_DATA
    )

    assert response.status_code == 409

    assert response.json()["detail"] == (
        "This wallet is already linked to another customer"
    )


# --------------------------------------------------
# Test 11: Invalid customer ID
# --------------------------------------------------

def test_verify_wallet_invalid_customer_id(client):

    invalid_data = {
        "customer_id": 0,
        "nonce": NONCE,
        "signature": SIGNATURE
    }

    response = client.post(
        "/api/wallet/verify",
        json=invalid_data
    )

    assert response.status_code == 422


# --------------------------------------------------
# Test 12: Invalid signature format
# --------------------------------------------------

def test_verify_wallet_invalid_signature_format(client):

    invalid_data = {
        "customer_id": CUSTOMER_ID,
        "nonce": NONCE,
        "signature": "invalid-signature"
    }

    response = client.post(
        "/api/wallet/verify",
        json=invalid_data
    )

    assert response.status_code == 422
