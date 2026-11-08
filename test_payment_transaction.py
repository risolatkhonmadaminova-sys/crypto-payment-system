from decimal import Decimal

from app.blockchain.blockchain_service import (
    prepare_payment_transaction
)

customer_wallet = "0x2333D3227da85455D6ccb4808C70E96ae18bD256"

try:
    result = prepare_payment_transaction(
        sender_address=customer_wallet,
        amount_eth=Decimal("0.001")
    )

    print("Transaction prepared successfully!")

    for key, value in result.items():
        print(f"{key}: {value}")

except Exception as error:
    print("Error:", error)