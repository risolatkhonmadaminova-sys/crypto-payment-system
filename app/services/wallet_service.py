
import secrets
from datetime import datetime, timedelta, timezone

from sqlalchemy import select, func
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from web3 import Web3
from eth_account import Account
from eth_account.messages import encode_defunct

from app.db.models import WalletChallenge, Customer
from app.security.jwt import create_access_token


class WalletChallengeNotFoundError(Exception):
    pass


class WalletChallengeExpiredError(Exception):
    pass


class WalletChallengeAlreadyUsedError(Exception):
    pass


class WalletSignatureInvalidError(Exception):
    pass


class CustomerNotFoundError(Exception):
    pass


class WalletAlreadyLinkedError(Exception):
    pass


def create_wallet_challenge(
    db: Session,
    customer_id: int,
    wallet_address: str
):
    # Step 1: Check whether customer exists
    customer = db.get(Customer, customer_id)

    if customer is None:
        raise CustomerNotFoundError("Customer not found")

    # Step 2: Validate wallet address
    if not Web3.is_address(wallet_address):
        raise ValueError("Invalid Ethereum wallet address")

    checksum_address = Web3.to_checksum_address(wallet_address)

    # Step 3: Generate a secure nonce
    nonce = secrets.token_hex(16)

    message = (
        "Crypto Payment System wallet verification\n\n"
        f"Wallet: {checksum_address}\n"
        f"Nonce: {nonce}\n"
        "Purpose: Verify wallet ownership.\n"
        "This signature does not authorize a transaction."
    )

    # Step 4: Set challenge expiration
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=5)

    # Step 5: Create challenge linked to customer
    challenge = WalletChallenge(
        customer_id=customer_id,
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


def verify_wallet_signature(
    db: Session,
    customer_id: int,
    nonce: str,
    signature: str
):
    # Step 1: Find customer
    customer = db.get(Customer, customer_id)

    if customer is None:
        raise CustomerNotFoundError("Customer not found")

    # Step 2: Find and lock wallet challenge
    statement = (
        select(WalletChallenge)
        .where(WalletChallenge.nonce == nonce)
        .with_for_update()
    )

    challenge = db.scalar(statement)

    if challenge is None:
        raise WalletChallengeNotFoundError(
            "Wallet challenge not found"
        )

    # Step 3: Check challenge ownership
    if challenge.customer_id != customer_id:
        raise WalletSignatureInvalidError(
            "Wallet challenge does not belong to this customer"
        )

    # Step 4: Check whether challenge was already used
    if challenge.used_at is not None:
        raise WalletChallengeAlreadyUsedError(
            "This wallet challenge has already been used"
        )

    # Step 5: Check expiration
    if datetime.now(timezone.utc) >= challenge.expires_at:
        raise WalletChallengeExpiredError(
            "Wallet challenge has expired"
        )

    # Step 6: Verify signature
    try:
        encoded_message = encode_defunct(
            text=challenge.message
        )

        recovered_address = Account.recover_message(
            encoded_message,
            signature=signature
        )

        recovered_address = Web3.to_checksum_address(
            recovered_address
        )

    except Exception:
        raise WalletSignatureInvalidError(
            "Invalid wallet signature"
        )

    # Step 7: Compare wallet addresses
    if recovered_address != Web3.to_checksum_address(
        challenge.wallet_address
    ):
        raise WalletSignatureInvalidError(
            "Signature does not belong to the requested wallet"
        )

    # Step 8: Check whether another customer owns this wallet
    existing_customer = db.scalar(
        select(Customer).where(
            func.lower(Customer.wallet_address)
            == challenge.wallet_address.lower(),
            Customer.id != customer_id
        )
    )

    if existing_customer is not None:
        raise WalletAlreadyLinkedError(
            "This wallet is already linked to another customer"
        )

    # Step 9: Prevent automatic wallet replacement
    if customer.wallet_address is not None:
        if customer.wallet_address.lower() != challenge.wallet_address.lower():
            raise WalletAlreadyLinkedError(
                "Customer already has a different wallet linked"
            )

    # Step 10: Link verified wallet to customer
    customer.wallet_address = challenge.wallet_address

    # Step 11: Mark challenge as used
    challenge.used_at = datetime.now(timezone.utc)

    # Save both changes together
    try:
        db.commit()

    except IntegrityError:
        db.rollback()
        raise WalletAlreadyLinkedError(
            "This wallet is already linked to another customer"
        )

    # Step 12: Generate JWT after successful verification
    access_token = create_access_token(
        customer_id=customer.id,
        wallet_address=challenge.wallet_address
    )

    return {
        "verified": True,
        "wallet_address": challenge.wallet_address,
        "access_token": access_token,
        "token_type": "bearer",
        "message": "Wallet verified and linked to customer successfully"
    }
