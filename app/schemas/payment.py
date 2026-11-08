from decimal import Decimal
from pydantic import BaseModel, Field
from typing import Literal
from enum import Enum


class PaymentCreate(BaseModel):
    customer_id: int
    order_id: str
    amount: Decimal = Field(gt=0)
    currency: Literal["ETH"]


class PaymentResponse(BaseModel):
    payment_id: str
    customer_id: int
    order_id: str
    amount: Decimal
    currency: str
    status: str
    message: str


class PaymentDetails(BaseModel):
    payment_id: str
    customer_id: int
    order_id: str
    amount: Decimal
    currency: str
    wallet_address: str
    status: str

    model_config = {"from_attributes": True}


class PaymentStatus(str, Enum):
    AWAITING_CUSTOMER_APPROVAL = "awaiting_customer_approval"
    PENDING_CONFIRMATION = "pending_confirmation"
    CONFIRMED = "confirmed"
    FAILED = "failed"


class PaymentStatusUpdate(BaseModel):
    status: PaymentStatus
