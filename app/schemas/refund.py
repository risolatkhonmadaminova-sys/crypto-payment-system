from decimal import Decimal

from pydantic import BaseModel, Field


class RefundCreate(BaseModel):
    payment_id: str = Field(
        min_length=36,
        max_length=36
    )


class RefundResponse(BaseModel):
    payment_id: str

    amount: Decimal

    from_address: str

    to_address: str

    transaction_hash: str | None

    status: str

    network: str

class RefundTransactionHashCreate(BaseModel):
    payment_id: str = Field(
        min_length=36,
        max_length=36
    )

    transaction_hash: str = Field(
        pattern=r"^0x[a-fA-F0-9]{64}$"
    )