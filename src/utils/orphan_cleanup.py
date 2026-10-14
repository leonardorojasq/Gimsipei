"""Orphan file cleanup utility.

Scans src/static/uploads/ and removes any file that is NOT referenced
by any DB column that stores a /static/uploads/... URL. The DB columns
we know about:

  Subject.image_url
  ClassModel.cover_image
  ClassContent.content_image
  Resource.cover_image
  Resource.file_url
  AssignmentSubmission.file_url
  (Book cover_image, but books are in a different upload path — skipped here)

Usage:
  from src.utils.orphan_cleanup import cleanup_orphan_uploads
  result = cleanup_orphan_uploads(dry_run=True)
  print(result)
  result = cleanup_orphan_uploads(dry_run=False)
"""
import os

from src.database.database import SessionLocal
from src.models.assignment_submission import AssignmentSubmission
from src.models.class_content import ClassContent
from src.models.class_model import ClassModel
from src.models.resource import Resource
from src.models.subject import Subject

_BASE_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "src",
    "static",
    "uploads",
)

_TABLE_PATHS: dict[type, str] = {
    Subject: "image_url",
    ClassModel: "cover_image",
    ClassContent: "content_image",
    Resource: "cover_image",  # Resource.cover_image AND Resource.file_url handled below
    AssignmentSubmission: "file_url",
}


def _collect_referenced_paths() -> set[str]:
    """Query every known table and collect the /static/uploads/... URLs."""
    referenced: set[str] = set()
    db = SessionLocal()
    try:
        for model, col in _TABLE_PATHS.items():
            for row in db.query(model).all():
                val = getattr(row, col, None)
                if isinstance(val, str) and val:
                    referenced.add(val)
        # Resource has a second path column
        for r in db.query(Resource).all():
            if isinstance(r.file_url, str) and r.file_url:
                referenced.add(r.file_url)
    finally:
        db.close()
    return referenced


def _is_under_uploads(path: str) -> bool:
    return path.startswith("/static/uploads/") or path.startswith("static/uploads/")


def cleanup_orphan_uploads(dry_run: bool = True) -> dict:
    """Walk src/static/uploads/ and remove files not referenced by the DB.

    Returns a dict with keys: scanned, referenced, removed, kept, errors.
    """
    referenced_urls = _collect_referenced_paths()

    # Normalize the referenced URLs to absolute paths
    referenced_paths: set[str] = set()
    for url in referenced_urls:
        stripped = url.lstrip("/")
        if not stripped.startswith("static/uploads/"):
            continue
        # strip the "static/uploads/" prefix to get the path under UPLOADS
        rel = stripped[len("static/uploads/"):]
        referenced_paths.add(os.path.normpath(os.path.join(_BASE_DIR, rel)))

    scanned: list[str] = []
    removed: list[str] = []
    kept: list[str] = []
    errors: list[tuple[str, str]] = []

    if not os.path.isdir(_BASE_DIR):
        return {
            "scanned": scanned,
            "referenced": len(referenced_paths),
            "removed": removed,
            "kept": kept,
            "errors": errors,
        }

    for dirpath, _dirnames, filenames in os.walk(_BASE_DIR):
        for fn in filenames:
            full = os.path.normpath(os.path.join(dirpath, fn))
            scanned.append(full)
            if full in referenced_paths:
                kept.append(full)
                continue
            if not dry_run:
                try:
                    os.remove(full)
                    removed.append(full)
                except Exception as exc:
                    errors.append((full, str(exc)))
            else:
                # dry run: just report what would be removed
                removed.append(full)

    return {
        "scanned": scanned,
        "referenced": len(referenced_paths),
        "removed": removed,
        "kept": kept,
        "errors": errors,
    }
