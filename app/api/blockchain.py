from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import Payment
from app.blockchain.blockchain_service import (
    prepare_payment_transaction
)
from app.schemas.blockchain import PreparedTransactionResponse
from fastapi import APIRouter, HTTPException, status
from app.schemas.blockchain import WalletBalanceResponse
from app.blockchain.blockchain_service import get_wallet_balance
from app.schemas.blockchain import (
    TransactionHashCreate,
    TransactionHashResponse
)
from app.services.payment_service import (
    save_transaction_hash,
    PaymentNotFoundError
)
from app.security.jwt import verify_access_token


router = APIRouter(
    prefix="/api/blockchain",
    tags=["Blockchain"]
)


@router.get(
    "/balance/{wallet_address}",
    response_model=WalletBalanceResponse
)
def get_wallet_balance_endpoint(wallet_address: str):

    try:
        return get_wallet_balance(wallet_address)

    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error)
        )

    except Exception:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Blockchain service is temporarily unavailable"
        )
@router.post(
    "/prepare-payment/{payment_id}",
    response_model=PreparedTransactionResponse
)
def prepare_payment_endpoint(
    payment_id: str,
    db: Session = Depends(get_db),
    token_data: dict = Depends(verify_access_token)
):
    try:
        customer_id = int(token_data["sub"])
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=401,
            detail="Invalid authentication token"
        )

    payment = db.scalar(
        select(Payment).where(Payment.payment_id == payment_id)
    )

    if payment is None:
        raise HTTPException(
            status_code=404,
            detail="Payment not found"
        )

    if payment.customer_id != customer_id:
        raise HTTPException(
            status_code=403,
            detail="You do not have permission to access this payment"
        )

    token_wallet = token_data["wallet_address"]

    if (
        not payment.wallet_address
        or payment.wallet_address.lower() != token_wallet.lower()
    ):
        raise HTTPException(
            status_code=403,
            detail="Verified wallet does not match payment wallet"
        )

    if payment.status != "awaiting_customer_approval":
        raise HTTPException(
            status_code=400,
            detail="Payment is not awaiting customer approval"
        )

    try:
        transaction = prepare_payment_transaction(
            sender_address=payment.wallet_address,
            amount_eth=payment.amount
        )

        return {
            "from_address": transaction["from"],
            "to_address": transaction["to"],
            "value_wei": transaction["value_wei"],
            "chain_id": transaction["chain_id"],
            "estimated_gas": transaction["estimated_gas"],
            "estimated_gas_fee_wei": transaction["estimated_gas_fee_wei"]
        }

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error)
        )

    except Exception:
        raise HTTPException(
            status_code=503,
            detail="Could not prepare blockchain transaction"
        )
    
@router.post(
    "/save-transaction",
    response_model=TransactionHashResponse
)
def save_transaction_endpoint(
    data: TransactionHashCreate,
    db: Session = Depends(get_db),
    token_data: dict = Depends(verify_access_token)
):
    try:
        customer_id = int(token_data["sub"])
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=401,
            detail="Invalid authentication token"
        )

    payment = db.scalar(
        select(Payment).where(
            Payment.payment_id == data.payment_id
        )
    )

    if payment is None:
        raise HTTPException(
            status_code=404,
            detail="Payment not found"
        )

    if payment.customer_id != customer_id:
        raise HTTPException(
            status_code=403,
            detail="You do not have permission to access this payment"
        )

    token_wallet = token_data["wallet_address"]

    if (
        not payment.wallet_address
        or payment.wallet_address.lower() != token_wallet.lower()
    ):
        raise HTTPException(
            status_code=403,
            detail="Verified wallet does not match payment wallet"
        )

    try:
        transaction = save_transaction_hash(
            db=db,
            payment_id=data.payment_id,
            transaction_hash=data.transaction_hash
        )

        return {
            "payment_id": transaction.payment_id,
            "transaction_hash": transaction.transaction_hash,
            "status": transaction.status,
            "network": transaction.network
        }

    except PaymentNotFoundError:
        raise HTTPException(
            status_code=404,
            detail="Payment not found"
        )

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error)
        )
