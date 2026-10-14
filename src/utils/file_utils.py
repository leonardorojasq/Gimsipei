"""Filesystem helpers for the upload pipeline.

These wrappers centralize the path-resolution + os.remove logic that
delete services use, so the rules are consistent and every failure is
logged to the central app logger.
"""
import os

from src.utils.app_logger import logger


def safe_remove_file(file_path: str | None) -> bool:
    """Remove a file at *file_path*, swallowing FileNotFoundError but
    logging any other failure. Returns True if the file was removed or
    did not exist, False if the removal failed for a real reason
    (permissions, file in use, etc.)."""
    if not file_path:
        return True
    if not os.path.exists(file_path):
        return True
    try:
        os.remove(file_path)
        return True
    except FileNotFoundError:
        return True
    except Exception as exc:
        logger.error("Failed to remove file %s: %s", file_path, exc)
        return False


def path_from_static_url(static_url: str | None, base: str = "src") -> str | None:
    """Resolve a /static/uploads/... URL to a filesystem path under *base*.

    e.g. path_from_static_url("/static/uploads/resources/covers/x.png")
         → "src/static/uploads/resources/covers/x.png"

    Returns None if the input is empty/None. The /static prefix is
    stripped before joining, and a leading slash is also stripped so
    that os.path.join doesn't discard the *base* prefix.
    """
    if not static_url or not isinstance(static_url, str):
        return None
    stripped = static_url.lstrip("/")
    if not stripped:
        return None
    return os.path.join(base, stripped)


def make_unique_filename(folder: str, filename: str) -> str:
    """Return a filename that does not yet exist in *folder*.

    If *filename* already exists, appends "_1", "_2", ... before the
    extension until a free slot is found. The first attempt is the
    unchanged input, so when there's no collision the original
    filename is returned (and the timestamp/microsecond prefix still
    gives the second-precision uniqueness that the upstream code
    relies on for human-readable names).
    """
    if not os.path.exists(os.path.join(folder, filename)):
        return filename
    base, ext = os.path.splitext(filename)
    counter = 1
    while True:
        candidate = f"{base}_{counter}{ext}"
        if not os.path.exists(os.path.join(folder, candidate)):
            return candidate
        counter += 1
