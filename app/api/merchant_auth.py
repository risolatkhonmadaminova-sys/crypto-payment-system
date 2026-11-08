from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db

from app.schemas.wallet import (
    MerchantWalletChallengeRequest,
    MerchantWalletVerificationRequest
)

from app.services.merchant_auth_service import (
    create_merchant_challenge,
    verify_merchant_signature
)


router = APIRouter(
    prefix="/api/merchant/auth",
    tags=["Merchant Authentication"]
)


@router.post("/challenge")
def merchant_challenge_endpoint(
    data: MerchantWalletChallengeRequest,
    db: Session = Depends(get_db)
):
    try:
        return create_merchant_challenge(
            db=db,
            wallet_address=data.wallet_address
        )

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error)
        )


@router.post("/verify")
def merchant_verify_endpoint(
    data: MerchantWalletVerificationRequest,
    db: Session = Depends(get_db)
):
    try:
        return verify_merchant_signature(
            db=db,
            nonce=data.nonce,
            signature=data.signature
        )

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error)
        )