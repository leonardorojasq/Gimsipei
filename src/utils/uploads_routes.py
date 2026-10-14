"""Upload pipeline routes: serve files from src/static/uploads with
strict no-cache headers so the browser does not keep showing an image
that was deleted (or that was replaced by a new upload with the same
timestamp + filename). Also exposes an admin-only endpoint to scan for
and reap orphan files.
"""
import os

from flask import Blueprint, abort, request, send_from_directory

from src.models.user import UserRole
from src.utils.api_response import ApiResponse
from src.utils.app_logger import logger
from src.utils.decorator_role_required import role_required
from src.utils.orphan_cleanup import cleanup_orphan_uploads

uploads_bp = Blueprint("uploads", __name__, url_prefix="/uploads")

_BASE_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "src",
    "static",
    "uploads",
)


_NO_CACHE_HEADERS = {
    "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
    "Pragma": "no-cache",
    "Expires": "0",
}


@uploads_bp.route("/<path:filepath>")
@role_required([UserRole.TEACHER, UserRole.ADMIN, UserRole.STUDENT])
def serve_upload(filepath: str):
    """Serve a file from src/static/uploads/<...>.

    Requires login (any role) so anonymous users cannot enumerate
    uploaded resources. Sets aggressive no-cache headers so the
    browser never serves a stale image after a delete + re-upload
    cycle.
    """
    if ".." in filepath or filepath.startswith("/"):
        abort(400)

    full = os.path.normpath(os.path.join(_BASE_DIR, filepath))
    if not full.startswith(_BASE_DIR):
        abort(403)
    if not os.path.isfile(full):
        abort(404)

    response = send_from_directory(_BASE_DIR, filepath)
    response.headers.update(_NO_CACHE_HEADERS)
    return response


@uploads_bp.route("/admin/cleanup-orphans", methods=["POST"])
@role_required([UserRole.ADMIN])
def admin_cleanup_orphans():
    """Reap orphan files in src/static/uploads/.

    Body (JSON, optional):
      { "dry_run": true|false }   defaults to true

    Response:
      { "scanned": N, "referenced": M, "removed": [paths], "kept": [paths], "errors": [...] }
    """
    payload = request.get_json(silent=True) or {}
    dry_run = bool(payload.get("dry_run", True))

    result = cleanup_orphan_uploads(dry_run=dry_run)
    logger.warning(
        "Orphan cleanup executed by admin (dry_run=%s, removed=%d, errors=%d)",
        dry_run,
        len(result["removed"]),
        len(result["errors"]),
    )
    return ApiResponse.success(
        data={
            "dry_run": dry_run,
            "scanned_count": len(result["scanned"]),
            "referenced_count": result["referenced"],
            "removed_count": len(result["removed"]),
            "removed_sample": result["removed"][:50],
            "kept_count": len(result["kept"]),
            "errors": result["errors"],
        },
        message=(
            f"Dry run: {len(result['removed'])} orphan file(s) would be removed"
            if dry_run
            else f"Removed {len(result['removed'])} orphan file(s)"
        ),
    )

