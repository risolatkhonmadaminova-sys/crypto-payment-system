
from pydantic import BaseModel, Field


class WalletChallengeRequest(BaseModel):
    customer_id: int = Field(gt=0)
    wallet_address: str = Field(pattern=r"^0x[a-fA-F0-9]{40}$")


class WalletChallengeResponse(BaseModel):
    nonce: str
    message: str
    expires_at: str


class WalletVerificationRequest(BaseModel):
    customer_id: int = Field(gt=0)
    nonce: str
    signature: str = Field(
        pattern=r"^0x[a-fA-F0-9]+$"
    )


class WalletVerificationResponse(BaseModel):
    verified: bool
    wallet_address: str
    access_token: str
    token_type: str
    message: str
class MerchantWalletChallengeRequest(BaseModel):
    wallet_address: str = Field(
        pattern=r"^0x[a-fA-F0-9]{40}$"
    )


class MerchantWalletVerificationRequest(BaseModel):
    nonce: str
    signature: str = Field(
        pattern=r"^0x[a-fA-F0-9]+$"
    )