"""Auth-failure audit records. The supplied key is never part of the record."""

from __future__ import annotations

import logging

audit_logger = logging.getLogger("data_boar.auth.audit")


_AUDIT_FIELD_MAX = 200


def _audit_field(value: object) -> str:
    """One log token: no raw controls or spaces, capped length."""
    text = str(value)[:_AUDIT_FIELD_MAX]
    parts: list[str] = []
    for char in text:
        if char.isprintable() and char != " ":
            parts.append(char)
        else:
            parts.append("\\x%02x" % ord(char))
    return "".join(parts)


def record_auth_failure(*, method: str, path: str, source: str, reason: str) -> None:
    """Write one Audit Trail line: time (log record), method, path, source, reason."""
    audit_logger.warning(
        "AUTH_AUDIT action=auth_failure method=%s path=%s source=%s reason=%s",
        _audit_field(method),
        _audit_field(path),
        source,
        reason,
    )
