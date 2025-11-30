"""
Common utility functions shared across apps.

Lightweight helpers with no external dependencies.
"""

from __future__ import annotations

import uuid
import re
from typing import Any, Dict


def to_uuid(value: str | uuid.UUID) -> uuid.UUID:
    """Coerce string to UUID, raising ValueError on invalid input."""
    if isinstance(value, uuid.UUID):
        return value
    return uuid.UUID(str(value))


_slug_re = re.compile(r"[^a-z0-9-]+")


def slugify(text: str) -> str:
    """Simple slugify: lowercases, replaces spaces with dashes, strips invalid chars."""
    text = text.strip().lower().replace(" ", "-")
    text = _slug_re.sub("", text)
    return re.sub(r"-+", "-", text).strip("-")


def mask_email(email: str) -> str:
    """Mask email for logs: j***e@example.com."""
    try:
        local, domain = email.split("@", 1)
        if len(local) <= 2:
            return f"*{'*' * max(0, len(local) - 1)}@{domain}"
        return f"{local[0]}***{local[-1]}@{domain}"
    except Exception:
        return "***"


def safe_get(d: Dict[str, Any], path: str, default: Any = None) -> Any:
    """Nested dict getter using dot-path: safe_get(obj, "a.b.c", default)."""
    cur: Any = d
    for part in path.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return default
        cur = cur[part]
    return cur
