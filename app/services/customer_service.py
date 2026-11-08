from sqlalchemy.orm import Session

from app.db.models import Customer
from app.schemas.customer import CustomerCreate


class CustomerNotFoundError(Exception):
    pass


class CustomerAlreadyExistsError(Exception):
    pass


def create_customer(db: Session, customer_data: CustomerCreate):

    existing_customer = (
        db.query(Customer)
        .filter(Customer.email == customer_data.email)
        .first()
    )

    if existing_customer:
        raise CustomerAlreadyExistsError(
            "Customer with this email already exists"
        )

    new_customer = Customer(
        full_name=customer_data.full_name,
        email=customer_data.email,
        wallet_address=customer_data.wallet_address
    )

    try:
        db.add(new_customer)
        db.commit()
        db.refresh(new_customer)

    except Exception:
        db.rollback()
        raise

    return new_customer


def get_customers(db: Session):

    return (
        db.query(Customer)
        .order_by(Customer.id.desc())
        .all()
    )


def get_customer(db: Session, customer_id: int):

    customer = (
        db.query(Customer)
        .filter(Customer.id == customer_id)
        .first()
    )

    if customer is None:
        raise CustomerNotFoundError("Customer not found")

    return customer
