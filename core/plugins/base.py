"""Enterprise remediation plugin protocol (#606 / ADR-0059)."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol, runtime_checkable


class PluginError(Exception):
    """Raised when a remediation plugin fails to load or is non-conformant."""


@runtime_checkable
class RemediationPlugin(Protocol):
    """Enterprise tier: post-scan remediation plugin interface."""

    def remediate(
        self,
        findings_path: Path,
        config: dict,
    ) -> Path:
        """
        Receives findings JSONL path (host-written from SQLite when the hook
        runs with db_manager — #1443), returns remediation_report.json path.
        Must not modify findings_path in place.
        """
        ...

    @property
    def name(self) -> str:
        """Plugin identifier for Audit Trail."""
        ...

    @property
    def version(self) -> str: ...
