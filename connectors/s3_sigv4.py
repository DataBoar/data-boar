"""SigV4 for GET requests of the ``object_storage`` reader, drivers ``s3`` and ``s3_compatible``.

Source: ``docs/desenho/2306.md``, section 5, option A of P-1 (operator decision, revision 5,
2026-11-20): the project's own AWS Signature Version 4, GET only, service ``s3``, algorithm
``AWS4-HMAC-SHA256``, with ``hmac`` and ``hashlib`` from the standard library. No third-party
signer and no new dependency. The clock is the ``now`` argument. This module logs nothing,
and the secret access key never leaves :func:`sign_get` (not in the return value, not in an
exception, not in a log).
"""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime


def uri_encode(value: str, *, keep_slash: bool) -> str:
    raise NotImplementedError("2306.1: uri_encode")


def sign_get(
    *,
    host_header: str,
    canonical_uri: str,
    query: list[tuple[str, str]],
    region: str,
    access_key_id: str,
    secret_access_key: str,
    session_token: str | None,
    now: datetime,
    extra_headers: Mapping[str, str] | None = None,
) -> tuple[str, dict[str, str]]:
    """Return ``(exact_query_string_to_send, headers_to_send)``.

    ``extra_headers`` are additional headers that are also signed (lower-case name, value
    stripped at both ends), such as ``range``. The connector of this delivery passes none.
    """
    raise NotImplementedError("2306.1: sign_get")
