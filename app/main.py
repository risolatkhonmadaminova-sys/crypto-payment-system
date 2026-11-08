from fastapi import FastAPI

from app.api.payments import router as payments_router

from app.api.customers import router as customers_router
from app.api.blockchain import router as blockchain_router
from fastapi.middleware.cors import CORSMiddleware
from app.api.wallet import router as wallet_router
from app.api.refunds import router as refunds_router
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from fastapi import Request
from fastapi.responses import JSONResponse

from app.security.rate_limiter import limiter
import logging

from app.core.logging_config import setup_logging

setup_logging()
from app.api.merchant_auth import router as merchant_auth_router

logger = logging.getLogger("app")

app = FastAPI(
    title="Crypto Payment System",
    description="Backend API for cryptocurrency payments",
    version="1.0.0"
)
logger = logging.getLogger("app")


@app.exception_handler(Exception)
async def global_exception_handler(
    request: Request,
    exc: Exception
):
    logger.exception(
        "Unhandled application error: method=%s path=%s",
        request.method,
        request.url.path
    )

    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error"
        }
    )

logger.info("Crypto Payment System application initialized")

app.state.limiter = limiter

app.add_exception_handler(
    RateLimitExceeded,
    _rate_limit_exceeded_handler
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5500"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE"],
    allow_headers=["*"],
)


app.include_router(payments_router)
app.include_router(customers_router)
app.include_router(blockchain_router)
app.include_router(wallet_router)
app.include_router(refunds_router)
app.include_router(merchant_auth_router)


@app.get("/")
def home():
    return {
        "message": "Welcome to Crypto Payment System",
        "status": "running"
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy"
    }