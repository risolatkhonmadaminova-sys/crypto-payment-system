import os

from dotenv import load_dotenv
from web3 import Web3


# Load environment variables
load_dotenv()


# Get Sepolia RPC URL
SEPOLIA_RPC_URL = os.getenv("SEPOLIA_RPC_URL")


if not SEPOLIA_RPC_URL:
    raise RuntimeError("SEPOLIA_RPC_URL is not configured")


# Create Web3 connection
web3 = Web3(
    Web3.HTTPProvider(
        SEPOLIA_RPC_URL,
        request_kwargs={"timeout": 20}
    )
)


# Check connection to Sepolia
def check_connection():

    if not web3.is_connected():
        raise ConnectionError(
            "Could not connect to Ethereum Sepolia"
        )

    chain_id = web3.eth.chain_id

    if chain_id != 11155111:
        raise RuntimeError(
            f"Wrong network! Expected Sepolia, got chain ID {chain_id}"
        )

    return {
        "connected": True,
        "network": "Sepolia",
        "chain_id": chain_id,
        "latest_block": web3.eth.block_number
    }