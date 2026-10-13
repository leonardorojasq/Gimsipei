"""Jinja template filters for the application."""

from enum import Enum

_ROLE_LABELS = {
    "TEACHER": "Docente",
    "ADMIN": "Administrador",
    "STUDENT": "Estudiante",
}


def role_label(role):
    """Return the human-friendly Spanish label for a user role.

    Accepts plain strings (``"ADMIN"`` / ``"admin"``) or
    :class:`~enum.Enum` members whose value is one of the role codes.
    Unknown values fall back to ``str(role)``.
    """
    if role is None:
        return ""
    if isinstance(role, Enum):
        key = str(role.value).upper()
    else:
        key = str(role).upper()
    return _ROLE_LABELS.get(key, str(role))


def register_jinja_filters(app):
    """Register all custom Jinja filters on the Flask app."""
    app.add_template_filter(role_label, "role_label")
