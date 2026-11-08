
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    status,
    Header
)

from sqlalchemy.orm import Session

from app.schemas.payment import (
    PaymentCreate,
    PaymentResponse,
    PaymentDetails,
    PaymentStatusUpdate
)

from app.db.database import get_db

from app.services.payment_service import (
    create_payment,
    get_payments,
    get_payment,
    update_payment_status,
    PaymentNotFoundError,
    InvalidPaymentStatusTransitionError,
    CustomerNotFoundError,
    CustomerWalletNotLinkedError,
    IdempotencyKeyConflictError
)

from app.security.api_key import verify_api_key


router = APIRouter(
    prefix="/api/payments",
    tags=["Payments"]
)


# Create a payment
@router.post(
    "",
    response_model=PaymentResponse,
    status_code=status.HTTP_201_CREATED
)
def create_payment_endpoint(
    payment: PaymentCreate,
    idempotency_key: str = Header(
        ...,
        alias="Idempotency-Key",
        min_length=1,
        max_length=255
    ),
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    try:
        new_payment = create_payment(
            db,
            payment,
            idempotency_key
        )

    except CustomerNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error)
        )

    except CustomerWalletNotLinkedError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(error)
        )

    except IdempotencyKeyConflictError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(error)
        )

    return PaymentResponse(
        payment_id=new_payment.payment_id,
        customer_id=new_payment.customer_id,
        order_id=new_payment.order_id,
        amount=new_payment.amount,
        currency=new_payment.currency,
        status=new_payment.status,
        message="Payment request created successfully"
    )


# Get all payments
@router.get(
    "",
    response_model=list[PaymentDetails]
)
def get_payments_endpoint(
    skip: int = 0,
    limit: int = Query(default=10, ge=1, le=100),
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    return get_payments(db, skip, limit)


# Get one payment
@router.get(
    "/{payment_id}",
    response_model=PaymentDetails
)
def get_payment_endpoint(
    payment_id: str,
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    try:
        return get_payment(db, payment_id)

    except PaymentNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error)
        )


# Update payment status
@router.patch(
    "/{payment_id}/status",
    response_model=PaymentDetails
)
def update_payment_status_endpoint(
    payment_id: str,
    status_update: PaymentStatusUpdate,
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    try:
        return update_payment_status(
            db,
            payment_id,
            status_update.status
        )

    except PaymentNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error)
        )

    except InvalidPaymentStatusTransitionError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error)
        )
