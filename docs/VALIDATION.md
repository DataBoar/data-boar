# Detection accuracy baseline (precision / recall / F1)

**Português (Brasil):** [VALIDATION.pt_BR.md](VALIDATION.pt_BR.md)

**Audience:** collaborators, Design Science reviewers, technical buyers who need a
**measured** detection baseline (not a marketing assertion).

**Related:** [TESTING_POC_GUIDE.md](TESTING_POC_GUIDE.md) (POC scenario corpus),
ADR 0007 (synthetic corpus before real data), GitHub issue **#835**.

---

## 1. What this is

Data Boar already has **performance** benchmarks. This document publishes the first
**accuracy** baseline of the PII detector against a **labeled synthetic** fixture set:

| Artifact | Path |
| -------- | ---- |
| Fixtures + manifest | `tests/data/f1_validation/` (`ground_truth.yaml`) |
| Regenerate fixtures | `uv run python scripts/generate_f1_validation_fixtures.py` |
| Measure P/R/F1 | `uv run python scripts/validate_detection_f1.py` |

The harness calls the real detector API
`SensitivityDetector.analyze` → `(sensitivity, pattern_detected, norm_tag, confidence 0–100)`.

---

## 2. Methodology (anti-leakage)

Four ground-truth classes:

| Class | Meaning |
| ----- | ------- |
| `pii` | Clear synthetic PII — must detect |
| `clean` | No PII — must not alert |
| `tricky_fp` | Looks like PII / entertainment noise — ideally no alert |
| `tricky_fn` | Hard / masked / stego gap — often miss; `expected_miss: true` |

**Splits (Presidio-research style):**

| Split | Role |
| ----- | ---- |
| `measure/` | **Only** split used for the published F1 numbers below |
| `calibrate/` | Reserved for future confidence-threshold tuning |

**Hard rule:** the same **synthetic template** (and the same synthetic identifiers)
must **not** appear in both splits. The harness checks this (`anti-leakage: OK`).
Calibrating thresholds on the same templates used for final measurement would
inflate F1 optimistically.

Phase 1 covers **text formats** (txt/csv/tsv/json/xml/html) with the **same**
identifiers across formats so later work can separate **extraction** failures
from **detection** failures. SQL/NoSQL/shares and report confidence bands are
**out of scope** for this baseline (plan Phases 2–4).

---

## 3. Published baseline (measure split)

Re-run any time:

```bash
uv run python scripts/validate_detection_f1.py --split measure
```

| Field | Value |
| ----- | ----- |
| **Date (UTC)** | 2026-08-17 |
| **Commit** | recorded at publish time on `main` after merge of #835 |
| **Files scored** | 12 (`measure` only) |
| **TP / FP / TN / FN** | 6 / 4 / 0 / 2 |
| **Precision** | **0.6000** |
| **Recall** | **0.7500** |
| **F1** | **0.6667** |

### Per pattern (measure)

| Pattern | Precision | Recall | F1 |
| ------- | --------- | ------ | -- |
| `EMAIL` | 1.0000 | 1.0000 | 1.0000 |
| `LGPD_CNPJ` | 1.0000 | 1.0000 | 1.0000 |
| `LGPD_CPF` | 1.0000 | 0.7500 | 0.8571 |

### Per class (measure)

| Class | Notes |
| ----- | ----- |
| `pii` | 6/6 true positives across formats (F1 **1.0000**) |
| `tricky_fn` | 0/2 — masked/spaced CPF and stego placeholder (honest FN; `expected_miss`) |
| `clean` | 2 FP — ML entertainment-context MEDIUM on synthetic catalog text |
| `tricky_fp` | 2 FP — lyrics date/phone context + ML on invalid CPF shapes (checksum correctly blocks `LGPD_CPF`) |

---

## 4. Known limitations (Design Science)

These are **measured** gaps, not deferred silence:

1. **Masked / spaced CPF** — `measure/tricky_fn/masked_spaced_cpf.txt` does not yield `LGPD_CPF`.
2. **Stego / absent payload** — `stego_placeholder.txt` documents the stego gap without embedding binary LSB in Phase 1.
3. **ML entertainment heuristic** — can emit `ML_POTENTIAL_ENTERTAINMENT` (MEDIUM) on non-song short/catalog text and on invalid-CPF placeholders, lowering file-level precision.
4. **Weak patterns in lyrics** — `PHONE_BR` / `DATE_DMY` still surface (downgraded to MEDIUM with lyrics context); counts as FP for `tricky_fp` labels.
5. **Phase 1 format scope** — binary office/PDF/OCR matrices remain for later plan phases; do not claim full-format F1 from this table.

---

## 5. What this is not

- Not a CI **gate** that fails on F1 drift (baseline is published; smoke tests only check structure, anti-leakage, and clear-PII recall).
- Not permission to skip ADR 0007 before real customer data.
- Not a substitute for the POC scenario corpus in [TESTING_POC_GUIDE.md](TESTING_POC_GUIDE.md).

---

## 6. Refresh ritual

1. Edit or regenerate fixtures (`generate_f1_validation_fixtures.py`).
2. Run `validate_detection_f1.py --split measure` (and optionally `--json`).
3. Update **§3** numbers in this file and the pt-BR pair.
4. Keep `calibrate/` out of the published table unless you are documenting threshold experiments separately.
