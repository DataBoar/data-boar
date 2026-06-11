# ADR 0052 — YAML-Based Plugin System: Centralized Schema and Unified Plugin File

- **Date (UTC):** 2026-05-14
- **Authors:** Fabio Leitao
- **Deciders:** Fabio Leitao

## Status

Accepted

### Status history

- 2026-05-14 — Accepted
- 2026-06-11 — Amended: retrofit to ADR-0045 UMADR format (metadata list, Authors, Status history) — GitHub #675

## Context

Data Boar supports three kinds of operator-provided extension patterns:

| Config key             | Purpose                              | Loader function         |
|------------------------|--------------------------------------|-------------------------|
| `regex_overrides_file` | Custom regex patterns for detection  | `_load_regex_overrides` |
| `ml_patterns_file`     | ML training terms (keyword/phrase)   | `_load_ml_patterns`     |
| `dl_patterns_file`     | Deep learning pattern terms          | `_load_dl_patterns`     |

Each loader has its own ad-hoc parsing with no formal schema.
Malformed entries are silently skipped.
There is no machine-readable contract for custom plugin authors.

As the number of operator deployments grows, this informal approach becomes a maintenance liability:
- Operators cannot validate plugin files before a scan run.
- Schema drift across the three loaders is invisible and hard to test.
- A "unified plugin file" (all types in one YAML) cannot be authored today.

---

## Decision

1. **Introduce `config/plugin_schema.yaml`** as the single source of truth for what a valid plugin file looks like for each pattern type.
   - Human-readable and machine-parseable.
   - No runtime dependency on `jsonschema` or `pydantic`; a lightweight custom validator (`config/plugin_validator.py`) reads it.

2. **Introduce `config/plugin_validator.py`** with `validate_plugin_file(path, plugin_type)`.
   - Returns `PluginValidationResult(valid: bool, issues: list[str])`.
   - Integrated into existing loaders as a pre-load check.
   - Emits `PluginValidationWarning` (via `warnings.warn`) for invalid items instead of silent discard.

3. **Add `patterns_plugin_file:` as a new unified config key** (backward-compatible with the three legacy keys).
   - A single YAML file with top-level sections `regex_patterns:`, `ml_patterns:`, `dl_patterns:`.
   - When both `patterns_plugin_file` and a legacy key point to the same content, `patterns_plugin_file` takes precedence per section.

4. **Backward compatibility guaranteed**: existing configs using the three separate keys continue to work unchanged.

---

## Alternatives Considered

| Alternative | Reason rejected |
|---|---|
| `pydantic` model validation | Adds runtime dependency; overkill for a list of simple dicts |
| `jsonschema` | Same dependency concern; YAML schema is more readable for operators |
| Ignore (keep ad-hoc) | Technical debt grows; silent failures hide operator misconfiguration |

---

## Consequences

**Positive:**
- Operators can author and self-validate plugin files before a scan run.
- Schema is the single documentation source for plugin format, reducing doc drift.
- Foundation for future CLI linter (`validate-plugin` subcommand) and Rust passthrough (Phase 2).

**Negative / Trade-offs:**
- Custom validator adds ~120 LOC to maintain vs. delegating to a library.
- `plugin_schema.yaml` must be updated when a new pattern type is added (enforced via test).

---

## Non-Goals

- Full JSON Schema compliance (not needed for simple list structures).
- Auto-generating plugin files (out of scope).
- Rust-side custom pattern injection (Phase 2, separate ADR).

---

## Related

- `docs/plans/PLAN_YAML_PLUGIN_SYSTEM.md`
- `config/plugin_schema.yaml`, `config/plugin_validator.py`
- `docs/SENSITIVITY_DETECTION.md` (operator reference)
- `config/regex_overrides.example.yaml` — example that must pass validation
