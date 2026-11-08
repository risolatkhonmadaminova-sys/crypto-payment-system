import os
from datetime import datetime, timedelta, timezone

import jwt
from dotenv import load_dotenv
from web3 import Web3

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.config import MERCHANT_WALLET_ADDRESS


load_dotenv()

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")

JWT_ACCESS_TOKEN_EXPIRE_MINUTES = int(
    os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "15")
)

if not JWT_SECRET_KEY:
    raise RuntimeError("JWT_SECRET_KEY is not configured")


bearer_scheme = HTTPBearer(auto_error=False)


# CUSTOMER JWT

def create_access_token(
    customer_id: int,
    wallet_address: str
) -> str:

    now = datetime.now(timezone.utc)

    payload = {
        "sub": str(customer_id),
        "role": "customer",
        "wallet_address": wallet_address,
        "iat": now,
        "exp": now + timedelta(
            minutes=JWT_ACCESS_TOKEN_EXPIRE_MINUTES
        )
    }

    return jwt.encode(
        payload,
        JWT_SECRET_KEY,
        algorithm=JWT_ALGORITHM
    )


# MERCHANT JWT

def create_merchant_access_token(
    wallet_address: str
) -> str:

    checksum_address = Web3.to_checksum_address(wallet_address)

    if checksum_address != MERCHANT_WALLET_ADDRESS:
        raise ValueError("Invalid merchant wallet address")

    now = datetime.now(timezone.utc)

    payload = {
        "sub": "merchant",
        "role": "merchant",
        "wallet_address": checksum_address,
        "iat": now,
        "exp": now + timedelta(
            minutes=JWT_ACCESS_TOKEN_EXPIRE_MINUTES
        )
    }

    return jwt.encode(
        payload,
        JWT_SECRET_KEY,
        algorithm=JWT_ALGORITHM
    )


# VERIFY CUSTOMER JWT

def verify_access_token(
    credentials: HTTPAuthorizationCredentials | None = Depends(
        bearer_scheme
    )
) -> dict:

    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication token",
            headers={"WWW-Authenticate": "Bearer"}
        )

    try:
        payload = jwt.decode(
            credentials.credentials,
            JWT_SECRET_KEY,
            algorithms=[JWT_ALGORITHM]
        )

        if (
            not payload.get("sub")
            or not payload.get("wallet_address")
            or payload.get("role") != "customer"
        ):
            raise jwt.InvalidTokenError("Invalid customer token")

        return payload

    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token has expired",
            headers={"WWW-Authenticate": "Bearer"}
        )

    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid customer token",
            headers={"WWW-Authenticate": "Bearer"}
        )


# VERIFY MERCHANT JWT

def verify_merchant_access_token(
    credentials: HTTPAuthorizationCredentials | None = Depends(
        bearer_scheme
    )
) -> dict:

    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing merchant authentication token",
            headers={"WWW-Authenticate": "Bearer"}
        )

    try:
        payload = jwt.decode(
            credentials.credentials,
            JWT_SECRET_KEY,
            algorithms=[JWT_ALGORITHM]
        )

        if (
            payload.get("role") != "merchant"
            or payload.get("sub") != "merchant"
            or payload.get("wallet_address")
            != MERCHANT_WALLET_ADDRESS
        ):
            raise jwt.InvalidTokenError("Invalid merchant token")

        return payload

    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token has expired",
            headers={"WWW-Authenticate": "Bearer"}
        )

    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid merchant token",
            headers={"WWW-Authenticate": "Bearer"}
        )