from app.blockchain.blockchain_service import get_wallet_balance


# Example Ethereum wallet address
wallet_address = "0x742d35Cc6634C0532925a3b844Bc454e4438f44e"


try:
    result = get_wallet_balance(wallet_address)

    print("Wallet balance retrieved successfully!")

    print("Wallet address:", result["wallet_address"])
    print("Network:", result["network"])
    print("Balance in ETH:", result["balance_eth"])
    print("Balance in Wei:", result["balance_wei"])

except Exception as error:
    print("Error:", error)