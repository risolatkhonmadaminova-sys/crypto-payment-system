from decimal import Decimal
from pydantic import BaseModel


class WalletBalanceResponse(BaseModel):
    wallet_address: str
    balance_wei: int
    balance_eth: Decimal
    network: str

class PreparedTransactionResponse(BaseModel):
    from_address: str
    to_address: str
    value_wei: int
    chain_id: int
    estimated_gas: int
    estimated_gas_fee_wei: int

from pydantic import Field

class TransactionHashCreate(BaseModel):
    payment_id: str
    transaction_hash: str = Field(
        pattern=r"^0x[a-fA-F0-9]{64}$"
    )


class TransactionHashResponse(BaseModel):
    payment_id: str
    transaction_hash: str
    status: str
    network: str