import secrets
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from web3 import Web3
from eth_account import Account
from eth_account.messages import encode_defunct

from app.config import MERCHANT_WALLET_ADDRESS
from app.db.models import WalletChallenge
from app.security.jwt import create_merchant_access_token


def create_merchant_challenge(
    db: Session,
    wallet_address: str
):
    if not Web3.is_address(wallet_address):
        raise ValueError("Invalid Ethereum wallet address")

    checksum_address = Web3.to_checksum_address(wallet_address)

    if checksum_address != MERCHANT_WALLET_ADDRESS:
        raise ValueError("Wallet is not the configured merchant wallet")

    nonce = secrets.token_hex(16)

    message = (
        "Crypto Payment System Merchant Verification\n\n"
        f"Wallet: {checksum_address}\n"
        f"Nonce: {nonce}\n"
        "Purpose: Verify merchant wallet ownership.\n"
        "This signature does not authorize a transaction."
    )

    expires_at = datetime.now(timezone.utc) + timedelta(minutes=5)

    challenge = WalletChallenge(
        customer_id=None,
        wallet_address=checksum_address,
        nonce=nonce,
        message=message,
        expires_at=expires_at
    )

    db.add(challenge)
    db.commit()
    db.refresh(challenge)

    return {
        "nonce": challenge.nonce,
        "message": challenge.message,
        "expires_at": challenge.expires_at.isoformat()
    }


def verify_merchant_signature(
    db: Session,
    nonce: str,
    signature: str
):
    statement = (
        select(WalletChallenge)
        .where(WalletChallenge.nonce == nonce)
        .with_for_update()
    )

    challenge = db.scalar(statement)

    if challenge is None:
        raise ValueError("Merchant challenge not found")

    if challenge.customer_id is not None:
        raise ValueError("This is not a merchant challenge")

    if challenge.used_at is not None:
        raise ValueError("Merchant challenge has already been used")

    now = datetime.now(timezone.utc)

    expires_at = challenge.expires_at

    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)

    if now >= expires_at:
        raise ValueError("Merchant challenge has expired")

    if challenge.wallet_address != MERCHANT_WALLET_ADDRESS:
        raise ValueError("Invalid merchant wallet")

    try:
        encoded_message = encode_defunct(text=challenge.message)

        recovered_address = Account.recover_message(
            encoded_message,
            signature=signature
        )

        recovered_address = Web3.to_checksum_address(
            recovered_address
        )

    except Exception:
        raise ValueError("Invalid merchant signature")

    if recovered_address != MERCHANT_WALLET_ADDRESS:
        raise ValueError("Signature does not belong to merchant wallet")

    challenge.used_at = now

    db.commit()

    access_token = create_merchant_access_token(
        wallet_address=recovered_address
    )

    return {
        "verified": True,
        "wallet_address": recovered_address,
        "access_token": access_token,
        "token_type": "bearer",
        "message": "Merchant wallet verified successfully"
    }