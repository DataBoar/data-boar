"""Auth-failure audit records. The supplied key is never part of the record."""

from __future__ import annotations

import logging

audit_logger = logging.getLogger("data_boar.auth.audit")


def record_auth_failure(*, method: str, path: str, source: str, reason: str) -> None:
    """Write one Audit Trail line: time (log record), method, path, source, reason."""
    audit_logger.warning(
        "AUTH_AUDIT action=auth_failure method=%s path=%s source=%s reason=%s",
        method,
        path,
        source,
        reason,
    )
