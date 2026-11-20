"""Driver ``s3`` of the ``object_storage`` reader: Amazon S3 and compatibles (#2306, 2306.1).

Source: ``docs/desenho/2306.md``, sections 0, 2, 2a, 5, 7 and 11. One implementation, two
registered names (revision 4, DEC-15): ``s3`` (Amazon S3) and ``s3_compatible``. It joins
``s3_addressing`` (host and base path), ``s3_sigv4`` (request signing), the reading of the
``ListObjectsV2`` response (``defusedxml``) and the S3 error table. It holds no credential
beyond one call, and every message it returns is fixed text of this module.
"""

from __future__ import annotations

import re
import urllib.parse
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Literal
from xml.etree.ElementTree import Element, ParseError

from defusedxml import DefusedXmlException
from defusedxml import ElementTree as DefusedET

from connectors.object_storage_driver import (
    DriverConfigError,
    DriverProtocolError,
    DriverSettings,
    ErrorClass,
    ListPage,
    ObjectEntry,
    PreparedGet,
    ResolvedCredentials,
)
from connectors.s3_addressing import (
    S3Location,
    object_storage_host,
    resolve_location,
    validate_prefix,
)
from connectors.s3_sigv4 import sign_get, uri_encode

_ERROR_BODY_LIMIT = 64 * 1024
_SIZE_RE = re.compile(r"[0-9]+")
_MALFORMED = "malformed listing response"

# Error vocabulary of section 11: only these codes ever leave the driver.
_AUTH_CODES = frozenset(
    {
        "InvalidAccessKeyId",
        "SignatureDoesNotMatch",
        "ExpiredToken",
        "InvalidToken",
        "TokenRefreshRequired",
        "RequestTimeTooSkewed",
    }
)
_REGION_CODES = frozenset({"PermanentRedirect", "AuthorizationHeaderMalformed"})
_PERMISSION_CODES = frozenset({"AccessDenied", "AllAccessDisabled"})
_GET_CODES = frozenset({"AccessDenied", "NoSuchKey", "InvalidRequest"})
_VOCABULARY = (
    _AUTH_CODES
    | _REGION_CODES
    | _PERMISSION_CODES
    | _GET_CODES
    | frozenset({"NoSuchBucket", "SlowDown"})
)
_RETRYABLE_STATUS = frozenset({500, 502, 503, 504})


@dataclass(frozen=True)
class S3Settings(DriverSettings):
    bucket: str
    region: str
    endpoint_url: str | None
    location: S3Location


S3Variant = Literal["s3", "s3_compatible"]


def _local(tag: str) -> str:
    """Local name of an ElementTree tag; the namespace, whatever it is, is discarded
    (design section 7, revision 5 arbitration: elements are read by local name only)."""
    return tag.rpartition("}")[2] if tag.startswith("{") else tag


def _children(node: Element, name: str) -> list[Element]:
    return [c for c in node if _local(c.tag) == name]


def _text(node: Element, name: str) -> str | None:
    found = _children(node, name)
    return found[0].text if found else None


def _parse_xml(body: bytes) -> Element:
    """``defusedxml`` with DTD, entities and external references all forbidden."""
    return DefusedET.fromstring(
        body, forbid_dtd=True, forbid_entities=True, forbid_external=True
    )


def _error_code(body: bytes) -> str | None:
    """The ``<Code>`` of an S3 error body, only when it is in the vocabulary."""
    try:
        root = _parse_xml(body[:_ERROR_BODY_LIMIT])
    except (ParseError, DefusedXmlException, ValueError, SyntaxError):
        return None
    if _local(root.tag) != "Error":
        return None
    code = _text(root, "Code")
    return code if code in _VOCABULARY else None


