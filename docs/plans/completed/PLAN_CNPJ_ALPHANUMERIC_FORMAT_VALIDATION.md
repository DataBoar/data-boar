# Plan: CNPJ alphanumeric format – understanding, validation, and compatibility

**Status:** Completed (format compatibility phases 1–4; checksum phase 5 deferred post-archive)
**Date:** 2026-03-15
**Authors:** Fabio Leitao
**Priority:** H3

**Synced with:** [PLANS_TODO.md](../PLANS_TODO.md) (central to-do list)

## When implementing steps: update docs and tests; then update PLANS_TODO.md and this file.

This plan uses the app’s **existing scan capabilities** across multiple data sources (databases, filesystems, APIs, shares) to **validate compatibility** of found data with the **current Brazilian alphanumeric CNPJ format** (as opposed to the legacy numbers-and-punctuation-only format). The focus is to (1) **understand and specify** this format, (2) **assess whether the app can support it** (by default, flag, or config/regex/ML/DL overrides), and (3) **give clear recommendations** on how to get there. No change to existing behaviour until the format is agreed and an option is explicitly enabled.

---

## Goals

- **Format understanding:** Document the **current Brazilian alphanumeric CNPJ format** (how it differs from the old 14-digit numeric format with optional `./-/` punctuation). If an official or widely adopted spec exists (e.g. Receita Federal, sector norms), reference it; otherwise define a **working specification** (character set, length, structure) so the app can detect and validate it.
- **Compatibility validation:** Use existing scans (same connectors and sensitivity pipeline) to:
- Detect values that **match the alphanumeric CNPJ pattern** (and optionally the legacy numeric pattern).
- Report **compatibility**: e.g. “column X contains values compatible with alphanumeric CNPJ” vs “only legacy numeric CNPJ” vs “mixed/invalid”.
- **App capability:** Determine whether support is best delivered by **default** (new built-in pattern), **flag** (e.g. `--cnpj-alphanumeric` or config `detection.cnpj_alphanumeric: true`), or **config/regex/ML/DL overrides** only, and **recommend** the preferred approach.
- **Recommendations:** Provide operator-facing guidance (USAGE, example YAML, regex_overrides and ML terms) so that users can enable alphanumeric CNPJ detection and, if needed, phase in the new format without breaking existing numeric CNPJ detection.

---

## Current state (app)

- **Built-in CNPJ:** [core/detector.py](../../../core/detector.py) defines `LGPD_CNPJ` as **numeric only**:

  `\b\d{2}\.?\d{3}\.?\d{3}/?\d{4}-?\d{2}\b`

  (14 digits with optional `.` `/` `-`). This matches the **legacy** format only.

- **Overrides:** [regex_overrides_file](../../SENSITIVITY_DETECTION.md) and [regex_overrides.example.yaml](regex_overrides.example.yaml) allow adding or overriding patterns (name, pattern, norm_tag). So an **alphanumeric CNPJ pattern can be added via config** without code change.
- **ML/DL:** [ml_patterns_file](../../SENSITIVITY_DETECTION.md) and [sensitivity_detection.ml_terms](../../USAGE.md) (and DL equivalents) can include terms like `cnpj` for column-name/sample context. They do not define the **value format**; regex does.
- **Scan:** All connectors (SQL, MongoDB, Redis, filesystem, REST, SMB, etc.) use the same detector; any new or overridden pattern applies to **all data sources** in the “data soup” once loaded.
- **Report:** Findings show `pattern_detected` (e.g. `LGPD_CNPJ`); we could add a distinct pattern name for alphanumeric CNPJ (e.g. `LGPD_CNPJ_ALPHA`) and optionally a small “CNPJ format compatibility” summary in the report.

---

## Alphanumeric CNPJ format (to be specified)

The **legacy** CNPJ format is:

- **Numeric only:** 14 digits, optionally formatted as `XX.XXX.XXX/XXXX-XX` (dots, slash, hyphen).
- **Stored/formatted** in many systems as digits only or with punctuation.

