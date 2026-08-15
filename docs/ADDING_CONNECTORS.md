# Adding a New Connector

This guide explains how to add a new data-source connector to **Data Boar** so that targets of a new type (e.g. Snowflake, a custom API, or another database) can be scanned from `config.yaml` and reported in the same Excel/heatmap flow.

**Português (Brasil):** [ADDING_CONNECTORS.pt_BR.md](ADDING_CONNECTORS.pt_BR.md)

---

## 1. How connectors fit in

- **Config:** Each entry in `targets` has at least `name`, `type`, and type-specific fields (e.g. `host`, `database`, `base_url`).
- **Registry:** Connectors register a **type** (and optionally a **driver** for `type: database`) in `core.connector_registry`.
- **Resolution:** For each target, `connector_for_target(target)` returns the connector class to use. For `type: database`, the **driver** (e.g. `postgresql+psycopg2`) is normalized to an engine name (e.g. `postgresql`) and looked up in the registry.
- **Engine:** `AuditEngine._run_target()` instantiates the connector with `(target_config, scanner, db_manager)` (plus optional kwargs for filesystem/shares), then calls `connector.run()`.

So a connector must:

1. Implement a class with **`run(self)`** that performs the scan.
1. Use **`self.scanner`** (e.g. `scan_column(column_name, sample_text)`) for sensitivity detection.
1. Report results via **`self.db_manager.save_finding(...)`** and failures via **`self.db_manager.save_failure(...)`**.
1. Optionally implement **`connect()`** and **`close()`** for connection lifecycle; **`run()`** should call them (e.g. connect at start, close in a `finally` block).

---

## 2. Connector contract (summary)

| Requirement                 | Description                                                                                                                                                                                                                             |
| ---                         | ---                                                                                                                                                                                                                                     |
| **Constructor**             | `__init__(self, target_config, scanner, db_manager, **kwargs)`. For database/API connectors the engine only passes these three; for filesystem and share connectors it may also pass `extensions`, `scan_sqlite_as_db`, `sample_limit`. |
| **`run()`**                 | Entry point. Connect, discover/sample, call `scanner.scan_column(name, sample)`, then `db_manager.save_finding(...)` or `save_failure(...)`. Close resources when done.                                                                 |
| **`connect()` / `close()`** | Optional but recommended. Use in `run()` so connections are released.                                                                                                                                                                   |
| **Findings**                | Use `save_finding(source_type="database", ...)` for DB-like sources (schema, table, column) or `save_finding(source_type="filesystem", ...)` for file/API-like (path, file_name).                                                       |
| **Failures**                | Use `save_failure(target_name, reason, details)` on unreachable targets or errors.                                                                                                                                                      |

---

## 3. Step-by-step

### Step 1: Create the connector module

Add a new file under `connectors/`, e.g. `connectors/snowflake_connector.py`.

- Implement a class (e.g. `SnowflakeConnector`) with:
- `__init__(self, target_config, scanner, db_manager, sample_limit=5)` (match the engine’s constructor call for database-like connectors).
- `connect()` – create client/engine from `target_config`.
- `close()` – dispose engine/close client.
- `run()` – call `connect()`, then discover/sample, run `scanner.scan_column(...)`, call `db_manager.save_finding(...)` or `save_failure(...)`, and in a `finally` block call `close()`.

### Step 2: Register the connector

At the bottom of your module (or behind an optional-import guard), call:

```python
from core.connector_registry import register

register("snowflake", SnowflakeConnector, ["name", "type"])
```

The third argument is the list of config keys that must be present (e.g. for validation or docs). The engine does not enforce it; it only uses it for documentation.

- For a **database** driver: register the engine name (e.g. `snowflake`) so that targets with `type: database` and `driver: snowflake+connector` resolve to your class (see “Mapping target type to connector” below).
- For a **non-database** target (e.g. API, share): register the type string that will appear in `target.type` (e.g. `api`, `rest`, `sharepoint`).

### Step 3: Map target type to connector (if needed)

