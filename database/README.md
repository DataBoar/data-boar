# Deprecated – use core.database and connectors

This folder contained legacy database connectors and scanner used by an older flow. The active implementation is:

- **Persistence:** `core.database.LocalDBManager` (single SQLite, sessions, database_findings, filesystem_findings, scan_failures)
- **SQL targets:** `connectors.sql_connector` (discover + sample + detect)
- **Entry:** `main.py` → `config.loader` → `core.engine`

Do not use `database/connectors` or `database/scanner` for new code.
