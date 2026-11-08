
import os

from dotenv import load_dotenv
from web3 import Web3

load_dotenv()

MERCHANT_WALLET_ADDRESS = os.getenv(
    "MERCHANT_WALLET_ADDRESS"
)

if not MERCHANT_WALLET_ADDRESS:
    raise RuntimeError(
        "MERCHANT_WALLET_ADDRESS is not configured"
    )

if not Web3.is_address(MERCHANT_WALLET_ADDRESS):
    raise RuntimeError(
        "Invalid merchant wallet address"
    )

MERCHANT_WALLET_ADDRESS = Web3.to_checksum_address(
    MERCHANT_WALLET_ADDRESS
)
