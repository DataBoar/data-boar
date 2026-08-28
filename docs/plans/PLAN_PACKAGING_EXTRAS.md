# Plan: SQL connector extras + lean core install (#1047)

<!-- plans-hub-summary: SQL extras + lean core (#1047); v1.8.0 #1059 [noavx] wheelhouse (#929) + [nlp]/[ocr]/[dl] profiles; CPU detect + loud FN-first degrade -->
<!-- plans-hub-related: PLAN_WHEELHOUSE_DISTRIBUTION.md, PLAN_CI_OPTIONAL_EXTRAS_COVERAGE.md, PLAN_QUICKSTART.md -->

**Português (Brasil):** [PLAN_PACKAGING_EXTRAS.pt_BR.md](PLAN_PACKAGING_EXTRAS.pt_BR.md)

**Status:** In progress (SQL extras on `main`; v1.8.0 survey [#1059](https://github.com/DataBoar/data-boar/issues/1059) enriches this plan — do not archive)
**Date:** 2026-06-27 (v1.8.0 wave: 2026-08-27)
**Authors:** Fabio Leitao (operator); Cursor executor
**Priority:** H1 (packaging / wide-install ICP)
**Milestone:** v1.8.0
**GitHub:** [#1047](https://github.com/DataBoar/data-boar/issues/1047) `[P2][packaging]` · **[#1059](https://github.com/DataBoar/data-boar/issues/1059)** (`[noavx]` / capability profiles; recipe [#929](https://github.com/DataBoar/data-boar/issues/929)) · **Container slice:** [#1400](https://github.com/DataBoar/data-boar/issues/1400) · [#1401](https://github.com/DataBoar/data-boar/issues/1401) · [#1399](https://github.com/DataBoar/data-boar/issues/1399) · [#1402](https://github.com/DataBoar/data-boar/issues/1402) · **CI extras job (does not change extra names):** [#1638](https://github.com/DataBoar/data-boar/issues/1638) [PLAN_CI_OPTIONAL_EXTRAS_COVERAGE.md](PLAN_CI_OPTIONAL_EXTRAS_COVERAGE.md)
**Related:** [ADR-0031](../adr/ADR-0031-pypi-packaging-hatchling-flat-layout.md) · [ADR-0073](../adr/ADR-0073-version-scheme-octet-maturity-and-roadmap.md) · [#1042](https://github.com/DataBoar/data-boar/issues/1042) (PyPI publish) · [CONTRIBUTING.md](../../CONTRIBUTING.md) · [PLAN_WHEELHOUSE_DISTRIBUTION.md](PLAN_WHEELHOUSE_DISTRIBUTION.md)

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

---

## Changelog

- **2026-08-27:** v1.8.0 survey **[#1059](https://github.com/DataBoar/data-boar/issues/1059)** — `[noavx]` = proven [#929](https://github.com/DataBoar/data-boar/issues/929) wheelhouse (system OpenBLAS, no bundled AVX); capability profiles `[nlp]` / `[ocr]` / `[dl]`; installer CPU detect; **loud + FN-first** degrade (never silent).
- **2026-06-27:** Initial plan — SQL extras + lean core (#1047); later container `/extras` mount (#1400–#1402).

---

## v1.8.0 wave — `[noavx]` wheelhouse + capability profiles ([#1059](https://github.com/DataBoar/data-boar/issues/1059))

**Driver:** Landscape survey (private competitive dossier). **Docs-first** in this PR; this wave does **not** add a `pyproject.toml` extra, a new installer binary, or a second wheelhouse recipe.

**Invariant (doctrine):** Capability **degrade is LOUD and FN-first**, never silent. If a reduced profile **detects less**, the risk is **false negative**. In a PII scanner that is the worst outcome — the operator **must see in output** that this run is **reduced** (banner / log / report footer). Same rule as the **min-spec floor**: Alpine no-AVX metal in the gate (**[#821](https://github.com/DataBoar/data-boar/issues/821)** / **[#406](https://github.com/DataBoar/data-boar/issues/406)**) — the artifact **adapts to the floor and declares what it achieved**. SIGILL with **zero** Python traceback ([#929](https://github.com/DataBoar/data-boar/issues/929) title class) is the anti-pattern this wave forbids.

**Non-claims:** No performance numbers (including Rust prefilter) without a pinned file under `tests/benchmarks/`. `[noavx]` is **not** a shipped pip extra on `main` today. Auto CPU-select installer is **specified here**, not implemented in this docs PR.

### What already ships (do not invent a second stack)

| Surface | Role today | #1059 relevance |
| ------- | ---------- | --------------- |
| SQL extras (#1047) + `/extras` mount | Lean core; optional drivers | Unchanged; `[noavx]` is **CPU/ISA**, not SQL |
| Core `numpy` / `scipy` / `scikit-learn` | Default ML (TF-IDF + RandomForest) | PyPI wheels can **SIGILL** on no-AVX; wheelhouse is the measured fix |
| Extra `[dl]` | Optional sentence-transformers | Heavier ISA; skip or fail **loud** on no-AVX — never omit embeddings in silence |
| Extra `[richmedia]` | `pytesseract` + system `tesseract-ocr` | Buyer `[ocr]` maps here; missing binary is already a named miss, keep it loud |
| [PLAN_WHEELHOUSE_DISTRIBUTION.md](PLAN_WHEELHOUSE_DISTRIBUTION.md) | Hosted x86-64-v1 cells + recipe CI | **Canonical** no-AVX distribution; pip/pipx two-step in [TROUBLESHOOTING.md](../TROUBLESHOOTING.md) |
| pip / pipx onboarding | [PLAN_QUICKSTART.md](PLAN_QUICKSTART.md) + USAGE | Where CPU detect **chooses** stock vs wheelhouse |

### `[noavx]` = wheelhouse recipe **proven** in [#929](https://github.com/DataBoar/data-boar/issues/929)

Lab RCA (metal, min-spec, no AVX): the killer is **`libscipy_openblas` bundled in the PyPI wheel** (unconditional AVX/SSE), not numpy-core once `-Dcpu-baseline=none`. Env vars (`OPENBLAS_CORETYPE`, `NPY_DISABLE_CPU_FEATURES`) **do not** fix a compiled baseline.

**Measured fix (do not re-hypothesize):** build numpy/scipy/sklearn **from source against system OpenBLAS** (`DYNAMIC_ARCH` at runtime = no-AVX-safe); **do not** bundle `scipy-openblas`. Confirm build log: system OpenBLAS **YES**, `scipy-openblas` **NO**. Re-validate **on metal** (build-box AVX can import a poisoned wheel). Full recipe + traps live on **#929** and the wheelhouse plan (no `CFLAGS=-march=…`; audit wheels for embedded OpenBLAS).

**Product extra name:** `data-boar[noavx]` means **install via that wheelhouse path** (plus runtime `openblas` / `libgomp` as the recipe documents) — **not** a new BLAS implementation in-tree. Wire it to the existing **pip / pipx** onboarding (two-step `--find-links` / index), not a greenfield channel.

### Capability profiles (buyer names → extras that exist or stay named)

| Profile | Buyer ask | Map onto (no second engine) | Reduced-run rule |
| ------- | --------- | --------------------------- | ---------------- |
| **`[nlp]`** | Regex + classical ML | Core detector path (sklearn already in core) on **stock** or **wheelhouse** wheels | If ML kernels are absent or v1-only, **say so**; regex-only is an FN risk |
| **`[ocr]`** | Image text | Existing `[richmedia]` + system Tesseract | Missing Tesseract / flag off = **declared** skip, not silent |
| **`[dl]`** | Embeddings | Existing `[dl]` extra | On no-AVX, **do not** load AVX PyPI DL wheels; degrade **loud** (regex+ML only) |

Exact extra aliases in `pyproject.toml` stay **TBD** until a packaging slice; this PR only locks the **mapping + loud-degrade** contract.

### Installer detects CPU (planned)

| CPU | Choose | Must declare |
| --- | ------ | ------------ |
| Capable (AVX / x86-64-v2+ as required by **stock** PyPI wheels) | Default PyPI / stock wheel | Full advertised stack (including `[dl]` if requested) |
| No AVX (min-spec / x86-64-v1) | Wheelhouse (`[noavx]` path) | **Reduced** profile in stdout + report: which extras loaded, which skipped, FN-first warning |

Do **not** auto-install AVX wheels on a v1 CPU (SIGILL). Do **not** pretend DL ran if it did not. Pre-flight **before** `import numpy` remains the #929 lesson (SIGILL is not `try`/`except`).

### Execution table (doc-first → later slices)

| Step | Deliverable | Status |
| ---- | ----------- | ------ |
| P1 | This plan section + hub summary + `PLANS_TODO` survey rows | ✅ Done (docs PR) |
| P2 | Name `[noavx]` in USAGE/TECH_GUIDE pip/pipx onboarding; pointer to #929 + wheelhouse two-step (no new recipe) | ⬜ Pending |
| P3 | CPU pre-flight + **loud** capability banner / report footer (FN-first copy) | ⬜ Pending |
| P4 | Optional `pyproject` extra aliases `[nlp]` / `[ocr]` if they stay distinct from `[dl]` / `[richmedia]` | ⬜ Pending |
