"""Centralized logger for critical application errors.

Writes ERROR and CRITICAL messages to both:
- The console (for dev visibility)
- logs/errors.log in the project root (rotated at 5MB, 3 backups)

The rest of the app should `from src.utils.app_logger import logger` and
call `logger.error(...)` / `logger.critical(...)` for failures that need
post-mortem visibility (file deletions, integrity errors, unhandled
exceptions in delete flows, orphan file cleanup, etc.).
"""
import logging
import os
from logging.handlers import RotatingFileHandler

_LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "logs")
_LOG_FILE = os.path.join(_LOG_DIR, "errors.log")

logger = logging.getLogger("gimsipei")
# Set to the lowest level we want to capture anywhere; per-handler levels
# decide what actually gets written. (See _ensure_log_handlers below.)
logger.setLevel(logging.DEBUG)
logger.propagate = False  # don't bubble to Flask's root logger (avoids double log lines)


def _ensure_log_handlers():
    if logger.handlers:
        return
    os.makedirs(_LOG_DIR, exist_ok=True)

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(funcName)s:%(lineno)d | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # File handler logs from INFO up so delete / upload / cleanup operations
    # leave a trail; the user can grep logs/errors.log for activity even
    # when nothing failed.
    file_handler = RotatingFileHandler(
        _LOG_FILE,
        maxBytes=5 * 1024 * 1024,  # 5MB
        backupCount=3,
        encoding="utf-8",
    )
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # Console stays at ERROR so dev output isn't spammed by routine ops.
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.ERROR)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)


_ensure_log_handlers()
