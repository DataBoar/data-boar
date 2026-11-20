"""SigV4 for GET requests of the ``object_storage`` reader, driver ``s3`` (#2306, task 2306.1).

Source: ``docs/desenho/2306.md``, section 5, option B of P-1 (operator decision, 2026-11-20):
``botocore.auth.S3SigV4Auth`` signs with explicit ``Credentials``. No ``boto3``, no botocore
session or client, no implicit credential chain. ``botocore`` is imported lazily, inside
the functions, because it ships in the optional ``cloud`` extra.

``botocore.auth`` logs the canonical request (which carries ``x-amz-security-token``) at
DEBUG. :data:`BOTOCORE_AUTH_LOG_FILTER` drops every record of that logger; it is installed
once by :func:`install_botocore_log_filter` and never changes any logger level.
"""

from __future__ import annotations

import logging
from datetime import datetime

BOTOCORE_AUTH_LOGGER = "botocore.auth"


class _DropAllRecords(logging.Filter):
    """Logger filter that discards every record (section 5, item 6)."""

    def filter(self, record: logging.LogRecord) -> bool:
        raise NotImplementedError("2306.1: botocore.auth log filter")


BOTOCORE_AUTH_LOG_FILTER = _DropAllRecords()


def install_botocore_log_filter() -> None:
    raise NotImplementedError("2306.1: install_botocore_log_filter")


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
) -> tuple[str, dict[str, str]]:
    """Return ``(exact_query_string_to_send, headers_to_send)``."""
    raise NotImplementedError("2306.1: sign_get")
