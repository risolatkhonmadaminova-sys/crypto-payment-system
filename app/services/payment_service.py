
import logging
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.db.models import (
    Payment,
    Customer,
    BlockchainTransaction
)

from app.schemas.payment import (
    PaymentCreate,
    PaymentStatus
)

from app.config import MERCHANT_WALLET_ADDRESS

from app.blockchain.blockchain_service import (
    verify_blockchain_transaction
)


logger = logging.getLogger("app")


# ==============================
# Custom exceptions
# ==============================

class PaymentNotFoundError(Exception):
    pass


class InvalidPaymentStatusTransitionError(Exception):
    pass


class CustomerNotFoundError(Exception):
    pass


class CustomerWalletNotLinkedError(Exception):
    pass


class IdempotencyKeyConflictError(Exception):
    pass


# ==============================
# Allowed payment status transitions
# ==============================

ALLOWED_TRANSITIONS = {
    "awaiting_customer_approval": [
        "pending_confirmation",
        "failed"
    ],
    "pending_confirmation": [
        "confirmed",
        "failed"
    ],
    "confirmed": [],
    "failed": []
}


# ==============================
# Idempotency payload validation
# ==============================

def check_idempotency_payload(payment, payment_data):
    """Check whether an existing key belongs to the same request."""

    if (
        payment.customer_id != payment_data.customer_id
        or payment.order_id != payment_data.order_id
        or payment.amount != payment_data.amount
        or payment.currency != payment_data.currency
    ):
        logger.warning(
            "Idempotency key reused with different payment data"
        )

        raise IdempotencyKeyConflictError(
            "Idempotency key has already been used with different payment data"
        )

    return payment


# ==============================
# Create payment with idempotency
# ==============================

def create_payment(
    db: Session,
    payment_data: PaymentCreate,
    idempotency_key: str
):
    logger.info(
        "Payment creation requested: customer_id=%s",
        payment_data.customer_id
    )

    # Step 1: Check whether this key was already used
    existing_payment = db.scalar(
        select(Payment).where(
            Payment.idempotency_key == idempotency_key
        )
    )

    if existing_payment is not None:
        logger.info(
            "Existing payment returned for repeated request: payment_id=%s",
            existing_payment.payment_id
        )

        return check_idempotency_payload(
            existing_payment,
            payment_data
        )

    # Step 2: Find customer
    customer = db.scalar(
        select(Customer).where(
            Customer.id == payment_data.customer_id
        )
    )

    if customer is None:
        logger.warning(
            "Payment creation failed: customer not found"
        )

        raise CustomerNotFoundError("Customer not found")

    # Step 3: Ensure customer has a linked wallet
    if customer.wallet_address is None:
        logger.warning(
            "Payment creation failed: customer wallet is not linked"
        )

        raise CustomerWalletNotLinkedError(
            "Customer has no verified wallet linked"
        )

    # Step 4: Create payment
    new_payment = Payment(
        payment_id=str(uuid4()),
        idempotency_key=idempotency_key,
        customer_id=customer.id,
        order_id=payment_data.order_id,
        amount=payment_data.amount,
        currency=payment_data.currency,
        wallet_address=customer.wallet_address,
        status="awaiting_customer_approval"
    )

    try:
        db.add(new_payment)
        db.commit()
        db.refresh(new_payment)

        logger.info(
            "Payment created successfully: payment_id=%s, customer_id=%s",
            new_payment.payment_id,
            new_payment.customer_id
        )

        return new_payment

    except IntegrityError:
        db.rollback()

        logger.warning(
            "Payment creation integrity error"
        )

        # Another simultaneous request may have created this key
        existing_payment = db.scalar(
            select(Payment).where(
                Payment.idempotency_key == idempotency_key
            )
        )

        if existing_payment is not None:
            logger.info(
                "Existing payment returned after concurrent request: payment_id=%s",
                existing_payment.payment_id
            )

            return check_idempotency_payload(
                existing_payment,
                payment_data
            )

        raise


# ==============================
# Get all payments
# ==============================

