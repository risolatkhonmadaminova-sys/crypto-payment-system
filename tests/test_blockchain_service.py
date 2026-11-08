from decimal import Decimal
from unittest.mock import MagicMock

import pytest
from web3 import Web3

from app.blockchain import blockchain_service


# Test addresses
CUSTOMER_WALLET = "0x" + "1" * 40
MERCHANT_WALLET = "0x" + "2" * 40
OTHER_WALLET = "0x" + "3" * 40

TRANSACTION_HASH = "0x" + "a" * 64

AMOUNT = Decimal("0.001")
VALUE_WEI = Web3.to_wei(AMOUNT, "ether")


@pytest.fixture
def mock_web3(monkeypatch):
    """
    Replace the real Web3 connection with a mock.
    No real blockchain requests will be made.
    """

    fake_web3 = MagicMock()

    fake_web3.eth.chain_id = 11155111
    fake_web3.eth.gas_price = 1_000_000_000
    fake_web3.eth.get_balance.return_value = 10**18
    fake_web3.eth.estimate_gas.return_value = 21000

    monkeypatch.setattr(
        blockchain_service,
        "web3",
        fake_web3
    )

    monkeypatch.setattr(
        blockchain_service,
        "MERCHANT_WALLET_ADDRESS",
        MERCHANT_WALLET
    )

    return fake_web3


# 1. Wallet balance

def test_get_wallet_balance_success(mock_web3):
    mock_web3.eth.get_balance.return_value = 10**18

    result = blockchain_service.get_wallet_balance(
        CUSTOMER_WALLET
    )

    assert result["balance_wei"] == 10**18
    assert result["balance_eth"] == Decimal("1")
    assert result["network"] == "Sepolia"

    mock_web3.eth.get_balance.assert_called_once()


# 2. Invalid wallet address

def test_get_wallet_balance_invalid_address(mock_web3):
    with pytest.raises(
        ValueError,
        match="Invalid Ethereum wallet address"
    ):
        blockchain_service.get_wallet_balance("invalid")


# 3. Prepare payment transaction

def test_prepare_payment_transaction_success(mock_web3):
    result = blockchain_service.prepare_payment_transaction(
        sender_address=CUSTOMER_WALLET,
        amount_eth=AMOUNT
    )

    assert result["from"] == Web3.to_checksum_address(
        CUSTOMER_WALLET
    )

    assert result["to"] == Web3.to_checksum_address(
        MERCHANT_WALLET
    )

    assert result["value_wei"] == VALUE_WEI
    assert result["chain_id"] == 11155111
    assert result["estimated_gas"] == 21000


# 4. Insufficient customer balance

def test_prepare_payment_insufficient_balance(mock_web3):
    mock_web3.eth.get_balance.return_value = 1

    with pytest.raises(
        ValueError,
        match="Insufficient ETH balance"
    ):
        blockchain_service.prepare_payment_transaction(
            sender_address=CUSTOMER_WALLET,
            amount_eth=AMOUNT
        )


# 5. Prepare refund transaction

def test_prepare_refund_transaction_success(mock_web3):
    result = blockchain_service.prepare_refund_transaction(
        recipient_address=CUSTOMER_WALLET,
        amount_eth=AMOUNT
    )

    assert result["from"] == Web3.to_checksum_address(
        MERCHANT_WALLET
    )

    assert result["to"] == Web3.to_checksum_address(
        CUSTOMER_WALLET
    )

    assert result["value_wei"] == VALUE_WEI
    assert result["chain_id"] == 11155111


# 6. Verify successful payment transaction

def test_verify_blockchain_transaction_success(mock_web3):
    mock_web3.eth.get_transaction.return_value = {
        "from": Web3.to_checksum_address(CUSTOMER_WALLET),
        "to": Web3.to_checksum_address(MERCHANT_WALLET),
        "value": VALUE_WEI
    }

    mock_web3.eth.wait_for_transaction_receipt.return_value = {
        "status": 1,
        "blockNumber": 12345
    }

    result = blockchain_service.verify_blockchain_transaction(
        transaction_hash=TRANSACTION_HASH,
        expected_sender=CUSTOMER_WALLET,
        expected_recipient=MERCHANT_WALLET,
        expected_amount=AMOUNT
    )

    assert result["transaction_hash"] == TRANSACTION_HASH
    assert result["status"] == "confirmed"
    assert result["block_number"] == 12345
    assert result["network"] == "sepolia"


# 7. Reject payment from incorrect sender

def test_verify_blockchain_transaction_wrong_sender(mock_web3):
    mock_web3.eth.get_transaction.return_value = {
        "from": Web3.to_checksum_address(OTHER_WALLET),
        "to": Web3.to_checksum_address(MERCHANT_WALLET),
        "value": VALUE_WEI
    }

    mock_web3.eth.wait_for_transaction_receipt.return_value = {
        "status": 1,
        "blockNumber": 12345
    }

    with pytest.raises(
        ValueError,
        match="Transaction sender does not match"
    ):
        blockchain_service.verify_blockchain_transaction(
            transaction_hash=TRANSACTION_HASH,
            expected_sender=CUSTOMER_WALLET,
            expected_recipient=MERCHANT_WALLET,
            expected_amount=AMOUNT
        )


# 8. Verify successful refund transaction

def test_verify_refund_transaction_success(mock_web3):
    mock_web3.eth.get_transaction.return_value = {
        "from": Web3.to_checksum_address(MERCHANT_WALLET),
        "to": Web3.to_checksum_address(CUSTOMER_WALLET),
        "value": VALUE_WEI
    }

    mock_web3.eth.wait_for_transaction_receipt.return_value = {
        "status": 1,
        "blockNumber": 12346
    }

    result = blockchain_service.verify_refund_transaction(
        transaction_hash=TRANSACTION_HASH,
        expected_sender=MERCHANT_WALLET,
        expected_recipient=CUSTOMER_WALLET,
        expected_amount=AMOUNT
    )

    assert result["transaction_hash"] == TRANSACTION_HASH
    assert result["status"] == "confirmed"
    assert result["network"] == "sepolia"


# 9. Reject failed refund transaction

def test_verify_refund_transaction_failed(mock_web3):
    mock_web3.eth.get_transaction.return_value = {
        "from": Web3.to_checksum_address(MERCHANT_WALLET),
        "to": Web3.to_checksum_address(CUSTOMER_WALLET),
        "value": VALUE_WEI
    }

    mock_web3.eth.wait_for_transaction_receipt.return_value = {
        "status": 0,
        "blockNumber": 12347
    }

    with pytest.raises(
        ValueError,
        match="Refund transaction failed"
    ):
        blockchain_service.verify_refund_transaction(
            transaction_hash=TRANSACTION_HASH,
            expected_sender=MERCHANT_WALLET,
            expected_recipient=CUSTOMER_WALLET,
            expected_amount=AMOUNT
        )