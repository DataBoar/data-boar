# Plan: CREDIT_CARD / PAN sample join false positives + optional Luhn validator

**Status:** Active (shipping #1332)
**Date:** 2026-09-22
**Authors:** Fabio Leitao
**Priority:** H1 / U1
**GitHub:** [#1332](https://github.com/DataBoar/data-boar/issues/1332)

<!-- plans-hub-summary: Fix space-joined SQL column samples that false-trigger PCI PAN regexes; add optional validator: luhn on regex override YAML (#1332). -->
<!-- plans-hub-related: PLAN_SAMPLING_DEDUP_BEFORE_CAP.md, PLAN_YAML_PLUGIN_SYSTEM.md, PLAN_CHECKSUM_VALIDATOR_REGISTRY.md -->

**Synced with:** [PLANS_TODO.md](PLANS_TODO.md)

## Motivation

Production scans reported hundreds of `CREDIT_CARD` / `PAN` hits on INTEGER years, sequential ids, and `last_four_digits` columns. Root cause: distinct values were **space-joined** into one blob, and user **regex overrides** (PCI sample) matched across value boundaries. Built-in detection already uses Luhn on some paths; overrides were form-only.

## Decision (operator — #1332)

Ship **both** complementary mitigations:

1. **Non-numeric join separator** (U+241F ␟ — not Python `\s`, unlike ASCII U+001F) in `join_distinct_sample` — fixes the whole class (CEP, phone, etc.) without editing every pattern.
2. **`validator: luhn`** on `regex_patterns` plugin items — post-match semantic gate aligned with `PLAN_CHECKSUM_VALIDATOR_REGISTRY.md` (first algorithm: `luhn` only).

## Implementation map

| Location | Role |
| -------- | ---- |
| `connectors/sample_value_dedup.py` | `SAMPLE_VALUE_JOIN_SEPARATOR`, `join_distinct_sample` |
| `config/plugin_schema.yaml` | `validator` field (`luhn`) |
| `core/detector.py` | Load validators; `_pattern_passes_post_match_gates` |
| `utils/luhn_card.py` | Shared Luhn helper (detector + Pro prefilter) |
| `docs/compliance-samples/` | Document `validator:`; PCI sample PAN uses `luhn` |
| `tests/test_credit_card_sample_fp_1332.py` | Synthetic regression (#1332 AC) |
| `tests/test_lab_smoke_fp_numeric_ids.py` | Remove xfail; assert zero CREDIT_CARD on INTEGER fixtures |

## Phase table

| Phase | Description | Status |
| ----- | ----------- | ------ |
| 1 | Unit separator + regression tests | ✅ |
| 2 | Schema + detector `validator: luhn` | ✅ |
| 3 | Compliance sample + README | ✅ |

## Out of scope

- Per-value matching for structured DB columns (option 3 in #1332) — evaluate separately vs `boar_fast_filter` cost.
- Full checksum registry (#1639) — only `luhn` in this slice.