The **current Brazilian alphanumeric format** is defined by **Instrução Normativa RFB nº 2.229/2024** (Receita Federal; in force 25 Oct 2024). Same 14-character length; display punctuation unchanged (`XX.XXX.XXX/XXXX-XX`). **Positions 1–8 (root)** and **9–12 (registration order):** alphanumeric `0–9`, `A–Z`. **Positions 13–14:** numeric only (verification digits). New registrations receive alphanumeric CNPJs from **July 2026**; legacy numeric CNPJs remain valid. **Plan outcome:** Phase 1 researched and documented the format; we use a **configurable regex** so that:

- The app can **detect** values that match the alphanumeric format.
- The app can **distinguish** in reports between “legacy numeric CNPJ”, “alphanumeric CNPJ”, and “not compatible”.

Implementation will **not** hardcode an unverified format; it will allow **regex override** and, if we add a built-in, it will be based on the agreed spec and documented as such.

---

## Scope: what the app can do

- **Scan:** Unchanged. All existing targets (DB, filesystem, API, shares) are scanned; column names and sample content are passed to the detector.
- **Detection:** Add or override a **regex pattern** for alphanumeric CNPJ. Optionally add **ML/DL** terms (e.g. “cnpj alfanumérico”) to improve context detection. The detector already merges regex_overrides with built-in patterns; no change to pipeline structure.
- **Compatibility notion:** “Compatible with alphanumeric CNPJ” = at least one value in the scanned data (per column/source) matches the alphanumeric pattern. We can report:
- Rows/columns where **only** legacy numeric CNPJ was found.
- Rows/columns where **only** alphanumeric CNPJ was found.
- Rows/columns where **both** appear (mixed).
- Rows/columns where **neither** matches (no CNPJ-like value in sample).

This is **pattern-based compatibility** (format of allowed or found data), not semantic validation (e.g. checksum or Receita Federal lookup).

---

## Implementation phases (to-dos)

### Phase 1: Understand and specify the format

| #   | To-do                                                                                                                                                                                                                                                                         | Status                                                                                           |
| --- | ---------------------------------------------------------------------                                                                                                                                                                                                         | ------                                                                                           |
| 1.1 | Research: document the current Brazilian alphanumeric CNPJ format (official or de facto: length, character set, structure, punctuation). Add a short “CNPJ formats” section in docs (e.g. SENSITIVITY_DETECTION.md or a new doc) describing legacy (numeric) vs alphanumeric. | ✅ Done (IN RFB 2.229/2024; positions 1–8, 9–12, 13–14; SENSITIVITY_DETECTION EN + pt-BR).        |
| 1.2 | If no single official spec is found, define a **working spec** (e.g. “alphanumeric CNPJ = 14–20 chars, [0-9A-Za-z] plus optional ./-/”) and document it as “configurable; adjust regex if your sector uses a different variant”.                                              | ✅ Done (official spec found; doc notes sector variants in override).                             |
| 1.3 | Propose a **regex pattern** that matches the alphanumeric format (and document overlap with the legacy numeric-only format, if any).                                                                                                                                          | ✅ Done (`\b[A-Z0-9]{2}\.?[A-Z0-9]{3}\.?[A-Z0-9]{3}/?[A-Z0-9]{4}-?\d{2}\b` in detector and docs). |
| 1.4 | Docs: add “CNPJ (Brazil): legacy vs alphanumeric” to SENSITIVITY_DETECTION.md and SENSITIVITY_DETECTION.pt_BR.md with the chosen spec and example.                                                                                                                            | ✅ Done                                                                                           |

### Phase 2: Feasibility – support by override only (no code change)

