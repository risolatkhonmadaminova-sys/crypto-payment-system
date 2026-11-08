
from decimal import Decimal

from web3 import Web3
from web3.exceptions import TimeExhausted

from app.config import MERCHANT_WALLET_ADDRESS
from app.blockchain.web3_client import web3


def get_wallet_balance(wallet_address: str):

    # 1. Validate Ethereum wallet address
    if not Web3.is_address(wallet_address):
        raise ValueError("Invalid Ethereum wallet address")

    # 2. Convert address to checksum format
    checksum_address = Web3.to_checksum_address(wallet_address)

    # 3. Get balance in Wei
    balance_wei = web3.eth.get_balance(checksum_address)

    # 4. Convert Wei to ETH
    balance_eth = Web3.from_wei(balance_wei, "ether")

    return {
        "wallet_address": checksum_address,
        "balance_wei": balance_wei,
        "balance_eth": Decimal(str(balance_eth)),
        "network": "Sepolia"
    }


def prepare_payment_transaction(
    sender_address: str,
    amount_eth: Decimal
):
    # 1. Validate sender address
    if not Web3.is_address(sender_address):
        raise ValueError("Invalid sender wallet address")

    # 2. Validate payment amount
    amount_eth = Decimal(str(amount_eth))

    if amount_eth <= 0:
        raise ValueError("Payment amount must be positive")

    # 3. Normalize wallet addresses
    sender = Web3.to_checksum_address(sender_address)
    recipient = Web3.to_checksum_address(MERCHANT_WALLET_ADDRESS)

    # 4. Check Sepolia network
    if web3.eth.chain_id != 11155111:
        raise RuntimeError("Wrong blockchain network")

    # 5. Convert ETH to Wei
    value_wei = Web3.to_wei(amount_eth, "ether")

    # 6. Get sender balance
    sender_balance = web3.eth.get_balance(sender)

    # 7. Estimate transaction gas
    transaction = {
        "from": sender,
        "to": recipient,
        "value": value_wei
    }

    estimated_gas = web3.eth.estimate_gas(transaction)
    gas_price = web3.eth.gas_price

    estimated_gas_fee = estimated_gas * gas_price

    # 8. Check whether sender has enough ETH
    required_balance = value_wei + estimated_gas_fee

    if sender_balance < required_balance:
        raise ValueError(
            "Insufficient ETH balance including estimated gas fee"
        )

    # 9. Return unsigned transaction information
    return {
        "from": sender,
        "to": recipient,
        "value_wei": value_wei,
        "chain_id": 11155111,
        "estimated_gas": estimated_gas,
        "estimated_gas_fee_wei": estimated_gas_fee
    }


def prepare_refund_transaction(
    recipient_address: str,
    amount_eth: Decimal
):
    # 1. Validate recipient address
    if not Web3.is_address(recipient_address):
        raise ValueError("Invalid recipient wallet address")

    # 2. Validate refund amount
    amount_eth = Decimal(str(amount_eth))

    if amount_eth <= 0:
        raise ValueError("Refund amount must be positive")

    # 3. Set merchant as sender
    sender = Web3.to_checksum_address(MERCHANT_WALLET_ADDRESS)

    # 4. Normalize customer address
    recipient = Web3.to_checksum_address(recipient_address)

    # 5. Check Sepolia network
    if web3.eth.chain_id != 11155111:
        raise RuntimeError("Wrong blockchain network")

    # 6. Convert ETH to Wei
    value_wei = Web3.to_wei(amount_eth, "ether")

    # 7. Get merchant balance
    sender_balance = web3.eth.get_balance(sender)

    # 8. Prepare transaction for gas estimation
    transaction = {
        "from": sender,
        "to": recipient,
        "value": value_wei
    }

    # 9. Estimate gas and transaction fee
    estimated_gas = web3.eth.estimate_gas(transaction)
    gas_price = web3.eth.gas_price

    estimated_gas_fee = estimated_gas * gas_price

    # 10. Check sufficient merchant balance
    required_balance = value_wei + estimated_gas_fee

    if sender_balance < required_balance:
        raise ValueError(
            "Merchant wallet has insufficient ETH "
            "including estimated gas fee"
        )

    # 11. Return unsigned transaction information
    return {
        "from": sender,
        "to": recipient,
        "value_wei": value_wei,
        "chain_id": 11155111,
        "estimated_gas": estimated_gas,
        "estimated_gas_fee_wei": estimated_gas_fee
    }


