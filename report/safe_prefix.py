"""Safe filename prefixes from operator-supplied session ids (path traversal hardening)."""

from __future__ import annotations

import re


def safe_session_prefix(session_id: str, *, max_len: int = 16) -> str:
    """
    Return a basename-safe prefix (no path separators, no parent traversal).

    UUID-style ids keep hex + hyphen; anything else is reduced to [A-Za-z0-9_-].
    """
    raw = (session_id or "").strip()
    if not raw:
        return "session"
    if max_len < 4:
        max_len = 4
    chunk = raw[:max_len]
    if re.fullmatch(r"[0-9a-fA-F-]{8,}", chunk):
        return re.sub(r"[^0-9a-fA-F-]+", "", chunk)[:max_len] or "session"
    cleaned = re.sub(r"[^0-9a-zA-Z_-]+", "_", chunk).strip("_")
    return (cleaned or "session")[:max_len]


__all__ = ["safe_session_prefix"]
