# Plan: SQL connector extras + lean core install (#1047)

<!-- plans-hub-summary: SQL extras + lean core (#1047); container delivery via runtime /extras+PYTHONPATH mount, EXTRAS_MANIFEST + --check-extras (#1400/#1401/#1399/#1402) — not fat image. -->

**Status:** In progress
**Date:** 2026-06-27
**Authors:** Fabio Leitao (operator); Cursor executor
**Priority:** H1 (packaging / wide-install ICP)
**GitHub:** [#1047](https://github.com/DataBoar/data-boar/issues/1047) `[P2][packaging]` · **Related:** [#1059](https://github.com/DataBoar/data-boar/issues/1059) (`[noavx]` / capability profiles; see [#929](https://github.com/DataBoar/data-boar/issues/929)) · **Container slice:** [#1400](https://github.com/DataBoar/data-boar/issues/1400) · [#1401](https://github.com/DataBoar/data-boar/issues/1401) · [#1399](https://github.com/DataBoar/data-boar/issues/1399) · [#1402](https://github.com/DataBoar/data-boar/issues/1402) · **CI extras job (does not change extra names):** [#1638](https://github.com/DataBoar/data-boar/issues/1638) [PLAN_CI_OPTIONAL_EXTRAS_COVERAGE.md](PLAN_CI_OPTIONAL_EXTRAS_COVERAGE.md)
**Related:** [ADR-0031](../adr/ADR-0031-pypi-packaging-hatchling-flat-layout.md) · [ADR-0073](../adr/ADR-0073-version-scheme-octet-maturity-and-roadmap.md) · [#1042](https://github.com/DataBoar/data-boar/issues/1042) (PyPI publish) · [CONTRIBUTING.md](../../CONTRIBUTING.md)

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
| `mssql` | `pymssql` | `mssql` / `mssql+pymssql` (default bare driver) |
| `mssql-pymssql` | `pymssql` | alias of `mssql` (#1588) |
| `mssql-pyodbc` | `pyodbc` | `mssql+pyodbc` only |
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

## Out of scope (#1047 library slice only)

- ML/plot stack (`numpy`/`pandas`/…) as extras — issue #1047 secondary note; track separately.
- PyPI publish run itself — operator **release-ritual** after merge.

---

## Container as delivery artifact (in scope — #1400 / #1401 / #1399 / #1402)

**Operator decision (1.8.x):** keep the **distroless base lean**; extend connectors at **runtime** by mounting prebuilt ABI-compatible wheels at **`/extras`** with **`PYTHONPATH=/extras:/app`** (`/extras` first). **No** fat image of all 18 extras, **no** image matrix, **no** requiring customers to `Dockerfile FROM` our image and rebuild.

| Step | Scope | Status |
| ---- | ----- | ------ |
| **C0** | `/extras` + `PYTHONPATH` + `VOLUME` + `DATA_BOAR_MACHINE_SEED=` on `Dockerfile` / `Dockerfile.nogil`; nonroot 65532 | ✅ |
| **C1** | Base image installs only `sql-community,mssql,oracle` from pyproject (not hand-written package list; not all 18) | ✅ |
| **C2** | `EXTRAS_MANIFEST.json` generated from `[project.optional-dependencies]` + import probe; `--check-extras`; smoke fails on `in_artifact` drift | ✅ |
| **C3** | ABI fail-closed when mounted pack mismatches interpreter; missing-connector messages name extra + `/extras` path (#1402) | ✅ |
| **C4** | Docs EN+pt-BR (`DOCKER_SETUP`, `USAGE`); this plan; `PLANS_TODO`; `plans_hub_sync` | ✅ |

**Still out of this container slice:** publishing a signed, versioned extras-pack artifact per ABI (follow-on to #1400).

---

## Pending

| Item | Notes |
| ---- | ----- |
| Post-merge PyPI upload | `1.7.4.post1` via `publish-pypi.yml` (library slice) |
| Operator smoke | `pipx install data-boar==1.7.4.post1` on constrained py3.14 lab host |
| Container smoke | `docker-image-smoke.sh` after lab build; mount `/extras` pack without `--user 0` |
