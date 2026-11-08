
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Payment, Refund
from app.config import MERCHANT_WALLET_ADDRESS
from app.blockchain.blockchain_service import (
    prepare_refund_transaction,
    verify_refund_transaction
)


def create_refund(
    db: Session,
    payment_id: str
):
    # Step 1: Find original payment
    payment = db.scalar(
        select(Payment).where(
            Payment.payment_id == payment_id
        )
    )

    if payment is None:
        raise ValueError("Payment not found")

    # Step 2: Check payment status
    if payment.status != "confirmed":
        raise ValueError(
            "Only confirmed payments can be refunded"
        )

    # Step 3: Check whether refund already exists
    existing_refund = db.scalar(
        select(Refund).where(
            Refund.payment_id == payment_id
        )
    )

    if existing_refund is not None:
        raise ValueError(
            "Refund already exists for this payment"
        )

    # Step 4: Create refund record
    refund = Refund(
        payment_id=payment.payment_id,
        amount=payment.amount,
        from_address=MERCHANT_WALLET_ADDRESS,
        to_address=payment.wallet_address,
        status="pending"
    )

    # Step 5: Save refund in database
    db.add(refund)
    db.commit()
    db.refresh(refund)

    return refund


def prepare_refund(
    db: Session,
    payment_id: str
):
    # Step 1: Find refund
    refund = db.scalar(
        select(Refund).where(
            Refund.payment_id == payment_id
        )
    )

    if refund is None:
        raise ValueError("Refund not found")

    # Step 2: Check refund status
    if refund.status != "pending":
        raise ValueError(
            "Refund is not awaiting processing"
        )

    # Step 3: Prepare blockchain transaction
    transaction_data = prepare_refund_transaction(
        recipient_address=refund.to_address,
        amount_eth=refund.amount
    )

    # Step 4: Return unsigned transaction
    return {
        "payment_id": refund.payment_id,
        "from": transaction_data["from"],
        "to": transaction_data["to"],
        "value_wei": transaction_data["value_wei"],
        "chain_id": transaction_data["chain_id"],
        "estimated_gas": transaction_data["estimated_gas"],
        "estimated_gas_fee_wei": (
            transaction_data["estimated_gas_fee_wei"]
        ),
        "status": "awaiting_merchant_approval",
        "network": "sepolia"
    }

def save_refund_transaction(
    db: Session,
    payment_id: str,
    transaction_hash: str
):
    # Step 1: Find refund
    refund = db.scalar(
        select(Refund).where(
            Refund.payment_id == payment_id
        )
    )

    if refund is None:
        raise ValueError("Refund not found")

    # Step 2: Check refund status
    if refund.status != "pending":
        raise ValueError(
            "Refund is not awaiting processing"
        )

    # Step 3: Find original payment
    payment = db.scalar(
        select(Payment).where(
            Payment.payment_id == payment_id
        )
    )

    if payment is None:
        raise ValueError("Payment not found")

    # Step 4: Verify blockchain transaction
    verification = verify_refund_transaction(
        transaction_hash=transaction_hash,
        expected_sender=refund.from_address,
        expected_recipient=refund.to_address,
        expected_amount=refund.amount
    )

    # Step 5: Save refund transaction
    refund.transaction_hash = (
        verification["transaction_hash"]
    )

    refund.status = "confirmed"

    # Step 6: Update original payment status
    payment.status = "refunded"

    # Step 7: Save changes
    db.commit()

    db.refresh(refund)
    db.refresh(payment)

    return refund