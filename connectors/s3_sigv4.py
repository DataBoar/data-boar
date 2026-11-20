"""SigV4 for GET requests of the ``object_storage`` reader, drivers ``s3`` and ``s3_compatible``.

Source: ``docs/desenho/2306.md``, section 5, option A of P-1 (operator decision, revision 5,
2026-11-20): the project's own AWS Signature Version 4, GET only, service ``s3``, algorithm
``AWS4-HMAC-SHA256``, with ``hmac`` and ``hashlib`` from the standard library. No third-party
signer and no new dependency. The clock is the ``now`` argument. This module logs nothing,
and the secret access key never leaves :func:`sign_get` (not in the return value, not in an
exception, not in a log).
"""

from __future__ import annotations

import hashlib
import hmac
import re
from collections.abc import Mapping
from datetime import datetime, timezone
from urllib.parse import quote

_ALGORITHM = "AWS4-HMAC-SHA256"
_SERVICE = "s3"
EMPTY_PAYLOAD_SHA256 = hashlib.sha256(b"").hexdigest()
_REGION_RE = re.compile(r"[a-z0-9]([a-z0-9-]{0,30}[a-z0-9])?")
_HEADER_NAME_RE = re.compile(r"[a-z0-9][a-z0-9-]*")
_RESERVED_HEADERS = frozenset({"host", "authorization", "x-amz-date"})


def uri_encode(value: str, *, keep_slash: bool) -> str:
    """AWS URI encoding: ``A-Z a-z 0-9 - _ . ~`` stay; the rest is ``%XX`` (upper case,
    byte by byte of the UTF-8 form). ``/`` stays only with ``keep_slash=True``."""
    if not isinstance(value, str):
        raise ValueError("uri_encode expects text")
    try:
        return quote(value, safe="-_.~/" if keep_slash else "-_.~", errors="strict")
    except UnicodeEncodeError:
        raise ValueError("value is not valid text for a URI") from None


def _hmac(key: bytes, msg: str) -> bytes:
    return hmac.new(key, msg.encode("utf-8"), hashlib.sha256).digest()


def _single_line(value: str) -> bool:
    return not any(ord(ch) < 0x20 or ord(ch) == 0x7F for ch in value)


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
    if not isinstance(region, str) or not _REGION_RE.fullmatch(region):
        raise ValueError("region is invalid for SigV4")
    if not isinstance(now, datetime) or now.utcoffset() is None:
        raise ValueError("now must be a timezone-aware datetime")
    if (
        not isinstance(host_header, str)
        or not host_header
        or not _single_line(host_header)
    ):
        raise ValueError("host header is invalid for SigV4")
    if (
        not isinstance(canonical_uri, str)
        or not canonical_uri.startswith("/")
        or not _single_line(canonical_uri)
        or " " in canonical_uri
    ):
        raise ValueError("canonical URI is invalid for SigV4")
    for label, value in (
        ("access key id", access_key_id),
        ("secret access key", secret_access_key),
    ):
        if not isinstance(value, str) or not value or not _single_line(value):
            raise ValueError(f"{label} is invalid for SigV4")
    if session_token is not None and (
        not isinstance(session_token, str)
        or not session_token
        or not _single_line(session_token)
    ):
        raise ValueError("session token is invalid for SigV4")

    pairs = sorted(
        (
            uri_encode(str(name), keep_slash=False),
            uri_encode(str(value), keep_slash=False),
        )
        for name, value in query
    )
    canonical_query = "&".join(f"{name}={value}" for name, value in pairs)

    stamp = now.astimezone(timezone.utc)
    amz_date = stamp.strftime("%Y%m%dT%H%M%SZ")
    day = amz_date[:8]

    signed: dict[str, str] = {
        "host": host_header,
        "x-amz-content-sha256": EMPTY_PAYLOAD_SHA256,
        "x-amz-date": amz_date,
    }
    if session_token is not None:
        signed["x-amz-security-token"] = session_token
    extras: dict[str, str] = {}
    for raw_name, raw_value in (extra_headers or {}).items():
        name = str(raw_name).strip().lower()
        if (
            not _HEADER_NAME_RE.fullmatch(name)
            or name in _RESERVED_HEADERS
            or name.startswith("x-amz-")
            or name in extras
        ):
            raise ValueError("extra header name is not accepted for SigV4")
        value = " ".join(str(raw_value).split())
        if not _single_line(value):
            raise ValueError("extra header value is invalid for SigV4")
        extras[name] = value
    signed.update(extras)

    names = sorted(signed)
    signed_headers = ";".join(names)
    canonical_headers = "".join(f"{name}:{signed[name]}\n" for name in names)
    canonical_request = "\n".join(
        [
            "GET",
            canonical_uri,
            canonical_query,
            canonical_headers,
            signed_headers,
            EMPTY_PAYLOAD_SHA256,
        ]
    )
    scope = f"{day}/{region}/{_SERVICE}/aws4_request"
    string_to_sign = "\n".join(
        [
            _ALGORITHM,
            amz_date,
            scope,
            hashlib.sha256(canonical_request.encode("utf-8")).hexdigest(),
        ]
    )
    key = _hmac(("AWS4" + secret_access_key).encode("utf-8"), day)
    for part in (region, _SERVICE, "aws4_request"):
        key = _hmac(key, part)
    signature = hmac.new(
        key, string_to_sign.encode("utf-8"), hashlib.sha256
    ).hexdigest()

    headers = {
        "Authorization": (
            f"{_ALGORITHM} Credential={access_key_id}/{scope}, "
            f"SignedHeaders={signed_headers}, Signature={signature}"
        ),
        "X-Amz-Date": amz_date,
        "X-Amz-Content-SHA256": EMPTY_PAYLOAD_SHA256,
    }
    if session_token is not None:
        headers["X-Amz-Security-Token"] = session_token
    headers.update(extras)
    return canonical_query, headers
