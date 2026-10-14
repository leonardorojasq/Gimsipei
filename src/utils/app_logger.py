"""Centralized logger for critical application errors.

Writes ERROR and CRITICAL messages to both:
- The console (for dev visibility)
- A rotating file under <project>/logs/errors.log by default.
  If that directory cannot be created or written to (e.g. because the
  gunicorn worker doesn't have write permission in the project root
  inside a Docker image) we fall back to a system temp dir so the
  worker still boots.

The rest of the app should `from src.utils.app_logger import logger` and
call `logger.error(...)` / `logger.critical(...)` for failures that need
post-mortem visibility (file deletions, integrity errors, unhandled
exceptions in delete flows, orphan file cleanup, etc.).
"""
import logging
import os
import tempfile
from logging.handlers import RotatingFileHandler


# These are recomputed on every _ensure_log_handlers() call so a
# permission change between worker boots (or a runtime that lazily
# imports the module) is handled. Importing the module triggers the
# first computation; if that fails we fall back to console-only.

def _fallback_dir() -> str:
    return os.path.join(tempfile.gettempdir(), "gimsipei-logs")


def _primary_dir() -> str:
    return os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        "logs",
    )


def _resolve_paths() -> tuple[str | None, str | None]:
    """Pick a (log_dir, log_file) pair that the current process can write to.

    Returns (None, None) if neither the project logs dir nor /tmp works —
    in that case the logger will run in console-only mode.
    """
    for candidate_dir in (_primary_dir(), _fallback_dir()):
        try:
            os.makedirs(candidate_dir, exist_ok=True)
            probe = os.path.join(candidate_dir, ".write_probe")
            with open(probe, "w") as f:
                f.write("ok")
            os.remove(probe)
            return candidate_dir, os.path.join(candidate_dir, "errors.log")
        except OSError:
            continue
    return None, None


logger = logging.getLogger("gimsipei")
# Set to the lowest level we want to capture anywhere; per-handler levels
# decide what actually gets written. (See _ensure_log_handlers below.)
logger.setLevel(logging.DEBUG)
logger.propagate = False  # don't bubble to Flask's root logger (avoids double log lines)


def _ensure_log_handlers():
    if logger.handlers:
        return
    log_dir, log_file = _resolve_paths()
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(funcName)s:%(lineno)d | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    if log_dir and log_file:
        # File handler logs from INFO up so delete / upload / cleanup
        # operations leave a trail; the user can grep the file even
        # when nothing failed.
        try:
            file_handler = RotatingFileHandler(
                log_file,
                maxBytes=5 * 1024 * 1024,  # 5MB
                backupCount=3,
                encoding="utf-8",
            )
            file_handler.setLevel(logging.INFO)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        except OSError as exc:
            # Read-only filesystem, etc. Fall back to console only.
            print(
                f"[gimsipei] WARNING: cannot open log file {log_file!r}: {exc}. "
                "Falling back to console-only logging.",
                flush=True,
            )
    else:
        print(
            "[gimsipei] WARNING: cannot create any log directory. "
            "Falling back to console-only logging.",
            flush=True,
        )

    # Console stays at ERROR so dev output isn't spammed by routine ops.
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.ERROR)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)


_ensure_log_handlers()
