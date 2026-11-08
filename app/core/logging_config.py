
import logging
from pathlib import Path
from logging.handlers import RotatingFileHandler


# Project root directory
BASE_DIR = Path(__file__).resolve().parents[2]

# Logs directory
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)

# Log file
LOG_FILE = LOG_DIR / "app.log"


def setup_logging():
    logger = logging.getLogger("app")

    # Prevent duplicate handlers
    if logger.handlers:
        return

    logger.setLevel(logging.INFO)
    logger.propagate = False

    # Log format
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    )

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    # File handler with rotation
    file_handler = RotatingFileHandler(
        LOG_FILE,
        maxBytes=5 * 1024 * 1024,
        backupCount=3,
        encoding="utf-8"
    )
    file_handler.setFormatter(formatter)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
