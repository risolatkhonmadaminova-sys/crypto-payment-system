from app.blockchain.web3_client import check_connection


result = check_connection()

print("Blockchain connection successful!")
print(result)