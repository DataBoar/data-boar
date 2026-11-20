"""Driver ``s3`` of the ``object_storage`` reader: Amazon S3 and compatibles (#2306, 2306.1).

Source: ``docs/desenho/2306.md``, sections 0, 2, 2a, 5, 7 and 11. One implementation, two
registered names (revision 4, DEC-15): ``s3`` (Amazon S3) and ``s3_compatible``. It joins ``s3_addressing``
(host and base path), ``s3_sigv4`` (request signing), the reading of the ``ListObjectsV2``
response (``defusedxml``) and the S3 error table. It holds no credential beyond one call.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Literal

from connectors.object_storage_driver import (
    DriverSettings,
    ErrorClass,
    ListPage,
    PreparedGet,
    ResolvedCredentials,
)
from connectors.s3_addressing import S3Location


@dataclass(frozen=True)
class S3Settings(DriverSettings):
    bucket: str
    region: str
    endpoint_url: str | None
    location: S3Location


S3Variant = Literal["s3", "s3_compatible"]


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

    def settings(self, cfg: dict[str, Any]) -> S3Settings:
        raise NotImplementedError("2306.1: S3Driver.settings")

    def destination(self, settings: DriverSettings) -> str:
        raise NotImplementedError("2306.1: S3Driver.destination")

    def destination_host(self, cfg: dict[str, Any]) -> str:
        raise NotImplementedError("2306.1: S3Driver.destination_host")

    def list_request(
        self,
        settings: DriverSettings,
        creds: ResolvedCredentials,
        prefix: str,
        token: str | None,
        page_size: int,
        now: datetime,
    ) -> PreparedGet:
        raise NotImplementedError("2306.1: S3Driver.list_request")

    def parse_list(self, body: bytes) -> ListPage:
        raise NotImplementedError("2306.1: S3Driver.parse_list")

    def get_request(
        self,
        settings: DriverSettings,
        creds: ResolvedCredentials,
        key: str,
        now: datetime,
    ) -> PreparedGet:
        raise NotImplementedError("2306.1: S3Driver.get_request")

    def classify_error(
        self,
        status: int,
        headers: Mapping[str, str],
        body: bytes,
        *,
        during: Literal["list", "get"],
    ) -> ErrorClass:
        raise NotImplementedError("2306.1: S3Driver.classify_error")

    def display_path(self, settings: DriverSettings, key: str) -> str:
        raise NotImplementedError("2306.1: S3Driver.display_path")

    def inventory_identity(self, settings: DriverSettings) -> dict[str, str]:
        raise NotImplementedError("2306.1: S3Driver.inventory_identity")