def get_payments(
    db: Session,
    skip: int = 0,
    limit: int = 10
):
    return (
        db.query(Payment)
        .order_by(Payment.id.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


# ==============================
# Get one payment
# ==============================

def get_payment(db: Session, payment_id: str):
    payment = (
        db.query(Payment)
        .filter(Payment.payment_id == payment_id)
        .first()
    )

    if payment is None:
        logger.warning(
            "Payment not found: payment_id=%s",
            payment_id
        )

        raise PaymentNotFoundError("Payment not found")

    return payment


# ==============================
# Update payment status
# ==============================

def update_payment_status(
    db: Session,
    payment_id: str,
    new_status: PaymentStatus
):
    payment = get_payment(db, payment_id)

    requested_status = new_status.value

    allowed_statuses = ALLOWED_TRANSITIONS[payment.status]

    if requested_status not in allowed_statuses:
        logger.warning(
            "Invalid payment status transition: payment_id=%s, from=%s, to=%s",
            payment_id,
            payment.status,
            requested_status
        )

        raise InvalidPaymentStatusTransitionError(
            f"Cannot change status from {payment.status} to {requested_status}"
        )

    old_status = payment.status

    payment.status = requested_status

    try:
        db.commit()
        db.refresh(payment)

        logger.info(
            "Payment status updated: payment_id=%s, from=%s, to=%s",
            payment.payment_id,
            old_status,
            payment.status
        )

    except Exception:
        db.rollback()

        logger.exception(
            "Failed to update payment status: payment_id=%s",
            payment_id
        )

        raise

    return payment


# ==============================
# Save and verify blockchain transaction
# ==============================

def save_transaction_hash(
    db: Session,
    payment_id: str,
    transaction_hash: str
):
    logger.info(
        "Blockchain transaction verification requested: payment_id=%s",
        payment_id
    )

    try:
        # Step 1: Find payment
        payment = db.scalar(
            select(Payment).where(
                Payment.payment_id == payment_id
            )
        )

        if payment is None:
            logger.warning(
                "Blockchain verification failed: payment not found"
            )

            raise PaymentNotFoundError("Payment not found")

        # Step 2: Check payment status
        if payment.status != "awaiting_customer_approval":
            logger.warning(
                "Blockchain verification rejected: invalid payment status"
            )

            raise ValueError(
                "Payment is not awaiting customer approval"
            )

        # Step 3: Find existing blockchain transaction
        transaction = db.scalar(
            select(BlockchainTransaction).where(
                BlockchainTransaction.payment_id == payment_id
            )
        )

        # Step 4: Prevent duplicate hash assignment
        if (
            transaction is not None
            and transaction.transaction_hash is not None
        ):
            raise ValueError(
                "Transaction hash has already been saved"
            )

        # Step 5: Verify transaction directly on Sepolia
        verification = verify_blockchain_transaction(
            transaction_hash=transaction_hash,
            expected_sender=payment.wallet_address,
            expected_recipient=MERCHANT_WALLET_ADDRESS,
            expected_amount=payment.amount
        )

        # Step 6: Create transaction record if needed
        if transaction is None:
            transaction = BlockchainTransaction(
                payment_id=payment.payment_id,
                from_address=verification["from_address"],
                to_address=verification["to_address"],
                amount=payment.amount,
                network="sepolia",
                status="confirmed"
            )

            db.add(transaction)

        # Step 7: Save verified transaction information
        transaction.transaction_hash = transaction_hash
        transaction.from_address = verification["from_address"]
        transaction.to_address = verification["to_address"]
        transaction.status = "confirmed"

        payment.status = "confirmed"

        # Step 8: Save changes to PostgreSQL
        db.commit()
        db.refresh(transaction)

        logger.info(
            "Blockchain transaction verified successfully: payment_id=%s",
            payment_id
        )

        return transaction

    except Exception:
        db.rollback()

        logger.exception(
            "Blockchain transaction processing failed: payment_id=%s",
            payment_id
        )

        raise
