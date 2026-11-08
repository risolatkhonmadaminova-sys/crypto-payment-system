
import pytest

from decimal import Decimal
from types import SimpleNamespace

from app.services.payment_service import (
    check_idempotency_payload,
    IdempotencyKeyConflictError,
    create_payment,
    CustomerNotFoundError,
    CustomerWalletNotLinkedError,
    update_payment_status,
    InvalidPaymentStatusTransitionError
)
from unittest.mock import MagicMock

from app.schemas.payment import PaymentCreate
from app.schemas.payment import PaymentStatus

# Test 1: Same payment data
def test_idempotency_accepts_same_payment_data():

    existing_payment = SimpleNamespace(
        customer_id=1,
        order_id="ORDER-001",
        amount=Decimal("0.001"),
        currency="ETH"
    )

    new_payment_data = SimpleNamespace(
        customer_id=1,
        order_id="ORDER-001",
        amount=Decimal("0.001"),
        currency="ETH"
    )

    result = check_idempotency_payload(
        existing_payment,
        new_payment_data
    )

    assert result is existing_payment


# Test 2: Different payment amount
def test_idempotency_rejects_different_amount():

    existing_payment = SimpleNamespace(
        customer_id=1,
        order_id="ORDER-001",
        amount=Decimal("0.001"),
        currency="ETH"
    )

    new_payment_data = SimpleNamespace(
        customer_id=1,
        order_id="ORDER-001",
        amount=Decimal("0.002"),
        currency="ETH"
    )

    with pytest.raises(IdempotencyKeyConflictError):
        check_idempotency_payload(
            existing_payment,
            new_payment_data
        )


# Test 3: Different order ID
def test_idempotency_rejects_different_order():

    existing_payment = SimpleNamespace(
        customer_id=1,
        order_id="ORDER-001",
        amount=Decimal("0.001"),
        currency="ETH"
    )

    new_payment_data = SimpleNamespace(
        customer_id=1,
        order_id="ORDER-002",
        amount=Decimal("0.001"),
        currency="ETH"
    )

    with pytest.raises(IdempotencyKeyConflictError):
        check_idempotency_payload(
            existing_payment,
            new_payment_data
        )

# Test 4: Successful payment creation
def test_create_payment_successfully():

    db = MagicMock()

    customer = SimpleNamespace(
        id=1,
        wallet_address="0x1234567890123456789012345678901234567890"
    )

    # First query: no existing payment
    # Second query: customer found
    db.scalar.side_effect = [None, customer]

    payment_data = PaymentCreate(
        customer_id=1,
        order_id="ORDER-TEST-001",
        amount=Decimal("0.001"),
        currency="ETH"
    )

    result = create_payment(
        db,
        payment_data,
        "test-key-001"
    )

    assert result.customer_id == 1
    assert result.order_id == "ORDER-TEST-001"
    assert result.amount == Decimal("0.001")
    assert result.currency == "ETH"
    assert result.status == "awaiting_customer_approval"

    db.add.assert_called_once()
    db.commit.assert_called_once()
    db.refresh.assert_called_once()


# Test 5: Customer does not exist
def test_create_payment_customer_not_found():

    db = MagicMock()

    db.scalar.side_effect = [None, None]

    payment_data = PaymentCreate(
        customer_id=999,
        order_id="ORDER-TEST-002",
        amount=Decimal("0.001"),
        currency="ETH"
    )

    with pytest.raises(CustomerNotFoundError):
        create_payment(
            db,
            payment_data,
            "test-key-002"
        )

    db.add.assert_not_called()
    db.commit.assert_not_called()


# Test 6: Customer has no linked wallet
def test_create_payment_without_wallet():

    db = MagicMock()

    customer = SimpleNamespace(
        id=1,
        wallet_address=None
    )

    db.scalar.side_effect = [None, customer]

    payment_data = PaymentCreate(
        customer_id=1,
        order_id="ORDER-TEST-003",
        amount=Decimal("0.001"),
        currency="ETH"
    )

    with pytest.raises(CustomerWalletNotLinkedError):
        create_payment(
            db,
            payment_data,
            "test-key-003"
        )

    db.add.assert_not_called()
    db.commit.assert_not_called()


# Test 7: Existing idempotency key returns existing payment
def test_create_payment_returns_existing_payment():

    db = MagicMock()

    existing_payment = SimpleNamespace(
        payment_id="existing-payment-001",
        customer_id=1,
        order_id="ORDER-TEST-004",
        amount=Decimal("0.001"),
        currency="ETH"
    )

    db.scalar.return_value = existing_payment

    payment_data = PaymentCreate(
        customer_id=1,
        order_id="ORDER-TEST-004",
        amount=Decimal("0.001"),
        currency="ETH"
    )

    result = create_payment(
        db,
        payment_data,
        "test-key-004"
    )

    assert result is existing_payment

    db.add.assert_not_called()
    db.commit.assert_not_called()


# Test 8: Valid transition to pending_confirmation
def test_payment_status_awaiting_to_pending():

    db = MagicMock()

    payment = SimpleNamespace(
        payment_id="payment-001",
        status="awaiting_customer_approval"
    )

    db.query.return_value.filter.return_value.first.return_value = payment

    new_status = SimpleNamespace(
        value="pending_confirmation"
    )

    result = update_payment_status(
        db,
        "payment-001",
        new_status
    )

    assert result.status == "pending_confirmation"

    db.commit.assert_called_once()
    db.refresh.assert_called_once_with(payment)


# Test 9: Valid transition to confirmed
def test_payment_status_pending_to_confirmed():

    db = MagicMock()

    payment = SimpleNamespace(
        payment_id="payment-002",
        status="pending_confirmation"
    )

    db.query.return_value.filter.return_value.first.return_value = payment

    new_status = SimpleNamespace(
        value="confirmed"
    )

    result = update_payment_status(
        db,
        "payment-002",
        new_status
    )

    assert result.status == "confirmed"

    db.commit.assert_called_once()


# Test 10: Valid transition to failed
def test_payment_status_awaiting_to_failed():

    db = MagicMock()

    payment = SimpleNamespace(
        payment_id="payment-003",
        status="awaiting_customer_approval"
    )

    db.query.return_value.filter.return_value.first.return_value = payment

    new_status = SimpleNamespace(
        value="failed"
    )

    result = update_payment_status(
        db,
        "payment-003",
        new_status
    )

    assert result.status == "failed"

    db.commit.assert_called_once()


# Test 11: Invalid transition from confirmed
def test_payment_status_confirmed_cannot_change():

    db = MagicMock()

    payment = SimpleNamespace(
        payment_id="payment-004",
        status="confirmed"
    )

    db.query.return_value.filter.return_value.first.return_value = payment

    new_status = SimpleNamespace(
        value="failed"
    )

    with pytest.raises(InvalidPaymentStatusTransitionError):
        update_payment_status(
            db,
            "payment-004",
            new_status
        )

    db.commit.assert_not_called()
