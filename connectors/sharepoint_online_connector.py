"""
Microsoft Graph reader, type ``sharepoint_online``, delegated mode (device code).

Contract: docs/desenho/2206.1.md. Skeleton only (task 2206.1, TDD red step).
"""

from __future__ import annotations

import tempfile  # noqa: F401 - used by the implementation
import time
from typing import Any, Literal, NamedTuple

from connectors.filesystem_connector import (  # noqa: F401 - used by the implementation
    _read_text_sample,
    _scan_sqlite_file_as_db,
    scan_archive_at_path,
)

_interactive_enabled = False


def install_download_log_filter() -> None:
    raise NotImplementedError("2206.1: install_download_log_filter")


class SharePointOnlineError(Exception):
    """A failure that ends the target (or one item); ``detail`` is a fixed message."""

    def __init__(self, reason: str, detail: str) -> None:
        super().__init__(detail)
        self.reason = reason
        self.detail = detail


class ScopeEntry(NamedTuple):
    display_path: str
    size: int
    kind: Literal["file", "folder"]
    skipped_reason: str | None


def enable_interactive_sign_in() -> None:
    raise NotImplementedError("2206.1: enable_interactive_sign_in")


class SharePointOnlineConnector:
    def __init__(
        self,
        target_config: dict[str, Any],
        scanner: Any,
        db_manager: Any,
        extensions: set[str] | list[str] | None = None,
        scan_sqlite_as_db: bool = True,
        sample_limit: int = 5,
        file_sample_max_chars: int = 12_000,
        file_passwords: dict[str, str] | None = None,
        *,
        _transport: Any = None,
        _sleep: Any = time.sleep,
        _monotonic: Any = time.monotonic,
        _prompt_stream: Any = None,
        _interactive: bool | None = None,
    ) -> None:
        self._name = str(target_config.get("name") or "sharepoint_online")

    def __repr__(self) -> str:
        return f"SharePointOnlineConnector(name={self._name!r})"

    def run(self) -> None:
        raise NotImplementedError("2206.1: run")

    def list_scope(self) -> list[ScopeEntry]:
        raise NotImplementedError("2206.1: list_scope")
