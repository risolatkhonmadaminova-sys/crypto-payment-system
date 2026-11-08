
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.refund import RefundCreate, RefundResponse
from app.services.refund_service import (
    create_refund,
    prepare_refund,
    save_refund_transaction
)
from app.schemas.refund import RefundTransactionHashCreate
from app.security.jwt import verify_merchant_access_token


router = APIRouter(
    prefix="/api/refunds",
    tags=["Refunds"]
)


@router.post("/", response_model=RefundResponse)
def create_refund_endpoint(
    refund_data: RefundCreate,
    db: Session = Depends(get_db),
    merchant: dict = Depends(verify_merchant_access_token)
):
    try:
        refund = create_refund(
            db=db,
            payment_id=refund_data.payment_id
        )

        return {
            "payment_id": refund.payment_id,
            "amount": refund.amount,
            "from_address": refund.from_address,
            "to_address": refund.to_address,
            "transaction_hash": refund.transaction_hash,
            "status": refund.status,
            "network": "sepolia"
        }

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error)
        )


@router.post("/{payment_id}/prepare")
def prepare_refund_endpoint(
    payment_id: str,
    db: Session = Depends(get_db),
    merchant: dict = Depends(verify_merchant_access_token)
):
    try:
        return prepare_refund(
            db=db,
            payment_id=payment_id
        )

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error)
        )

    except RuntimeError as error:
        raise HTTPException(
            status_code=500,
            detail=str(error)
        )

@router.post("/save-transaction")
def save_refund_transaction_endpoint(
    data: RefundTransactionHashCreate,
    db: Session = Depends(get_db),
    merchant: dict = Depends(verify_merchant_access_token)
):
    try:
        refund = save_refund_transaction(
            db=db,
            payment_id=data.payment_id,
            transaction_hash=data.transaction_hash
        )

        return {
            "payment_id": refund.payment_id,
            "transaction_hash": refund.transaction_hash,
            "amount": str(refund.amount),
            "from_address": refund.from_address,
            "to_address": refund.to_address,
            "status": refund.status,
            "network": "sepolia"
        }

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error)
        )

    except RuntimeError as error:
        raise HTTPException(
            status_code=500,
            detail=str(error)
        )
