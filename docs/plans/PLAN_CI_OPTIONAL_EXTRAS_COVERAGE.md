# Plan: CI optional extras coverage — #1638

<!-- plans-hub-summary: Dedicated Ubuntu pytest job installs SQL extras except mariadb (3.13 SyntaxError in 1.1.14) plus nosql/compressed/dataformats; deselects MAESTRO_ROOT-gated tests; skip-count ceiling 60. -->
<!-- plans-hub-related: PLAN_PACKAGING_EXTRAS.md, PLAN_WINDOWS_CI_ENABLEMENT.md -->

**Status:** In progress (job + ceiling in this PR; remaining extras are backlog)
**Date:** 2026-08-19
**Authors:** Fabio Leitao (operator); Cursor executor
**Priority:** **`[H1][U2]`** [P2] CI honesty
**GitHub:** [#1638](https://github.com/DataBoar/data-boar/issues/1638) (canonical)
**Found via:** [#1636](https://github.com/DataBoar/data-boar/issues/1636) / [#832](https://github.com/DataBoar/data-boar/issues/832) (Mongo/Redis timeout tests skipped in default CI)

**Synced with:** [PLANS_TODO.md](PLANS_TODO.md)

---

## Problem

Default GitHub Actions `uv sync` installs **one** extra (`shares`) of ~20 optional extras. Tests guarded by `importorskip` / `pytest.skip("… not installed")` **skip in CI** and pass on a developer machine that has extras. A regression in those tests is invisible until someone runs locally.

Evidence in #1638: **122 skipped** vs ~2188 passed on a recent default-matrix run.

## Goal (this slice)

1. Job **`test-extras`** on **`ubuntu-latest`**, **Python 3.13** only (not the full 3.12/3.13/3.14 matrix).
1. Install: `uv sync --extra postgres --extra mysql --extra mssql --extra mssql-pyodbc --extra oracle --extra nosql --extra compressed --extra dataformats --extra shares --group dev` (**`sql-all` minus `mariadb`**).
1. Apt: **`unixodbc-dev`** for `pyodbc`. No **`install-libmariadb-dev`** while the `mariadb` extra is omitted.
1. Full pytest + **skip-count ceiling** (`scripts/ci_pytest_skip_ceiling.py`, default **60**; JUnit parse via **`defusedxml`**). Deselect `MAESTRO_ROOT`-gated tests (`--ignore=tests/test_maestro_scripts.py` plus `--deselect` on the two mixed files) so the ceiling measures optional-Python-extra gaps. Public CI / forks must not clone private DataBoar/maestro; spinout maestro#8 skips those guards when the clone is absent. A future **opt-in** job may run Maestro consumer guards — not on **`test-extras`**.
1. Env **`DATA_BOAR_CI_EXTRAS=1`** so `tests/test_ci_extras_runtime.py` **requires** pymongo/redis/SQL-driver imports except `mariadb` (Mongo/Redis timeout cases must not skip).

### Python 3.13 — omit `mariadb` extra (decision)

PyPI **`mariadb` 1.1.14** is the latest **stable** (2026-08-20). Importing it on CPython 3.13 raises `SyntaxError: invalid escape sequence` in `site-packages/mariadb/connectionpool.py` (non-raw docstring). 3.13 turned that from warning into error. **`2.0.0rc1` / `rc2` exist** — this repo does **not** pin release candidates for extras CI. **`PYSEC-2026-217`** also tracks 1.1.14 with no PyPI fix (#922).

**Restore** `--extra mariadb` or `--extra sql-all` (and `install-libmariadb-dev`) when a **stable** connector imports on 3.13. Then add `"mariadb"` back to `_REQUIRED_WHEN_EXTRAS_JOB`.

### Out of scope (deliberate)

- **`dl`**, **`otel`**, **`richmedia`**, **`bigdata`**, **`grc-dashboard`**, **`legacy-doc`**, **`detection-fuzzy`** (dev group already has rapidfuzz) — heavy C-exts, live services, or already covered elsewhere.
- Live database engines. Tests that need a running server still skip; the target is **importable packages** with mocks/fixtures.
- Installing every extra on every matrix job.
- Checking out private **DataBoar/maestro** from public **`test-extras`** (forks, PAT, spinout skip-when-absent).

---

## Acceptance criteria

- [x] Dedicated extras job runs the suite with the broad extra set
- [x] Mongo/Redis cases in `tests/test_connector_timeouts.py` execute when extras are installed (`DATA_BOAR_CI_EXTRAS` import guard)
- [x] Skip ceiling fails the extras job if skipped tests exceed **60** (calibrated: extras run `989a4a3f` skipped=106 minus 56 Maestro guards = 50 remainder +10 slack)
- [x] `test-extras` deselects `MAESTRO_ROOT`-gated tests (no private Maestro checkout)
- [x] This plan + `PLANS_TODO` + hub wired

---

## Execution steps

| Step  | Scope                                                            | Status    |
| ----  | -----                                                            | ------    |
| **0** | Plan + `PLANS_TODO` + hub                                        | ✅         |
| **1** | `test-extras` job + unixodbc + skip ceiling                      | ✅         |
| **1b** | Omit `mariadb` extra on 3.13 (`SyntaxError` in 1.1.14)          | ✅         |
| **1c** | Deselect `MAESTRO_ROOT` guards from extras; ceiling **60**      | ✅         |
| **2** | Workflow shape tests                                             | ✅         |
| **3** | Merge + close #1638                                              | ⬜         |
| **4** | Optional later: `otel` / `bigdata` / `grc-dashboard` extras jobs | ⬜ backlog |

---

## Relationship to other plans

- [PLAN_PACKAGING_EXTRAS.md](PLAN_PACKAGING_EXTRAS.md) — extra **names** and lean core; this plan is **CI coverage** of those extras, not packaging layout.
- [PLAN_WINDOWS_CI_ENABLEMENT.md](PLAN_WINDOWS_CI_ENABLEMENT.md) — Windows job stays **`shares` only** (no libmariadb apt). Do not mix extras into `test-windows`.
