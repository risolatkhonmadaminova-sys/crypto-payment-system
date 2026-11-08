
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session

from app.security.rate_limiter import limiter
from app.db.database import get_db

from app.schemas.wallet import (
    WalletChallengeRequest,
    WalletChallengeResponse,
    WalletVerificationRequest,
    WalletVerificationResponse
)

from app.services.wallet_service import (
    create_wallet_challenge,
    verify_wallet_signature,
    WalletChallengeNotFoundError,
    WalletChallengeExpiredError,
    WalletChallengeAlreadyUsedError,
    WalletSignatureInvalidError,
    CustomerNotFoundError,
    WalletAlreadyLinkedError
)


router = APIRouter(
    prefix="/api/wallet",
    tags=["Wallet Verification"]
)


@router.post(
    "/challenge",
    response_model=WalletChallengeResponse
)
@limiter.limit("5/minute")
def create_challenge(
    request: Request,
    request_data: WalletChallengeRequest,
    db: Session = Depends(get_db)
):
    try:
        return create_wallet_challenge(
            db,
            request_data.customer_id,
            request_data.wallet_address
        )

    except CustomerNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error)
        )

    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error)
        )


@router.post(
    "/verify",
    response_model=WalletVerificationResponse
)
@limiter.limit("5/minute")
def verify_wallet(
    request: Request,
    request_data: WalletVerificationRequest,
    db: Session = Depends(get_db)
):
    try:
        return verify_wallet_signature(
            db,
            request_data.customer_id,
            request_data.nonce,
            request_data.signature
        )

    except WalletChallengeNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error)
        )

    except WalletChallengeAlreadyUsedError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(error)
        )

    except WalletChallengeExpiredError as error:
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail=str(error)
        )

    except WalletSignatureInvalidError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error)
        )

    except CustomerNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error)
        )

    except WalletAlreadyLinkedError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(error)
        )