class S3Driver:
    max_page_size = 1000
    max_key_bytes = 1024
    credential_keys: tuple[tuple[str, bool], ...] = (
        ("access_key_id_from_env", True),
        ("secret_access_key_from_env", True),
        ("session_token_from_env", False),
    )
    forbidden_inline_keys = frozenset(
        {
            "access_key_id",
            "secret_access_key",
            "session_token",
            "aws_access_key_id",
            "aws_secret_access_key",
            "aws_session_token",
        }
    )

    def __init__(self, variant: S3Variant = "s3") -> None:
        self.name: str = variant
        misnamed = dict.fromkeys(
            ("endpoint", "url", "base_url", "host"), "use endpoint_url"
        )
        if variant == "s3":
            misnamed["endpoint_url"] = "use driver s3_compatible"
        self.misnamed_keys: Mapping[str, str] = misnamed

    # -- configuration -----------------------------------------------------

    def _own(self, settings: DriverSettings) -> S3Settings:
        if not isinstance(settings, S3Settings):
            raise TypeError("settings were not built by the S3 driver")
        return settings

    def settings(self, cfg: dict[str, Any]) -> S3Settings:
        if not isinstance(cfg, dict) or cfg.get("driver") != self.name:
            raise DriverConfigError(f"target is not configured for driver {self.name}")
        # S3ConfigError is a DriverConfigError with a fixed message (no configured value).
        location = resolve_location(cfg)
        validate_prefix(cfg.get("prefix", ""))
        endpoint = cfg.get("endpoint_url") if self.name == "s3_compatible" else None
        return S3Settings(
            bucket=str(cfg["bucket"]),
            region=location.region,
            endpoint_url=str(endpoint) if endpoint is not None else None,
            location=location,
        )

    def destination(self, settings: DriverSettings) -> str:
        loc = self._own(settings).location
        host = f"[{loc.host}]" if ":" in loc.host else loc.host
        return f"https://{host}" + (f":{loc.port}" if loc.port is not None else "")

    def destination_host(self, cfg: dict[str, Any]) -> str:
        if not isinstance(cfg, dict) or cfg.get("driver") != self.name:
            return ""
        return object_storage_host(cfg)

    # -- requests ----------------------------------------------------------

    def _signed(
        self,
        settings: S3Settings,
        creds: ResolvedCredentials,
        canonical_uri: str,
        query: list[tuple[str, str]],
        now: datetime,
    ) -> PreparedGet:
        raw_query, headers = sign_get(
            host_header=settings.location.host_header,
            canonical_uri=canonical_uri,
            query=query,
            region=settings.region,
            access_key_id=creds["access_key_id_from_env"],
            secret_access_key=creds["secret_access_key_from_env"],
            session_token=creds.get("session_token_from_env"),
            now=now,
        )
        url = self.destination(settings) + canonical_uri
        if raw_query:
            url += "?" + raw_query
        return PreparedGet(url, headers)

    def list_request(
        self,
        settings: DriverSettings,
        creds: ResolvedCredentials,
        prefix: str,
        token: str | None,
        page_size: int,
        now: datetime,
    ) -> PreparedGet:
        s3 = self._own(settings)
        if (
            isinstance(page_size, bool)
            or not isinstance(page_size, int)
            or not 1 <= page_size <= self.max_page_size
        ):
            raise ValueError("page size is out of range for S3")
        query = [
            ("list-type", "2"),
            ("prefix", prefix),
            ("max-keys", str(page_size)),
            ("encoding-type", "url"),
        ]
        if token is not None:
            query.append(("continuation-token", token))
        return self._signed(s3, creds, s3.location.base_path or "/", query, now)

    def get_request(
        self,
        settings: DriverSettings,
        creds: ResolvedCredentials,
        key: str,
        now: datetime,
    ) -> PreparedGet:
        s3 = self._own(settings)
        uri = s3.location.base_path + "/" + uri_encode(key, keep_slash=True)
        return self._signed(s3, creds, uri, [], now)

    # -- listing -----------------------------------------------------------

    def parse_list(self, body: bytes) -> ListPage:
        try:
            root = _parse_xml(body)
        except (ParseError, DefusedXmlException, ValueError, SyntaxError):
            raise DriverProtocolError(_MALFORMED) from None
        if _local(root.tag) != "ListBucketResult":
            raise DriverProtocolError(_MALFORMED)
        truncated_text = _text(root, "IsTruncated")
        if truncated_text not in ("true", "false"):
            raise DriverProtocolError(_MALFORMED)
        encoding = _text(root, "EncodingType")
        if encoding not in (None, "url"):
            raise DriverProtocolError(_MALFORMED)
        entries = [
            self._entry(item, url_encoded=encoding == "url")
            for item in _children(root, "Contents")
        ]
        return ListPage(
            entries, _text(root, "NextContinuationToken"), truncated_text == "true"
        )

    @staticmethod
    def _entry(item: Element, *, url_encoded: bool) -> ObjectEntry:
        size_text = _text(item, "Size")
        size = int(size_text) if size_text and _SIZE_RE.fullmatch(size_text) else None
        raw_key = _text(item, "Key")
        if size is None or not raw_key:
            # D2306-82: no valid Size, or no key -> invalid for the driver.
            return ObjectEntry(None, None)
        if not url_encoded:
            return ObjectEntry(raw_key, size)
        try:
            return ObjectEntry(
                urllib.parse.unquote_plus(raw_key, errors="strict"), size
            )
        except UnicodeDecodeError:
            return ObjectEntry(None, size)

    # -- errors ------------------------------------------------------------

    def classify_error(
        self,
        status: int,
        headers: Mapping[str, str],
        body: bytes,
        *,
        during: Literal["list", "get"],
    ) -> ErrorClass:
        """Section 11. ``headers`` are never read into the message (Retry-After is the
        common layer's)."""
        code = _error_code(body)
        listing = during == "list"
        generic = f"S3 error HTTP {int(status)}"
        if code in _AUTH_CODES:
            if code == "RequestTimeTooSkewed":
                text = (
                    "authentication failed: clock skew between this host and the "
                    "server (RequestTimeTooSkewed)"
                )
            else:
                text = f"authentication failed ({code})"
            return ErrorClass("auth_failed", code, False, True, text)
        if code in _REGION_CODES and (code != "PermanentRedirect" or status == 301):
            return ErrorClass(
                "config_error",
                code,
                False,
                True,
                f"bucket is not in region configured for this target ({code})",
            )
        if 300 <= status < 400:
            return ErrorClass("scope_violation", None, False, True, "redirect refused")
        if status in _RETRYABLE_STATUS or code == "SlowDown":
            kept = code if code == "SlowDown" else None
            if not listing:
                return ErrorClass("download_failed", kept, True, False, generic)
            if status == 503 or code == "SlowDown":
                return ErrorClass(
                    "throttled", kept, True, True, "S3 throttled the request (SlowDown)"
                )
            return ErrorClass("unreachable", None, True, True, generic)
        if not listing:
            kept = code if code in _GET_CODES else None
            text = f"download failed ({kept})" if kept else generic
            return ErrorClass("download_failed", kept, False, False, text)
        if code in _PERMISSION_CODES:
            return ErrorClass(
                "permission_denied",
                code,
                False,
                True,
                f"listing permission denied ({code})",
            )
        if code == "NoSuchBucket":
            return ErrorClass(
                "not_found", code, False, True, "bucket not found (NoSuchBucket)"
            )
        if status == 403:
            return ErrorClass("permission_denied", None, False, True, generic)
        if status == 404:
            return ErrorClass("not_found", None, False, True, generic)
        return ErrorClass("protocol_error", None, False, True, generic)

    # -- presentation ------------------------------------------------------

    def display_path(self, settings: DriverSettings, key: str) -> str:
        return f"s3://{self._own(settings).bucket}/{key}"

    def inventory_identity(self, settings: DriverSettings) -> dict[str, str]:
        s3 = self._own(settings)
        identity = {
            "product": "Amazon S3" if self.name == "s3" else "S3-compatible",
            "protocol_or_api_version": "S3 ListObjectsV2",
            "engine": "s3",
            "bucket": s3.bucket,
            "region": s3.region,
            "addressing": s3.location.addressing,
        }
        if s3.endpoint_url is not None:
            host = urllib.parse.urlsplit(s3.endpoint_url).hostname
            identity["endpoint_host"] = (host or "").lower()
        return identity
