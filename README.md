# Crypto Payment System

A cryptocurrency payment backend built with **FastAPI, PostgreSQL, SQLAlchemy, and Web3.py**. The system integrates Ethereum Sepolia testnet and MetaMask to support cryptocurrency payments and refunds.

## 1. Project Overview

Crypto Payment System is a backend application that allows merchants to accept Ethereum payments from customers.

The application supports:

- Customer management.
- Ethereum wallet connection and ownership verification.
- Payment creation and tracking.
- Blockchain transaction preparation and verification.
- Refund creation and processing.
- API Key authentication.
- Rate limiting.
- Idempotent payment creation.
- Error handling and application logging.
- Automated testing.

**Network:** Ethereum Sepolia Testnet  
**Currency:** ETH

This project is intended for educational and testing purposes. It is not a production-ready payment processor.

## 2. Technologies

| Technology | Purpose |
|---|---|
| Python 3.11 | Backend programming |
| FastAPI | REST API |
| PostgreSQL 16 | Database |
| SQLAlchemy | ORM and database operations |
| Web3.py | Ethereum blockchain integration |
| MetaMask | Non-custodial wallet interaction |
| Pydantic | Data validation |
| SlowAPI | Rate limiting |
| Pytest | Automated testing |
| Docker | PostgreSQL environment |

## 3. System Architecture

The application follows a layered architecture:

- **API Layer:** Handles HTTP requests and responses.
- **Service Layer:** Contains payment, customer, wallet, and refund business logic.
- **Database Layer:** Manages PostgreSQL data using SQLAlchemy.
- **Blockchain Layer:** Communicates with Ethereum Sepolia through Web3.py.
- **Security Layer:** Provides API Key authentication and request rate limiting.

### Payment Flow

1. Customer connects MetaMask.
2. Backend generates a wallet verification challenge.
3. Customer signs the challenge using MetaMask.
4. Backend verifies wallet ownership.
5. Customer requests payment creation.
6. Backend prepares an unsigned blockchain transaction.
7. Customer approves and signs the transaction in MetaMask.
8. Backend verifies the transaction on Sepolia.
9. Payment status is updated after successful verification.

### Refund Flow

1. Merchant requests a refund for a confirmed payment.
2. Backend creates a refund record.
3. Backend prepares an unsigned refund transaction.
4. Merchant approves and signs the transaction.
5. Backend verifies the transaction on Sepolia.
6. Refund is marked as confirmed.

## 4. Project Structure

```text
crypto-payment-system/
│
├── app/
│   ├── api/
│   ├── blockchain/
│   ├── core/
│   ├── db/
│   ├── schemas/
│   ├── security/
│   ├── services/
│   ├── config.py
│   └── main.py
│
├── frontend/
│
├── tests/
│
├── logs/
├── .env
├── .gitignore
├── docker-compose.yml
├── create_tables.py
├── requirements.txt
└── README.md
```

## 5. Installation and Setup

### Requirements

- Python 3.11
- Docker Desktop
- MetaMask browser extension
- Ethereum Sepolia RPC provider

### Step 1. Clone the repository

```bash
git clone YOUR_GITHUB_REPOSITORY_URL
cd crypto-payment-system
```

### Step 2. Create a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### Step 3. Install dependencies

```bash
pip install -r requirements.txt
```

### Step 4. Configure environment variables

Create a `.env` file in the project root:

```env
SEPOLIA_RPC_URL=YOUR_SEPOLIA_RPC_URL
MERCHANT_WALLET_ADDRESS=YOUR_MERCHANT_WALLET_ADDRESS
DATABASE_URL=YOUR_DATABASE_URL
API_KEY=YOUR_SECRET_API_KEY
```

Never publish `.env` or share private keys, seed phrases, API keys, or RPC credentials.

### Step 5. Start PostgreSQL

```bash
docker compose up -d
```

### Step 6. Create database tables

```bash
python create_tables.py
```

### Step 7. Start the backend

```bash
uvicorn app.main:app --reload
```

The backend runs at:

```text
http://127.0.0.1:8000
```

## 6. API Documentation

FastAPI automatically generates interactive API documentation.

Swagger UI:

```text
http://127.0.0.1:8000/docs
```

Main API endpoint groups:

| Endpoint | Method | Purpose |
|---|---|---|
| `/api/customers/` | Customer operations | Customer management |
| `/api/payments/` | POST | Create payment |
| `/api/payments/` | GET | Retrieve payments |
| `/api/payments/{payment_id}` | GET | Retrieve payment details |
| `/api/payments/{payment_id}/status` | PATCH | Update payment status |
| `/api/wallet/challenge` | POST | Generate wallet challenge |
| `/api/wallet/verify` | POST | Verify wallet signature |
| `/api/blockchain/balance/{wallet_address}` | GET | Retrieve wallet balance |
| `/api/refunds/` | POST | Create refund |
| `/api/refunds/{payment_id}/prepare` | POST | Prepare refund transaction |
| `/api/refunds/save-transaction` | POST | Save and verify refund transaction |

Protected endpoints require an API Key in the `X-API-Key` request header.

## 7. Automated Testing

The project uses Pytest for automated testing.

Run all tests:

```bash
python -m pytest tests/ -v
```

Current test result:

**47 passed, 1 warning**

Test coverage includes:

- Payment service logic.
- Payment API endpoints.
- Wallet API endpoints.
- Refund API endpoints.
- Blockchain service operations.

Blockchain tests use mocked Web3 responses and do not send real transactions.

## 8. Security Features

The project implements:

- API Key authentication for protected API endpoints.
- Wallet ownership verification using cryptographic signatures.
- One-time wallet verification challenges.
- Challenge expiration.
- Rate limiting.
- Payment idempotency.
- Environment variables for sensitive configuration.
- Input validation.
- Centralized error handling and logging.
- Blockchain transaction verification.

### Important Security Considerations

- Private keys and seed phrases are not stored by the backend.
- MetaMask signs customer payment transactions.
- Refund transactions require merchant approval.
- Payment confirmation must depend on blockchain verification, not an arbitrary client request.
- API Key authentication alone is not sufficient for production customer authentication.
- Production deployment requires HTTPS, proper user authentication, authorization, and restricted administrative operations.

## 9. Blockchain Network

The project currently uses **Ethereum Sepolia Testnet**.

Sepolia is a test network intended for development and testing. Test ETH has no real monetary value.

Blockchain transaction verification checks:

- Transaction hash.
- Sender address.
- Recipient address.
- Transaction amount.
- Transaction receipt status.
- Network chain ID.

## 10. Project Purpose

The main purpose of this project is to demonstrate the integration of a REST API backend with a relational database, a non-custodial cryptocurrency wallet, and the Ethereum blockchain.

The system demonstrates payment processing, wallet verification, refund handling, API security, and automated software testing.