def verify_blockchain_transaction(
    transaction_hash: str,
    expected_sender: str,
    expected_recipient: str,
    expected_amount: Decimal
):
    # 1. Validate transaction hash format
    if (
        not isinstance(transaction_hash, str)
        or not transaction_hash.startswith("0x")
        or len(transaction_hash) != 66
        or not all(
            c in "0123456789abcdefABCDEF"
            for c in transaction_hash[2:]
        )
    ):
        raise ValueError("Invalid transaction hash")

    # 2. Check Sepolia network
    if web3.eth.chain_id != 11155111:
        raise RuntimeError("Wrong blockchain network")

    # 3. Get transaction from blockchain
    try:
        transaction = web3.eth.get_transaction(transaction_hash)
    except Exception as error:
        raise ValueError(
            "Transaction not found on Sepolia"
        ) from error

    # 4. Wait for transaction receipt
    try:
        receipt = web3.eth.wait_for_transaction_receipt(
            transaction_hash,
            timeout=180,
            poll_latency=2
        )

    except TimeExhausted as error:
        raise ValueError(
            "Transaction was submitted but not confirmed "
            "within 180 seconds. Please retry using the same "
            "transaction hash. Do not send another payment."
        ) from error

    except Exception as error:
        raise ValueError(
            "Could not retrieve transaction receipt from Sepolia RPC"
        ) from error

    # 5. Validate transaction status
    if receipt["status"] != 1:
        raise ValueError("Blockchain transaction failed")

    # 6. Validate expected wallet addresses
    if not Web3.is_address(expected_sender):
        raise ValueError("Invalid expected sender address")

    if not Web3.is_address(expected_recipient):
        raise ValueError("Invalid expected recipient address")

    # 7. Normalize wallet addresses
    sender = Web3.to_checksum_address(expected_sender)
    recipient = Web3.to_checksum_address(expected_recipient)

    # 8. Check sender address
    if transaction["from"] != sender:
        raise ValueError(
            "Transaction sender does not match customer wallet"
        )

    # 9. Check recipient address
    if transaction["to"] != recipient:
        raise ValueError(
            "Transaction recipient does not match merchant wallet"
        )

    # 10. Convert expected ETH amount to Wei
    expected_value = Web3.to_wei(
        Decimal(str(expected_amount)),
        "ether"
    )

    # 11. Check transaction amount
    if transaction["value"] != expected_value:
        raise ValueError(
            "Transaction amount does not match payment amount"
        )

    # 12. Return verified transaction information
    return {
        "transaction_hash": transaction_hash,
        "from_address": sender,
        "to_address": recipient,
        "amount_wei": transaction["value"],
        "block_number": receipt["blockNumber"],
        "status": "confirmed",
        "network": "sepolia"
    }


def verify_refund_transaction(
    transaction_hash: str,
    expected_sender: str,
    expected_recipient: str,
    expected_amount: Decimal
):
    # 1. Validate transaction hash
    if (
        not isinstance(transaction_hash, str)
        or not transaction_hash.startswith("0x")
        or len(transaction_hash) != 66
        or not all(
            c in "0123456789abcdefABCDEF"
            for c in transaction_hash[2:]
        )
    ):
        raise ValueError("Invalid transaction hash")

    # 2. Check Sepolia network
    if web3.eth.chain_id != 11155111:
        raise RuntimeError("Wrong blockchain network")

    # 3. Get transaction from blockchain
    try:
        transaction = web3.eth.get_transaction(transaction_hash)
    except Exception as error:
        raise ValueError(
            "Refund transaction not found on Sepolia"
        ) from error

    # 4. Wait for refund transaction receipt
    try:
        receipt = web3.eth.wait_for_transaction_receipt(
            transaction_hash,
            timeout=180,
            poll_latency=2
        )

    except TimeExhausted as error:
        raise ValueError(
            "Refund transaction was submitted but not confirmed "
            "within 180 seconds. Please retry using the same "
            "transaction hash. Do not send another refund."
        ) from error

    except Exception as error:
        raise ValueError(
            "Could not retrieve refund receipt from Sepolia RPC"
        ) from error

    # 5. Check transaction success
    if receipt["status"] != 1:
        raise ValueError("Refund transaction failed")

    # 6. Validate expected wallet addresses
    if not Web3.is_address(expected_sender):
        raise ValueError("Invalid expected refund sender address")

    if not Web3.is_address(expected_recipient):
        raise ValueError("Invalid expected refund recipient address")

    # 7. Normalize addresses
    expected_sender = Web3.to_checksum_address(expected_sender)
    expected_recipient = Web3.to_checksum_address(expected_recipient)

    actual_sender = Web3.to_checksum_address(transaction["from"])

    if transaction["to"] is None:
        raise ValueError("Invalid refund recipient in transaction")

    actual_recipient = Web3.to_checksum_address(transaction["to"])

    # 8. Verify sender
    if actual_sender != expected_sender:
        raise ValueError("Incorrect refund sender")

    # 9. Verify recipient
    if actual_recipient != expected_recipient:
        raise ValueError("Incorrect refund recipient")

    # 10. Verify amount
    expected_value = Web3.to_wei(
        Decimal(str(expected_amount)),
        "ether"
    )

    if transaction["value"] != expected_value:
        raise ValueError("Incorrect refund amount")

    # 11. Return verification result
    return {
        "transaction_hash": transaction_hash,
        "from_address": actual_sender,
        "to_address": actual_recipient,
        "amount": str(expected_amount),
        "block_number": receipt["blockNumber"],
        "status": "confirmed",
        "network": "sepolia"
    }