- **`type: database`:** Resolution is in `connector_for_target()` in `core/connector_registry.py`. The driver is normalized to an engine name (e.g. `snowflake+connector` → `snowflake`). If you registered `"snowflake"`, no change is needed; the existing logic will pick it up.
- **New top-level type (e.g. `type: snowflake`):** Add a branch in `connector_for_target()`:

  ```python
  if t == "snowflake":
      try:
          return get_connector("snowflake")
      except KeyError:
          return None
  ```

  Then in config you use `type: snowflake` (and optionally still support `type: database` + `driver: snowflake...` by registering `snowflake` as above).

### Step 4: Optional dependency (recommended for heavy or rare backends)

If the connector needs a library that is not in the default dependencies (e.g. `snowflake-connector-python`), add an optional extra in `pyproject.toml`:

```toml
[project.optional-dependencies]
bigdata = ["snowflake-connector-python>=3.0"]
```

Users install with:

```bash
uv pip install -e ".[bigdata]"
```

In the connector module, guard the import and registration so the app does not fail when the dependency is missing:

```python
try:
    import snowflake.connector
    _SNOWFLAKE_AVAILABLE = True
except ImportError:
    _SNOWFLAKE_AVAILABLE = False

class SnowflakeConnector:
    # ...

if _SNOWFLAKE_AVAILABLE:
    register("snowflake", SnowflakeConnector, ["name", "type"])
```

### Step 5: Register the module in the engine

So that the connector is loaded and registers itself, import it in `core/engine.py`:

```python
try:
    import connectors.snowflake_connector  # noqa: F401
except ImportError:
    pass
```

Use a try/except if the connector is optional (optional dependency); otherwise a plain import is enough.

### Step 6: Document config shape and example

In the README (or this doc), add:

- Which **packages** to install (e.g. `.[bigdata]` or `pip install snowflake-connector-python`).
- The **target shape** in YAML: `type`, `name`, and required/optional keys (e.g. `account`, `user`, `password`, `database`, `schema`, `warehouse`).
- A minimal **example** snippet.

---

## 4. Database vs filesystem/API findings

- **Database-like sources** (tables and columns): use `save_finding(source_type="database", ...)` and pass at least:
- `target_name`, `server_ip` (or host), `schema_name`, `table_name`, `column_name`, `data_type`
- `sensitivity_level`, `pattern_detected`, `norm_tag`, `ml_confidence`
- Other DB fields are optional but useful for reports.

- **File/API-like sources** (paths, endpoints, keys): use `save_finding(source_type="filesystem", ...)` and pass:
- `target_name`, `path`, `file_name` (e.g. endpoint + field), `data_type`
- `sensitivity_level`, `pattern_detected`, `norm_tag`, `ml_confidence`

The scanner returns a dict with at least `sensitivity_level`, `pattern_detected`, `norm_tag`, `ml_confidence`; pass those through to `save_finding`. Skip or do not report rows where `sensitivity_level == "LOW"` if you want to match existing behavior.

---

## 5. Example: Snowflake connector (database-style)

Below is a minimal pattern for a Snowflake connector that reuses the same “discover → sample → scan_column → save_finding” flow as the SQL connector. You can adapt it to your driver and config keys.

