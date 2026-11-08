from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.database import get_db

from app.schemas.customer import (
    CustomerCreate,
    CustomerResponse
)

from app.services.customer_service import (
    create_customer,
    get_customers,
    get_customer,
    CustomerNotFoundError,
    CustomerAlreadyExistsError
)
from app.security.api_key import verify_api_key

router = APIRouter(
    prefix="/api/customers",
    tags=["Customers"]
)


# Create a customer
@router.post(
    "",
    response_model=CustomerResponse,
    status_code=status.HTTP_201_CREATED
)
def create_customer_endpoint(
    customer: CustomerCreate,
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):

    try:
        return create_customer(db, customer)

    except CustomerAlreadyExistsError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(error)
        )


# Get all customers
@router.get(
    "",
    response_model=list[CustomerResponse]
)
def get_customers_endpoint(
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):

    return get_customers(db)


# Get one customer
@router.get(
    "/{customer_id}",
    response_model=CustomerResponse
)
def get_customer_endpoint(
    customer_id: int,
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):

    try:
        return get_customer(db, customer_id)

    except CustomerNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error)
        )