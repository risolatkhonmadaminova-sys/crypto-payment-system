
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
import os

from dotenv import load_dotenv

load_dotenv()


# Database connection URL
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL is not configured"
    )


# Create database engine
engine = create_engine(
    DATABASE_URL,
    echo=True
)


# Create database sessions
SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False
)


# Base class for database models
class Base(DeclarativeBase):
    pass

# Database session dependency
def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()

# Import models to register them with SQLAlchemy
from app.db import models