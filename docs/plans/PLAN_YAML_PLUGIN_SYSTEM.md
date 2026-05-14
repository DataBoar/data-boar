---
Status: In Progress
Priority: H1
Tags: extensibility, plugin, yaml, schema, patterns
ADR: ADR-0052
---

# PLAN — YAML-Based Plugin System (Extensibility)

## Goal

Allow operators to add custom discovery patterns without modifying the Data Boar core engine (Python or Rust). All custom pattern definitions are validated against a single, centralized YAML schema file before the scan engine loads them.

## Problem Statement

- Three separate pattern file keys (`regex_overrides_file`, `ml_patterns_file`, `dl_patterns_file`) each have their own ad-hoc YAML parser with no formal schema.
- Malformed plugin files fail **silently**: the engine skips bad items without reporting why.
- Operators have no machine-readable contract to validate their custom files before a scan run.
- There is no support for a **unified plugin file** (one file with all pattern types), requiring operators to manage 3+ separate configs.

## Approach (Three Phases)

### Phase 1 — Canonical Schema + Validator (this plan) ✅

1. `config/plugin_schema.yaml` — centralized definition for all plugin types (regex, ml, dl).
2. `config/plugin_validator.py` — lightweight validator (no third-party deps) that reads the schema and checks a plugin file before loading, emitting `PluginValidationWarning` with actionable messages.
3. `config/loader.py` — integrate validator call into existing `_load_regex_overrides`, `_load_ml_patterns`, `_load_dl_patterns`. **No behaviour change** for valid files; warnings surfaced for invalid ones.
4. New unified key: `patterns_plugin_file:` — a single YAML file that may contain `regex_patterns:`, `ml_patterns:`, and/or `dl_patterns:` sections. Backward-compatible with the three legacy keys.
5. Tests: `tests/test_plugin_schema.py` — unit-test validator edge cases (missing required field, wrong type, unknown key, unified file).

### Phase 1b — Context gates + PCI sample calibration (queued; `PLANS_TODO` **S4b**)

- **Driver:** PCI-DSS v4 readiness — noisy logs where digit runs collide with PAN-shaped regexes; validate ADR-0052 YAML expressiveness under stress.
- **Engine work:** optional schema fields (e.g. proximity keywords, metadata) must wire into `SensitivityDetector` (regex light → Luhn or keyword window before heavy work)—not validator-only.
- **Sample file:** `docs/compliance-samples/compliance-sample-pci_dss.yaml` — align PAN patterns with built-in `CREDIT_CARD` to avoid duplicate findings; document framing already warns on bare routing-style regexes.
- **Exit:** same discipline as other sprint rows — tests + `check-all`; then remove or date the matching row in `docs/ops/today-mode/CARRYOVER.md` (EN + pt-BR).

### Phase 2 — Rust Passthrough (future)

- Export compiled regex patterns from the plugin file to the Rust `boar_fast_filter` layer so custom regexes benefit from Rust-speed matching.

### Phase 3 — CLI Linter (future)

- `uv run python -m data_boar validate-plugin <file>` — operator can validate a plugin file standalone, outside a scan run.

## Acceptance Criteria (Phase 1)

- [ ] `config/plugin_schema.yaml` documents all three pattern types with required/optional fields, types, and constraints.
- [ ] `validate_plugin_file(path, plugin_type)` returns a `PluginValidationResult` (valid bool + list of issue strings).
- [ ] Invalid items in `regex_overrides_file` emit `PluginValidationWarning` (not silent skip).
- [ ] `patterns_plugin_file:` config key loads all three sections from one file.
- [ ] All existing example files pass validation.
- [ ] `tests/test_plugin_schema.py` green with ≥ 8 test cases.

## Related

- ADR-0052 (architectural decision)
- `docs/SENSITIVITY_DETECTION.md` — add `patterns_plugin_file` to operator reference
- `config/regex_overrides.example.yaml` — already valid under new schema
