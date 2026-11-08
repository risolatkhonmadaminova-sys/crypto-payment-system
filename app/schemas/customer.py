from pydantic import BaseModel, EmailStr, Field


class CustomerCreate(BaseModel):
    full_name: str = Field(min_length=2, max_length=100)
    email: EmailStr
    wallet_address: str = Field(
        pattern=r"^0x[a-fA-F0-9]{40}$"
    )


class CustomerResponse(BaseModel):
    id: int
    full_name: str
    email: EmailStr
    wallet_address: str

    model_config = {"from_attributes": True}