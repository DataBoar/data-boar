# Deprecated – use core engine and connectors

This folder contains legacy scanner/factory code that referenced `src.scanners`. The active implementation is:

- **Scan flow:** `main.py` → `config.loader` → `core.engine.AuditEngine` → `core.connector_registry` → `connectors/sql_connector.py`, `connectors/filesystem_connector.py`, etc.
- **Detection:** `core.scanner.DataScanner` and `core.detector.SensitivityDetector`
- **Reports:** `report.generator.generate_report` with `core.database.LocalDBManager`

Do not use `scanner_factory` or `db_scanner` for new code. Prefer the unified flow above.
