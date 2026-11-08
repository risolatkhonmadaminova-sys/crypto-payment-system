
from sqlalchemy import Integer, String, Numeric, DateTime, func, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class Payment(Base):
    __tablename__ = "payments"

    # Primary key
    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True
    )

    # Unique payment identifier
    payment_id: Mapped[str] = mapped_column(
        String(36),
        unique=True,
        nullable=False,
        index=True
    )
    # Idempotency key prevents duplicate payment creation
    idempotency_key: Mapped[str | None] = mapped_column(
        String(255),
        unique=True,
        nullable=True
    )

    # Customer and order information

    customer_id: Mapped[int] = mapped_column(
    Integer,
    ForeignKey("customers.id"),
    nullable=False
)

    order_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    # Payment amount and currency
    amount: Mapped[float] = mapped_column(
        Numeric(18, 8),
        nullable=False
    )

    currency: Mapped[str] = mapped_column(
        String(10),
        nullable=False
    )

    # Customer's crypto wallet address
    wallet_address: Mapped[str] = mapped_column(
        String(42),
        nullable=False
    )

    # Payment status
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="awaiting_customer_approval"
    )

    # Payment creation time
    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    
class Customer(Base):
    __tablename__ = "customers"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True
    )

    full_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True
    )

    wallet_address: Mapped[str | None] = mapped_column(
    String(42),
    unique=True,
    nullable=True
    )

    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
class BlockchainTransaction(Base):
    __tablename__ = "blockchain_transactions"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True
    )

    payment_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("payments.payment_id"),
        nullable=False
    )

    transaction_hash: Mapped[str] = mapped_column(
        String(66),
        unique=True,
        nullable=True
    )

    from_address: Mapped[str] = mapped_column(
        String(42),
        nullable=False
    )

    to_address: Mapped[str] = mapped_column(
        String(42),
        nullable=False
    )

    amount: Mapped[float] = mapped_column(
        Numeric(18, 8),
        nullable=False
    )

    network: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="sepolia"
    )

    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="pending"
    )

    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

class WalletChallenge(Base):
    __tablename__ = "wallet_challenges"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True
    )

    customer_id: Mapped[int] = mapped_column(
    Integer,
    ForeignKey("customers.id"),
    nullable=True
    )

    wallet_address: Mapped[str] = mapped_column(
        String(42),
        nullable=False,
        index=True
    )

    nonce: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        nullable=False
    )

    message: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    expires_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        nullable=False
    )

    used_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )

    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

class Refund(Base):
    __tablename__ = "refunds"

    # Primary key
    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True
    )

    # Link refund to original payment
    payment_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("payments.payment_id"),
        nullable=False,
        index=True
    )

    # Refund amount
    amount: Mapped[float] = mapped_column(
        Numeric(18, 8),
        nullable=False
    )

    # Merchant wallet address
    from_address: Mapped[str] = mapped_column(
        String(42),
        nullable=False
    )

    # Customer wallet address
    to_address: Mapped[str] = mapped_column(
        String(42),
        nullable=False
    )

    # Blockchain transaction hash
    transaction_hash: Mapped[str] = mapped_column(
        String(66),
        unique=True,
        nullable=True
    )

    # Refund status
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="pending"
    )

    # Refund creation time
    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )