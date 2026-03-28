"""
Logging configuration for the Trading Bot.
Sets up structured logging to both console and a rotating log file.
"""

import logging
import logging.handlers
import os
from pathlib import Path


LOG_DIR = Path(__file__).parent.parent / "logs"
LOG_FILE = LOG_DIR / "trading_bot.log"
LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def setup_logging(log_level: str = "INFO") -> None:
    """
    Configure root logger with:
      - A rotating file handler (writes to logs/trading_bot.log)
      - A console (stream) handler
    """
    LOG_DIR.mkdir(exist_ok=True)

    numeric_level = getattr(logging, log_level.upper(), logging.INFO)

    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)

    # Avoid adding duplicate handlers if called multiple times
    if root_logger.handlers:
        return

    formatter = logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT)

    # Rotating file handler – keeps last 5 × 5 MB log files
    file_handler = logging.handlers.RotatingFileHandler(
        LOG_FILE,
        maxBytes=5 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setLevel(numeric_level)
    file_handler.setFormatter(formatter)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.WARNING)  # Only warnings+ to console; file gets everything
    console_handler.setFormatter(formatter)

    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