```python
# connectors/snowflake_connector.py
"""Snowflake connector: optional, requires snowflake-connector-python. Use type: database, driver: snowflake."""
from typing import Any

from core.connector_registry import register

try:
    import snowflake.connector
    from sqlalchemy import create_engine
    _SNOWFLAKE_AVAILABLE = True
except ImportError:
    _SNOWFLAKE_AVAILABLE = False
    snowflake = None

def _build_url(target: dict[str, Any]) -> str:
    account = target.get("account", "")
    user = target.get("user", "")
    password = target.get("pass", target.get("password", ""))
    database = target.get("database", "")
    schema = target.get("schema", "PUBLIC")
    warehouse = target.get("warehouse", "")
    # Build SQLAlchemy-style URL or use connector params; here simplified.
    return f"snowflake://{user}:{password}@{account}/{database}/{schema}?warehouse={warehouse}"

class SnowflakeConnector:
    def __init__(self, target_config: dict[str, Any], scanner: Any, db_manager: Any, sample_limit: int = 5):
        self.config = target_config
        self.scanner = scanner
        self.db_manager = db_manager
        self.sample_limit = sample_limit
        self.engine = None
        self._connection = None

    def connect(self) -> None:
        if not _SNOWFLAKE_AVAILABLE:
            raise RuntimeError("snowflake-connector-python required. Install with: pip install snowflake-connector-python")
        url = _build_url(self.config)
        self.engine = create_engine(url)
        self._connection = self.engine.connect()

    def close(self) -> None:
        if self._connection:
            try:
                self._connection.close()
            except Exception:
                pass
            self._connection = None
        if self.engine:
            self.engine.dispose()
            self.engine = None

    def discover(self) -> list[dict[str, Any]]:
        """Return list of {schema, table, columns: [{name, type}]}."""
        from sqlalchemy import inspect
        inspector = inspect(self.engine)
        result = []
        for schema in inspector.get_schema_names():
            for table in inspector.get_table_names(schema=schema):
                columns = inspector.get_columns(table, schema=schema)
                result.append({
                    "schema": schema or "",
                    "table": table,
                    "columns": [{"name": c["name"], "type": str(c["type"])} for c in columns],
                })
        return result

    def sample(self, schema: str, table: str, column_name: str) -> str:
        """Return sample values for the column as a single string (not stored)."""
        from sqlalchemy import text
        quoted = f'"{schema}"."{table}"."{column_name}"' if schema else f'"{table}"."{column_name}"'
        q = text(f"SELECT {quoted} FROM {quoted.rpartition('.')[0]} LIMIT {self.sample_limit}")
        try:
            rows = self._connection.execute(q).fetchall()
            return " ".join(str(r[0])[:200] for r in rows if r[0] is not None)
        except Exception:
            return ""

    def run(self) -> None:
        target_name = self.config.get("name", "snowflake")
        try:
            self.connect()
        except Exception as e:
            self.db_manager.save_failure(target_name, "unreachable", str(e))
            return
        try:
            for item in self.discover():
                schema = item["schema"]
                table = item["table"]
                for col in item["columns"]:
                    cname = col["name"]
                    ctype = col["type"]
                    sample = self.sample(schema, table, cname)
                    res = self.scanner.scan_column(cname, sample)
                    if res["sensitivity_level"] == "LOW":
                        continue
                    self.db_manager.save_finding(
                        source_type="database",
                        target_name=target_name,
                        server_ip=self.config.get("account", ""),
                        engine_details="snowflake",
                        schema_name=schema,
                        table_name=table,
                        column_name=cname,
                        data_type=ctype,
                        sensitivity_level=res["sensitivity_level"],
                        pattern_detected=res["pattern_detected"],
                        norm_tag=res.get("norm_tag", ""),
                        ml_confidence=res.get("ml_confidence", 0),
                    )
        except Exception as e:
            self.db_manager.save_failure(target_name, "error", str(e))
        finally:
            self.close()

if _SNOWFLAKE_AVAILABLE:
    register("snowflake", SnowflakeConnector, ["name", "type", "account", "user", "database"])
```

## Config example (`config.yaml`)

```yaml
targets:

- name: "Warehouse_LGPD"

    type: database
    driver: snowflake
    account: "xy12345.us-east-1"
    user: "AUDIT_USER"
    pass: "secret"
    database: "COMPLIANCE_DB"
    schema: "PUBLIC"
    warehouse: "AUDIT_WH"
```

Install optional dependency:

```bash
uv pip install -e ".[bigdata]"
```

Then add in `core/connector_registry.py` a fallback for `type: database` so that `driver: snowflake` (or `snowflake+connector`) maps to the `snowflake` registry key (the existing loop over aliases does not include `snowflake`; you can add `"snowflake"` to the alias list or handle it in the same way as `postgresql`/`mysql`). And in `core/engine.py`:

