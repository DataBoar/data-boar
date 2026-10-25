"""
NFS connector: scan an NFS share that is already mounted on the audit server.
Config: host (FQDN or IP), export_path (for reporting), path (local mount point).
No NFS client library required; the path must be a local directory (mount point).
Uses the same file scan logic as the filesystem connector.
"""

from pathlib import Path
from typing import Any

from core.connector_registry import register

from connectors.filesystem_connector import FilesystemConnector


class NFSConnector:
    """
    Scan a path that is expected to be an NFS mount point. Requires the operator to mount
    the NFS share locally (e.g. mount -t nfs server:/export /mnt/nfs) and set path to that directory.
    Findings are tagged with target name and host/export_path for DPO reporting.

    **Sampling (#1337):** no NFS-specific sampling code. ``sample_limit`` is passed to
    :class:`~connectors.filesystem_connector.FilesystemConnector` in ``__init__``; ``run()``
    delegates to ``self._fs.run()`` (SQLite-as-DB and file paths use the same dedup-before-cap
    path as local filesystem scans).
    """

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
    ):
        self.config = dict(target_config)
        self.scanner = scanner
        self.db_manager = db_manager
        self._fs = FilesystemConnector(
            self.config,
            scanner,
            db_manager,
            extensions=extensions,
            scan_sqlite_as_db=scan_sqlite_as_db,
            sample_limit=sample_limit,
            file_sample_max_chars=file_sample_max_chars,
            file_passwords=file_passwords,
        )

    def run(self) -> None:
        target_name = self.config.get("name", "NFS")
        path = self.config.get("path", "").strip()
        host = self.config.get("host", self.config.get("server", ""))
        export_path = self.config.get("export_path", "")
        if not path:
            self.db_manager.save_failure(
                target_name,
                "error",
                "Missing path (local NFS mount point). Mount the share first, e.g. mount -t nfs host:/export /mnt/nfs",
            )
            return
        if not Path(path).exists():
            self.db_manager.save_failure(
                target_name,
                "unreachable",
                f"Path does not exist: {path}. Ensure NFS is mounted (e.g. mount -t nfs {host or 'server'}:{export_path or 'export'} {path}).",
            )
            return
        if not Path(path).is_dir():
            self.db_manager.save_failure(
                target_name, "error", "path is not a directory"
            )
            return
        self._fs.run()


register("nfs", NFSConnector, ["name", "path"])
