"""S3 addressing for the ``object_storage`` reader, driver ``s3`` (#2306, task 2306.1).

Source: ``docs/desenho/2306.md``, sections 1, 2 and 2a (revision 4). Pure (no I/O):
validation of ``bucket``, ``region``, ``endpoint_url``, ``addressing_style`` and ``prefix``;
the single host and the base path of a target. Two drivers share this module (DEC-15):

- ``s3`` (Amazon S3): virtual-hosted style only, ``endpoint_url`` and ``addressing_style``
  refused, bucket with a dot refused. The AWS host is built only in :func:`_aws_virtual_host`.
- ``s3_compatible``: ``endpoint_url`` required, ``addressing_style`` ``path`` (default) or
  ``virtual``. No check of whether the host belongs to AWS.

Every error message is fixed text that names the key, never the configured value.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Literal
from urllib.parse import urlsplit

from connectors.object_storage_driver import DriverConfigError

_DRIVERS = ("s3", "s3_compatible")
_MISNAMED_DESTINATION_KEYS = ("endpoint", "url", "base_url", "host")
_BUCKET_RE = re.compile(r"[a-z0-9][a-z0-9.-]{1,61}[a-z0-9]")
_IPV4_SHAPE_RE = re.compile(r"\d+\.\d+\.\d+\.\d+")
_AWS_REGION_RE = re.compile(r"[a-z]{2}(-[a-z]+)+-\d{1,2}")
_GENERIC_REGION_RE = re.compile(r"[a-z0-9]([a-z0-9-]{0,30}[a-z0-9])?")
_MAX_PREFIX_BYTES = 1024


@dataclass(frozen=True)
class S3Location:
    host: str  # lower-case hostname, no port
    port: int | None  # None when absent or 443
    host_header: str  # host, or "host:port" when the port is neither 80 nor 443
    base_path: str  # "" (virtual-hosted style) or "/<bucket>" (path style)
    addressing: Literal["virtual", "path"]
    region: str


class S3ConfigError(DriverConfigError):
    """``str(exc)`` is a fixed message of section 1 or 2 (a ``DriverConfigError``, so the
    driver passes it through unchanged)."""


def _aws_virtual_host(bucket: str, region: str) -> str:
    """The only place that builds an Amazon S3 host (driver ``s3``; D2306-78)."""
    return f"{bucket}.s3.{region}.amazonaws.com"


def _validate_bucket(raw: Any) -> str:
    if not isinstance(raw, str) or not _BUCKET_RE.fullmatch(raw):
        raise S3ConfigError("bucket is invalid")
    if ".." in raw or ".-" in raw or "-." in raw or _IPV4_SHAPE_RE.fullmatch(raw):
        raise S3ConfigError("bucket is invalid")
    return raw


def _validate_region(raw: Any, *, aws: bool) -> str:
    if not isinstance(raw, str):
        raise S3ConfigError("region is invalid")
    if aws:
        if not _AWS_REGION_RE.fullmatch(raw) or raw.startswith("cn-"):
            raise S3ConfigError("region is invalid for driver s3")
    elif not _GENERIC_REGION_RE.fullmatch(raw):
        raise S3ConfigError("region is invalid")
    return raw


def _parse_endpoint(raw: Any) -> tuple[str, int | None]:
    """(lower-case host, explicit port or None) of an ``https`` endpoint without extras."""
    message = "endpoint_url must be https://host[:port] without userinfo, path, query or fragment"
    if not isinstance(raw, str) or "?" in raw or "#" in raw:
        raise S3ConfigError(message)
    parts = urlsplit(raw)
    if parts.scheme != "https" or not parts.netloc or "@" in parts.netloc:
        raise S3ConfigError(message)
    if parts.path not in ("", "/") or parts.query or parts.fragment:
        raise S3ConfigError(message)
    try:
        port = parts.port
    except ValueError:
        raise S3ConfigError(message) from None
    host = (parts.hostname or "").lower()
    if not host or (port is not None and not 1 <= port <= 65535):
        raise S3ConfigError(message)
    return host, port


def _host_header(host: str, port: int | None) -> str:
    shown = f"[{host}]" if ":" in host else host
    if port is None or port in (80, 443):
        return shown
    return f"{shown}:{port}"


def resolve_location(cfg: dict[str, Any]) -> S3Location:
    if not isinstance(cfg, dict):
        raise S3ConfigError("target config is invalid")
    driver = cfg.get("driver")
    if driver not in _DRIVERS:
        raise S3ConfigError("driver must be one of: s3, s3_compatible")
    for key in _MISNAMED_DESTINATION_KEYS:
        if key in cfg:
            raise S3ConfigError(
                f"{key} is not accepted by driver {driver}; use endpoint_url"
            )

    if driver == "s3":
        if "endpoint_url" in cfg:
            raise S3ConfigError(
                "endpoint_url is not accepted by driver s3; use driver s3_compatible"
            )
        if "addressing_style" in cfg:
            raise S3ConfigError("addressing_style is not accepted by driver s3")
        bucket = _validate_bucket(cfg.get("bucket"))
        if "." in bucket:
            raise S3ConfigError("bucket names with dots are not supported by driver s3")
        region = _validate_region(cfg.get("region"), aws=True)
        host = _aws_virtual_host(bucket, region)
        return S3Location(host, None, host, "", "virtual", region)

    if cfg.get("endpoint_url") is None:
        raise S3ConfigError("endpoint_url is required by driver s3_compatible")
    endpoint_host, raw_port = _parse_endpoint(cfg.get("endpoint_url"))
    style = cfg.get("addressing_style", "path")
    if style not in ("path", "virtual"):
        raise S3ConfigError("addressing_style must be path or virtual")
    bucket = _validate_bucket(cfg.get("bucket"))
    region = _validate_region(cfg.get("region"), aws=False)
    port = None if raw_port in (None, 443) else raw_port
    if style == "virtual":
        if "." in bucket:
            raise S3ConfigError(
                "bucket names with dots are not supported with addressing_style virtual"
            )
        host = f"{bucket}.{endpoint_host}"
        return S3Location(host, port, _host_header(host, port), "", "virtual", region)
    return S3Location(
        endpoint_host,
        port,
        _host_header(endpoint_host, port),
        f"/{bucket}",
        "path",
        region,
    )


def object_storage_host(cfg: dict[str, Any]) -> str:
    """The connected host for the loader; ``""`` when the config is invalid (never raises)."""
    try:
        return resolve_location(cfg).host
    except S3ConfigError:
        return ""


def validate_prefix(raw: Any) -> str:
    if not isinstance(raw, str):
        raise S3ConfigError("prefix must be a string")
    try:
        size = len(raw.encode("utf-8", errors="strict"))
    except UnicodeEncodeError:
        raise S3ConfigError("prefix is not valid text") from None
    if size > _MAX_PREFIX_BYTES:
        raise S3ConfigError("prefix is longer than 1024 bytes")
    if raw.startswith("/"):
        raise S3ConfigError("prefix must not start with /")
    if any(ord(ch) < 0x20 or ord(ch) == 0x7F for ch in raw):
        raise S3ConfigError("prefix must not contain control characters")
    if any(segment in (".", "..") for segment in raw.split("/")):
        raise S3ConfigError("prefix must not contain a . or .. segment")
    return raw
