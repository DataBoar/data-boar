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

from dataclasses import dataclass
from typing import Any, Literal


@dataclass(frozen=True)
class S3Location:
    host: str  # lower-case hostname, no port
    port: int | None  # None when absent or 443
    host_header: str  # host, or "host:port" when the port is neither 80 nor 443
    base_path: str  # "" (virtual-hosted style) or "/<bucket>" (path style)
    addressing: Literal["virtual", "path"]
    region: str


class S3ConfigError(ValueError):
    """``str(exc)`` is a fixed message of section 1 or 2."""


def _aws_virtual_host(bucket: str, region: str) -> str:
    """The only place that builds an Amazon S3 host (driver ``s3``; D2306-78)."""
    raise NotImplementedError("2306.1: _aws_virtual_host")


def resolve_location(cfg: dict[str, Any]) -> S3Location:
    raise NotImplementedError("2306.1: resolve_location")


def object_storage_host(cfg: dict[str, Any]) -> str:
    """The connected host for the loader; ``""`` when the config is invalid (never raises)."""
    raise NotImplementedError("2306.1: object_storage_host")


def validate_prefix(raw: Any) -> str:
    raise NotImplementedError("2306.1: validate_prefix")