| #   | To-do                                                                                                                                                                                                                                  | Status                                                                                                                    |
| --- | ---------------------------------------------------------------------                                                                                                                                                                  | ------                                                                                                                    |
| 2.1 | Provide an **example regex_overrides** entry (and optional ml_patterns term) for alphanumeric CNPJ in docs (e.g. regex_overrides.example.yaml and SENSITIVITY_DETECTION.md). Name e.g. `LGPD_CNPJ_ALPHA`; norm_tag LGPD Art. 5.        | ✅ Done (name `LGPD_CNPJ_ALNUM`; config/regex_overrides.example.yaml, compliance-sample-lgpd.yaml, SENSITIVITY_DETECTION). |
| 2.2 | Verify with a small test or manual run that (1) existing scan still detects legacy `LGPD_CNPJ`, (2) with the override added, alphanumeric-style values are detected and reported with the new pattern name.                            | ✅ Done (tests/test_cnpj_formats.py, test_report_cnpj_compatibility.py).                                                   |
| 2.3 | Document in USAGE (EN + pt-BR): “To validate compatibility with alphanumeric CNPJ, add the pattern from regex_overrides.example.yaml (or the CNPJ formats doc); re-run the scan; check report for pattern_detected = LGPD_CNPJ_ALPHA.” | ✅ Done (USAGE.md and USAGE.pt_BR.md reference LGPD_CNPJ_ALNUM and config/override).                                       |

### Phase 3: Optional built-in or flag (if desired)

| #   | To-do                                                                                                                                                                                                                                        | Status                                                                                                                                                     |
| --- | ---------------------------------------------------------------------                                                                                                                                                                        | ------                                                                                                                                                     |
| 3.1 | Decide: support as **default built-in** (new pattern in DEFAULT_PATTERNS), **config flag** (e.g. `detection.cnpj_alphanumeric: true` that adds the pattern at load time), or **override only**. Document decision and rationale in the plan. | ✅ Done (decision: **built-in + config flag**; pattern gated by `detection.cnpj_alphanumeric` so legacy behaviour unchanged; override-only also supported). |
| 3.2 | If built-in: add `LGPD_CNPJ_ALPHA` (or similar) to DEFAULT_PATTERNS with the agreed regex; ensure legacy `LGPD_CNPJ` remains; add test that both patterns can match their respective samples.                                                | ✅ Done (`LGPD_CNPJ_ALNUM` in core/detector.py; tests in test_cnpj_formats.py).                                                                             |
| 3.3 | If config flag: add `detection.cnpj_alphanumeric` (or similar) in config loader; when true, inject alphanumeric pattern into detector; document in USAGE and config schema.                                                                  | ✅ Done (config/loader.py; USAGE EN + pt-BR).                                                                                                               |
| 3.4 | Optional report enhancement: add a one-line “CNPJ format compatibility” summary (e.g. “Legacy numeric: N columns; Alphanumeric: M columns”) in Report info or a small dedicated section when both patterns are in use.                       | ✅ Done (report/generator.py: CNPJ format compatibility counts in report).                                                                                  |

### Phase 4: Recommendations and docs

| #   | To-do                                                                                                                                                                                                                                                                                                                                       | Status                                                                      |
| --- | ---------------------------------------------------------------------                                                                                                                                                                                                                                                                       | ------                                                                      |
| 4.1 | Write a short **“How to get there”** section (in this plan or in docs): (1) Use regex_overrides_file with the alphanumeric pattern; (2) optionally add ML term “cnpj” / “cnpj alfanumérico”; (3) run scan; (4) use report to see where alphanumeric-compatible data appears; (5) if built-in or flag is implemented, enable it and re-scan. | ✅ Done (see "How to get there" above; USAGE documents config and override). |
| 4.2 | Update PLANS_TODO.md and this plan when steps are completed; ensure SENSITIVITY_DETECTION and USAGE docs (EN + pt_BR) are in sync.                                                                                                                                                                                                          | ✅ Done                                                                      |
| 4.3 | Regression: full test suite passes; existing LGPD_CNPJ behaviour unchanged when alphanumeric is not enabled.                                                                                                                                                                                                                                | ✅ Done                                                                      |

