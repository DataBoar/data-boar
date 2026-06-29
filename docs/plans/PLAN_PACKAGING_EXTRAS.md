# Plan: SQL connector extras + lean core install (#1047)

<!-- plans-hub-summary: Move SQL C-extension drivers out of core dependencies into PEP 508 extras; lazy-import with clear install hints; PyPI republish via 1.7.4.postN + maturity_build side-channel per ADR-0073 PyPI clause. -->

**Status:** In progress
**Date:** 2026-06-27
**Authors:** Fabio Leitao (operator); Cursor executor
**Priority:** H1 (packaging / wide-install ICP)
**GitHub:** [#1047](https://github.com/FabioLeitao/data-boar/issues/1047) `[P2][packaging]` · **Related:** [#1059](https://github.com/FabioLeitao/data-boar/issues/1059) (`[noavx]` / capability profiles; see [#929](https://github.com/FabioLeitao/data-boar/issues/929))
**Related:** [ADR-0031](../adr/ADR-0031-pypi-packaging-hatchling-flat-layout.md) · [ADR-0073](../adr/ADR-0073-version-scheme-octet-maturity-and-roadmap.md) · [#1042](https://github.com/FabioLeitao/data-boar/issues/1042) (PyPI publish) · [CONTRIBUTING.md](../../CONTRIBUTING.md)

**Synced with:** [PLANS_TODO.md](PLANS_TODO.md)

---

## Problem

`pip install data-boar` / `pipx install data-boar` pulls **all** SQL drivers as **core** dependencies (`mariadb`, `mysqlclient`, `psycopg2-binary`, `pyodbc`, `oracledb`, `pymysql`, plus suspicious `mysql>=0.0.3` placeholder). On platforms without wheels (e.g. **Python 3.14** on Void Linux), **C-extensions** compile and fail unless a full toolchain + dev headers are present — blocking installs for operators who only scan **files** or **SQLite**.

Evidence: multi-node smoke 2026-06-27 (py3.12 lab host OK; constrained py3.14 lab host failed on `mariadb` source build). Issue body + private uv log.

---

## Decision

### Extras (per engine)

| Extra | PyPI packages | Typical `driver` / dialect |
| ----- | ------------- | --------------------------- |
| `postgres` | `psycopg2-binary` | `postgresql` / `postgresql+psycopg2` |
| `mysql` | `pymysql` (pure Python) | `mysql` / `mysql+pymysql` |
| `mariadb` | `mariadb` (Connector/C) | `mariadb` / `mariadb+mariadbconnector` |
| `mssql` | `pyodbc` | `mssql` / `mssql+pyodbc` |
| `oracle` | `oracledb` | `oracle` / `oracle+oracledb` |
| `sql-all` | union of the above | convenience meta-extra (Docker / lab images) |

**Core** keeps `sqlalchemy` + **SQLite** (stdlib). **Remove** from core: `mariadb`, `mysqlclient`, `mysql` (placeholder), `psycopg2-binary`, `pymysql`, `pyodbc`, `oracledb`.

### Lazy-import contract

- `connectors/sql_connector.py` always **registers** SQL engine types (YAML resolves).
- `connect()` calls `ensure_sql_driver_available(driver)` → clear `ImportError` with `pip install 'data-boar[<extra>]'` when the driver module is missing.
- `core/engine.py` imports `SQLConnector` only for typing/sampling bases (no driver install at import).

### Version / PyPI tension (ADR-0073 amendment)

PyPI is **immutable per version**; there is **no** `maturity_build` side-channel on the index.

| Option | Verdict |
| ------ | ------- |
| **`1.7.4.post1`** in `[project] version` | **Chosen** — PEP 440 post-release for packaging fix on the **same public line** (`1.7.4`); **not** `1.7.5`; **not** a fourth semver segment (`1.7.4.202`). |
| Defer to **`1.8.0`** | **Rejected** — `1.8.0` is the **next architecture line**, not a packaging hotfix. |
| Re-upload **`1.7.4`** | **Impossible** on PyPI. |

**Side-channel:** `[tool.databoar] maturity_build` **201 → 202** (packaging-fix maturity). **Never** copy octet into About as a fourth segment.

**Git/Docker tags:** remain on the `1.7.4` **line** until operator **release-ritual** publishes `1.7.4.post1` to PyPI (workflow from #1042).

---

## Execution steps

| Step | Scope | Status |
| ---- | ----- | ------ |
| **0** | Branch `feat/sql-extras-1047`, this plan, ADR-0073 PyPI clause, ADR-0031 extras note | ✅ |
| **1** | `pyproject.toml`: extras, core trim, `version = "1.7.4.post1"`, `maturity_build = 202` | ✅ |
| **2** | `connectors/sql_driver_deps.py`, `sql_connector` guard, `engine.py`, `DRIVER_MAP` mariadb dialect | ✅ |
| **3** | Tests: core must not list SQL C-ext; missing-extra message | ✅ |
| **4** | Docs EN+pt-BR (USAGE, TECH_GUIDE, CONTRIBUTING); `Dockerfile` installs SQL driver mins | ✅ |
| **5** | `uv lock`, `uv export`, `./scripts/check-all.sh`, PR `Closes #1047` | ✅ |

---

## Acceptance criteria (#1047)

- [x] SQL C-extension drivers **not** in `[project].dependencies`
- [x] lazy-import + actionable extra hint on connect
- [x] `mysql>=0.0.3` placeholder **removed**
- [x] `pip install data-boar` (core) succeeds on py3.14 without DB toolchain (CI/dev proof via dependency guard + operator smoke)
- [x] Install docs list SQL extras
- [x] This plan + **ADR-0031** + **ADR-0073** PyPI clause updated
- [x] PyPI expression documented: **`1.7.4.post1`**

---

## Out of scope (this slice)

- ML/plot stack (`numpy`/`pandas`/…) as extras — issue #1047 secondary note; track separately.
- PyPI publish run itself — operator **release-ritual** after merge.

---

## Pending

| Item | Notes |
| ---- | ----- |
| Post-merge PyPI upload | `1.7.4.post1` via `publish-pypi.yml` |
| Operator smoke | `pipx install data-boar==1.7.4.post1` on constrained py3.14 lab host |