```python
try:
    import connectors.snowflake_connector  # noqa: F401
except ImportError:
    pass
```

---

## 6. Example: REST/API connector (filesystem-style)

For an API that returns JSON, you use **filesystem** findings and a single `run()` that fetches endpoints, flattens JSON, and runs `scan_column` on field names and sample values. See `connectors/rest_connector.py` for the full pattern:

- **Constructor:** `(target_config, scanner, db_manager, sample_limit=5)`.
- **Auth:** Read `target_config["auth"]` (basic, bearer, oauth2_client, custom) and set headers or client auth.
- **Discovery:** Either fixed `paths` in config or a `discover_url` that returns a list of paths.
- **Per path:** GET, parse JSON, flatten to `(key, value)` pairs, call `scanner.scan_column(key, value)`; if not LOW, call `db_manager.save_finding("filesystem", target_name=..., path=..., file_name=f"GET {path} | {key}", ...)`.
- **Failures:** `save_failure(target_name, "error", message)` on connection or parse errors.
- **Optional dependency:** Guard with `try/import httpx` and only register when `httpx` is available.

Config example:

```yaml
targets:

- name: "Internal API"

    type: api
    base_url: "https://api.example.com"
    auth:
      type: bearer
      token_from_env: "API_TOKEN"
    paths:

      - "/users"
      - "/orders"

```

---

## 7. Example: HubSpot CRM connector (#1229)

Managed SaaS CRM (Pro tier). Discovers **all** property names (including custom fields
where CPF/CNPJ often hide), then samples objects with pagination and rate-limit backoff.

- **Module:** `connectors/hubspot_connector.py`
- **Auth:** Private App Token via env ``HUBSPOT_PRIVATE_APP_TOKEN`` (never commit tokens).
  Read-only scopes: `crm.objects.*.read` + `crm.schemas.*.read` for contacts/companies/deals.
- **SSRF:** All outbound HTTP uses `connectors/url_guard.py` host pinning (#1552) — same
  posture as the REST connector.

Config example:

```yaml
targets:
  - name: crm-hubspot
    type: hubspot
    objects: [contacts, companies, deals]
```

Optional keys: `base_url` (default `https://api.hubapi.com`), `token_from_env`
(override env var name), `allow_private_networks` (lab only).

---

## 8. Checklist

- [ ] New module under `connectors/<name>_connector.py`.
- [ ] Class with `run()`, and optionally `connect()`/`close()`.
- [ ] Uses `self.scanner.scan_column(name, sample)` and `self.db_manager.save_finding(...)` / `save_failure(...)`.
- [ ] `register(<type>, <Class>, [required_config_keys])` (and driver mapping in `connector_for_target` if new type or driver).
- [ ] Optional dep in `pyproject.toml` and import guard + conditional register.
- [ ] Import in `core/engine.py` (with try/except if optional).
- [ ] README or this doc: install command, target config shape, example YAML.

Once these are in place, the new connector is used automatically for matching targets and appears in the same Excel and heatmap reports as existing connectors.

**See also:** Documentation index (all topics, both languages): [README.md](README.md) · [README.pt_BR.md](README.pt_BR.md). [TOPOLOGY.md](TOPOLOGY.md) ([pt-BR](TOPOLOGY.pt_BR.md)) — application topology; [TECH_GUIDE.md](TECH_GUIDE.md) · [TECH_GUIDE.pt_BR.md](TECH_GUIDE.pt_BR.md); [TESTING.md](TESTING.md) ([pt-BR](TESTING.pt_BR.md)); [COMMIT_AND_PR.md](ops/COMMIT_AND_PR.md) ([pt-BR](ops/COMMIT_AND_PR.pt_BR.md)); [COMPLIANCE_FRAMEWORKS.md](COMPLIANCE_FRAMEWORKS.md) ([pt-BR](COMPLIANCE_FRAMEWORKS.pt_BR.md)).
