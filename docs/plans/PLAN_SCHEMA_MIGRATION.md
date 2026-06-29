# Plan: SQLite schema auto-migration (`_ensure_*` convention)

<!-- plans-hub-summary: SQLite schema auto-migration — _ensure_* convention, regression test pattern, Alembic roadmap -->

**Status:** Active
**Date:** 2026-05-25
**Authors:** Fabio Leitao
**Priority:** H2
**GitHub:** [#736](https://github.com/FabioLeitao/data-boar/issues/736) (`_ensure_*` convention; filesystem_findings Phase 1 follow-up)
**Replaces:** Schema migration gap called out in [PLAN_SELF_UPGRADE_AND_VERSION_CHECK.md](PLAN_SELF_UPGRADE_AND_VERSION_CHECK.md) (local DB evolution before remote upgrade UX)
**Related:** [PLAN_INCREMENTAL_SCAN_IDEMPOTENCY.md](PLAN_INCREMENTAL_SCAN_IDEMPOTENCY.md) (Phase 1 columns on `filesystem_findings`), [PLAN_BUILD_IDENTITY_RELEASE_INTEGRITY.md](PLAN_BUILD_IDENTITY_RELEASE_INTEGRITY.md)

**Synced with:** [PLANS_TODO.md](PLANS_TODO.md)

---

## Context

`LocalDBManager` uses SQLAlchemy `Base.metadata.create_all()` on startup. That creates **missing tables** but does **not** add columns to **existing** tables. Operators who keep `audit_results.db` across releases therefore hit `OperationalError: table … has no column named …` when new `Column()` fields ship without a migration hook.

Issue **#736** (P1): `filesystem_findings` gained `source_mtime_ns`, `source_size`, and `content_fingerprint` in commit `f29ae567` (Phase 1 incremental scan) without `_ensure_*` methods — scans crashed on legacy DBs until fixed.

---

## Decision: `_ensure_*` convention

1. **New table** (no prior installs): prefer `SomeModel.__table__.create(engine, checkfirst=True)` from a `_ensure_<table>_table()` helper called in `LocalDBManager.__init__` after `create_all` (existing pattern for `aggregated_identification_risk`, `data_source_inventory`, etc.).

2. **New column on an existing table:** add `_ensure_<column>_column()` that:
   - queries `pragma_table_info('<table>')` for the column name;
   - runs `ALTER TABLE … ADD COLUMN …` when absent;
   - commits on the connection (same pattern as `_ensure_tenant_column()`).

3. **Wire every `_ensure_*` in `LocalDBManager.__init__`** immediately after `create_all` and existing ensures, in dependency-safe order.

4. **Rule (enforced by review + regression tests):** every new `Column()` on a table that can already exist in the field **must** ship with a matching `_ensure_*` and a test that bootstraps a **legacy** schema without the column and asserts migration on `LocalDBManager` init.

---

## Regression test pattern

Template: `tests/test_database.py::test_localdbmanager_migrates_filesystem_findings_columns`

1. Create a SQLite file with **raw** `CREATE TABLE` SQL (pre-migration shape) via `create_engine` + `text()` — **do not** construct `LocalDBManager` first.
2. Instantiate `LocalDBManager(db_path)`.
3. Assert each new column exists via `pragma_table_info`.
4. Call `mgr.dispose()` in `finally`.

Repeat for each additive column group or table when schema changes.

---

## Audit checklist (LocalDBManager vs models)

When adding schema, verify:

| Model / table | Migration mechanism |
| --- | --- |
| `scan_sessions` additive columns | `_ensure_tenant_column`, `_ensure_technician_column`, `_ensure_config_scope_hash_column`, `_ensure_jurisdiction_hint_column` |
| `filesystem_findings` Phase 1 identity | `_ensure_source_mtime_ns_column`, `_ensure_source_size_column`, `_ensure_content_fingerprint_column` (**#736**) |
| Whole new tables (post–first release) | `_ensure_*_table()` + `create(checkfirst=True)` |
| `maturity_assessment_answers.row_hmac` | `_ensure_maturity_row_hmac_column` |
| `webauthn_credentials.roles_json` | `_ensure_webauthn_roles_json_column` |

**Note:** `ScanObjectState` and other **new tables** are created by `create_all` when the table is absent; column adds on **existing** tables always need `_ensure_*`.

---

## Alembic roadmap (deferred)

While the schema is small, **`_ensure_*` + pytest** stays the single source of truth (no Alembic dependency in the product image).

**Trigger to introduce Alembic** (any one):

- More than ~5 column migrations per release cycle;
- Non-additive migrations (rename, drop, backfill);
- Multi-tenant or replicated SQLite → server DB move.

Until then: document each `_ensure_*` in this plan or the feature plan that introduced it; keep [PLAN_SELF_UPGRADE_AND_VERSION_CHECK.md](PLAN_SELF_UPGRADE_AND_VERSION_CHECK.md) focused on **remote** upgrade UX, not local DDL.

---

## To-do

| # | Task | Status |
| --- | --- | --- |
| 1 | Fix `filesystem_findings` Phase 1 columns + regression test (**#736**) | ✅ Done |
| 2 | Document convention (this plan) + AGENTS.md rule | ✅ Done |
| 3 | Optional: CI guard that diffs SQLAlchemy models vs `_ensure_*` call list | ⬜ Pending |
