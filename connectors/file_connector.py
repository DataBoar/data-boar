"""
Backward-compatible alias: FileScanner and scan_directory delegate to FilesystemConnector.
Prefer using connectors.filesystem_connector.FilesystemConnector and the connector registry.
"""

from connectors.filesystem_connector import FilesystemConnector


class FileScanner:
    """Thin wrapper around FilesystemConnector for backward compatibility."""

    def __init__(self, scanner_engine, db_session):
        self._scanner = scanner_engine
        self._db = db_session
        self._connector = None

    def scan_directory(self, root_path, recursive=True):
        """Run filesystem scan; requires target config with name and path. Use AuditEngine for full flow."""
        # Caller may pass db_session=None; we need a target dict and db_manager from engine
        from core.database import LocalDBManager

        if self._db is None:
            return
        target = {"name": "filesystem", "path": root_path, "recursive": recursive}
        if hasattr(self._db, "save_finding"):
            connector = FilesystemConnector(target, self._scanner, self._db)
            connector.run()
        else:
            # Legacy: db_session might be something else
            connector = FilesystemConnector(target, self._scanner, LocalDBManager())
            connector.run()