### Phase 5: Future checksum validation (CNPJ, CPF and other Brazilian IDs) — deferred post-archive

Not part of the archived delivery; pattern-based compatibility (phases 1–4) is what shipped.

| #   | To-do                                                                                                                                                                                                                           | Status |
| --- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------ |
| 5.1 | Research official checksum algorithms for numeric and alphanumeric CNPJ, CPF and other Brazilian identifiers already covered by regex (e.g. PIS/PASEP), and document them in a detector-logic design note.                      | ⬜ Deferred (post-archive)      |
| 5.2 | Design how checksum validation would integrate with the existing detector pipeline (e.g. optional flag or config section that adds a second “validated” pass after regex) without breaking current behaviour or performance.    | ⬜ Deferred (post-archive)      |
| 5.3 | When/if implemented, update SENSITIVITY_DETECTION docs and PLANS_TODO.md to reflect that format compatibility (regex) and checksum validation are distinct, opt-in layers.                                                      | ⬜ Deferred (post-archive)      |

---

## How to get there (operator summary)

1. **Enable alphanumeric CNPJ (recommended):** In your config, set `detection.cnpj_alphanumeric: true`. The built-in pattern `LGPD_CNPJ_ALNUM` will be active; legacy `LGPD_CNPJ` remains active. Re-run the scan; the report will show `pattern_detected` = `LGPD_CNPJ` or `LGPD_CNPJ_ALNUM` per finding, and the “CNPJ format compatibility” summary when both patterns are in use.
1. **Override-only (no config flag):** Add the `LGPD_CNPJ_ALNUM` entry from `config/regex_overrides.example.yaml` or [SENSITIVITY_DETECTION.md](SENSITIVITY_DETECTION.md#yaml-example-regex-overrides) to your `regex_overrides_file`. No code or config schema change required.
1. **Optional:** Add ML term `cnpj` or `cnpj alfanumérico` in your `ml_patterns_file` or `sensitivity_detection.ml_terms` to improve column-name context (same as for legacy CNPJ).
1. **Report:** Use the Excel report “Recommendations” sheet and, when available, the CNPJ format compatibility summary to see where legacy vs alphanumeric data appears across the data soup.

See [USAGE.md](../../USAGE.md) (EN) and [USAGE.pt_BR.md](../../USAGE.pt_BR.md) (pt-BR) for config keys and examples.

---

## Recommendations (summary)

- **Short term (no code change):** Use **regex_overrides_file** (and optional ML term) to add the alphanumeric CNPJ pattern once the format is specified. Point operators to the example YAML and the “CNPJ formats” doc. Scans then validate “compatibility” in the sense of “data matching this pattern is present”.
- **Medium term (optional):** If the format is stable and widely used, add a **built-in** pattern `LGPD_CNPJ_ALPHA` or a **config flag** so that deployments can enable alphanumeric CNPJ without maintaining an override file. Keep legacy `LGPD_CNPJ` as default so existing behaviour is unchanged.
- **Report:** Optionally add a short “CNPJ format compatibility” summary when both patterns are active, so IT/compliance can see at a glance where legacy vs alphanumeric data appears across the data soup.

---

## Dependencies and constraints

- **No breaking change:** Legacy numeric CNPJ detection (`LGPD_CNPJ`) remains the default and continues to work as today.
- **Format first:** Implementation of a built-in or flag should follow Phase 1 (format understood and documented); override-only support can be documented as soon as the regex is agreed.
- **Pattern only:** The app validates **format compatibility** (pattern of allowed or found data), not semantic validity (e.g. CNPJ checksum or registry lookup).

---

## Conflict and placement in roadmap

- **No conflicts** with other plans. This is additive (new pattern and optional report summary).
- **Recommended placement:** Can be done in parallel with Compliance samples or after; depends only on having the format specified. See [PLANS_TODO.md](../PLANS_TODO.md) for the full sequence.

---

## Last updated with plan file. Update PLANS_TODO.md when completing or adding to-dos.
