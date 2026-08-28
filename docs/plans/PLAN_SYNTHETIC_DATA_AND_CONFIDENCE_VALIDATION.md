# Plan: Synthetic and true-like data sources, confidence scoring, and operator guidance

<!-- plans-hub-summary: Synthetic fixtures + F1 harness (#835); v1.8.0 #1060 composite eval (F1 + latency + throughput + re-id risk as separate axes; no single score) -->
<!-- plans-hub-related: PLAN_SYNTHETIC_DATA_LAB.pt_BR.md, PLAN_BENCHMARK_SAFE_AXIS.md, PLAN_CLAIMS_CONSISTENCY_AND_ANTI_OVERCLAIM.md, ../VALIDATION.md -->

**Português (Brasil):** [PLAN_SYNTHETIC_DATA_AND_CONFIDENCE_VALIDATION.pt_BR.md](PLAN_SYNTHETIC_DATA_AND_CONFIDENCE_VALIDATION.pt_BR.md)

**Status:** In Progress (Phase 1 + 5.1 on `main`; v1.8.0 survey [#1060](https://github.com/DataBoar/data-boar/issues/1060) enriches this plan — do not archive)
**Date:** 2026-03-15 (v1.8.0 wave: 2026-08-27)
**Authors:** Fabio Leitao
**Priority:** H3
**Depends on:** ADR-0007
**Milestone:** v1.8.0
**Issue:** [#835](https://github.com/DataBoar/data-boar/issues/835) (Phase 1 + 5.1 baseline F1) · **[#1060](https://github.com/DataBoar/data-boar/issues/1060)** (composite eval methodology)

**Synced with:** [PLANS_TODO.md](PLANS_TODO.md) (central to-do list)

## When implementing steps: update docs and tests; then update PLANS_TODO.md and this file.

This plan enables **creation of synthetic and possible "true" data sources** that cover the full range of ingredients the app can ingest (all compatible file formats, network shares, SQL and NoSQL sources in popular flavors). It adds **intentional false positives and false negatives** so we can **validate and score how confident we are** in a discovery, and it delivers **operator-facing guidance**: from "probably nothing serious, but better safe than sorry" (with instructions to manually verify) to "chance of high risk of violation, but ML/DL may be struggling" (with how to manually verify and how to tune configs and options). It also covers **timeouts and connectivity/network I/O issues** with instructions on how to solve or prevent them for the next scan sessions.

---

## Goals

- **Synthetic and true-like data sources:** Provide or document how to create fixtures that include:
- **All compatible file formats** (txt, csv, tsv, json, xml, html, pdf, docx, odt, xlsx, msg, eml, etc. – see [connectors/filesystem_connector.py](../connectors/filesystem_connector.py) and text extraction).
- **Network shares:** SMB/CIFS, NFS, WebDAV, SharePoint – sample data or scripts to expose minimal shares for testing.
- **SQL:** PostgreSQL, MySQL/MariaDB, SQLite, MSSQL, Oracle (popular flavors) – e.g. Docker Compose or in-memory DBs with known schema and rows.
- **NoSQL:** MongoDB, Redis, Snowflake – sample collections/keys/data.
- **False positives and false negatives:** In the fixture data, include:
- **Ground truth labels** (per column, file, or row: truly PII/sensitive vs not).
- **Intentional false positives:** Content that may trigger detection but is not real PII (e.g. lyrics with digits, fiction with fake CPF, tablature).
- **Intentional false negatives:** Real PII or sensitive data that is hard to detect (masked, non-standard format, rare pattern).
- Use these to **validate** detector behaviour and to **score** confidence (e.g. precision/recall per run or per pattern).
- **Confidence and operator guidance:** From each discovery (sensitivity_level, pattern_detected, ml_confidence), derive a **discovery confidence band** and **recommendations**:
- **Probably nothing serious:** Low/medium confidence or weak pattern; recommend "better safe than sorry" and **how to manually access and verify** (e.g. open the table/file, spot-check values).
- **High risk but ML/DL may be struggling:** High sensitivity but borderline confidence or conflicting signals; recommend **manual verification** and **how to tune** (regex_overrides_file, ml_patterns_file, dl_patterns_file, min_sensitivity, timeouts, sample_limit).
- **High confidence finding:** Strong pattern + high ml_confidence; still recommend verification and remediation steps.
- **Timeouts and connectivity:** Document and, where useful, **simulate** timeout and network I/O issues so that:
- The app’s existing **failure_hint** (unreachable, auth_failed, permission_denied, timeout) is surfaced in reports and docs.
- **Instructions** are provided: how to **solve** (increase timeout, check network, retry) and how to **prevent** for the next scan (config timeouts, network path, off-peak run).

---

## Current state

- **File formats:** [connectors/filesystem_connector.py](../connectors/filesystem_connector.py) and text extraction support txt, csv, tsv, json, xml, html, pdf, docx, odt, xlsx, ods, odp, msg, eml, etc. (SUPPORTED_EXTENSIONS).
- **Connectors:** SQL (PostgreSQL, MySQL, MariaDB, SQLite, MSSQL, Oracle), MongoDB, Redis, Snowflake, SMB, NFS, WebDAV, SharePoint, Power BI, Dataverse, REST API (see [TOPOLOGY.md](TOPOLOGY.md)).
- **Detection:** [core/detector.py](../core/detector.py) returns sensitivity_level, pattern_detected, norm_tag, ml_confidence (0–100). Report includes recommendations sheet and failure hints ([core/database.py](../core/database.py) `failure_hint(reason)`).
- **No shared synthetic dataset with measured P/R/F1:** Phase 1 (#835) adds `tests/data/f1_validation/` + `scripts/validate_detection_f1.py` and publishes numbers in [VALIDATION.md](../VALIDATION.md). POC scenario corpus (`generate_synthetic_poc_corpus.py` / EXPECTED.txt) remains complementary. Phases 2–4 (SQL/NoSQL/shares, report confidence bands) still open.
- **Report:** Recommendations and scan failures already show hints; there is no explicit **discovery confidence band** (e.g. “probably nothing serious” vs “high risk, tune ML/DL”) nor a dedicated “operator guidance” section for manual verification and tuning.

---

## Scope: synthetic data ingredients

| Category        | Ingredients to cover                                                                 | Delivery (fixture / doc / script)        |
| --------------- | ------------------------------------------------------------------------------------ | ----------------------------------       |
| **Files**       | txt, csv, tsv, json, xml, html, pdf, docx, odt, xlsx, ods, msg, eml, etc.            | Fixture tree + ground-truth manifest     |
| **SQL**         | PostgreSQL, MySQL, MariaDB, SQLite, MSSQL, Oracle                                    | Docker Compose or in-memory + SQL dumps  |
| **NoSQL**       | MongoDB, Redis, Snowflake                                                            | Docker or test containers + seed data    |
| **Shares**      | SMB/CIFS, NFS, WebDAV, SharePoint                                                    | Scripts or minimal server + sample files |
| **APIs**        | REST (JSON), Power BI, Dataverse                                                     | Mock or minimal API + sample responses   |

Ground truth: for each fixture (file, table/column, API response), a **manifest** (YAML/JSON) states whether it contains real PII, no PII, or “tricky” (FP/FN) so we can compare scan output and compute precision/recall and confidence.

---

## False positives and false negatives (in fixtures)

- **False positive (FP):** Content that the detector flags as sensitive but that is **not** real PII (e.g. song lyrics with dates, guitar tab digits, novel with fake CPF). Include several in fixtures; label in manifest so we can measure FP rate and adjust thresholds or patterns.
- **False negative (FN):** Content that **is** PII/sensitive but the detector misses (e.g. masked CPF, non-standard date format, rare identifier). Include several; label in manifest to measure FN rate and improve regex/ML/DL or document “manual verification recommended”.
- **Use:** (1) Run scan on fixture set; (2) compare findings to manifest; (3) compute precision, recall, F1; (4) optionally **score confidence** per finding (e.g. “this finding matches a known FP” → lower confidence; “this finding matches known PII” → high confidence). Results can feed the **operator guidance** (e.g. “ML/DL may be struggling” when FN rate is high on tricky rows).

---

## Confidence bands and operator guidance

- **Inputs:** sensitivity_level, pattern_detected, ml_confidence (and optional dl_confidence), plus optional “matches_ground_truth” when running against labeled fixtures.
- **Bands (example):**
- **Probably nothing serious:** LOW sensitivity, or MEDIUM with low confidence and weak pattern (e.g. GENERAL). Guidance: “Better safe than sorry. Manually verify: [link or steps to open target and spot-check]. If confirmed non-sensitive, consider adding to ML non-sensitive terms or excluding path in config.”
- **Better safe than sorry:** MEDIUM sensitivity or HIGH with moderate confidence. Guidance: “Manually access and verify: [steps]. If PII confirmed, apply remediation; if false positive, tune regex_overrides or ml_patterns_file to reduce noise.”
- **High risk – verify and remediate:** HIGH sensitivity and high confidence. Guidance: “Treat as potential violation. Manually verify: [steps]. Remediate (mask, delete, or document base legal).”
- **High risk but ML/DL may be struggling:** HIGH sensitivity but low/borderline confidence, or pattern_detected = ML_DETECTED / ML_POTENTIAL with many FNs in validation. Guidance: “Manual verification strongly recommended. Consider tuning: (1) Add examples to ml_patterns_file / dl_patterns_file; (2) Adjust regex_overrides_file for your domain; (3) Increase sample_limit or review min_sensitivity; (4) See docs/SENSITIVITY_DETECTION.md for options.”
- **Report:** Add a column or section “Discovery confidence” and “Operator guidance” (short text or link to doc). Recommendations sheet can be extended with these messages per finding or per band.

---

## Timeouts and connectivity

- **Existing:** [core/database.py](../core/database.py) `failure_hint(reason)` already maps unreachable, auth_failed, permission_denied, timeout to human-readable next steps. Scan failures appear in the report with these hints.
- **Plan:** (1) **Document** in USAGE or a dedicated “Troubleshooting” section: how to **solve** (increase timeout in config or connector, check network/DNS/firewall, retry during off-peak) and how to **prevent** for the next scan (set timeouts, reduce parallelism, use stable network path). (2) Optionally add **fixture or test** that simulates a slow/timeout target so the report shows the timeout hint and we can assert the message. (3) Extend failure_hint or report text with a short “Prevent next time” line where useful (e.g. “Set scan timeouts in config; see docs/USAGE.md.”).

---

## Implementation phases (to-dos)

### Phase 1: Fixture structure and file-format coverage

| #   | To-do                                                                                                                                                                                  | Status |
| --- | ---------------------------------------------------------------------                                                                                                                  | ------ |
| 1.1 | Create fixture root (e.g. `fixtures/synthetic_data/` or `test_data/validation/`) with subdirs: files/, sql/, nosql/, shares/ (or doc for shares).                                      | ✅ Done (`tests/data/f1_validation/` measure+calibrate; sql/nosql/shares → Phase 2–3) |
| 1.2 | Add sample files for all compatible extensions (txt, csv, json, pdf, docx, xlsx, odt, etc.): some with real PII, some with no PII, some FP (e.g. lyrics/dates), some FN (e.g. masked). | ✅ Partial — text formats txt/csv/tsv/json/xml/html + 4 classes; binary/office later |
| 1.3 | Ground-truth manifest (YAML/JSON): path → label (`pii` / `clean` / `tricky_fp` / `tricky_fn`) + `expected_miss` + disjoint measure/calibrate templates. | ✅ Done (`ground_truth.yaml`) |
| 1.4 | Doc: how to run a scan against the fixture root and compare results to manifest (manual or script).                                                                                    | ✅ Done ([VALIDATION.md](../VALIDATION.md) + harness) |
| 1.5 | Tests: optional pytest that runs detector on a subset of fixtures and asserts expected sensitivity or counts; or doc-only.                                                             | ✅ Done (`tests/test_validate_detection_f1.py` — structure/anti-leakage/clear-PII; F1 numbers published not asserted) |

### Phase 2: SQL and NoSQL fixtures

| #   | To-do                                                                                                                                                                      | Status |
| --- | ---------------------------------------------------------------------                                                                                                      | ------ |
| 2.1 | SQL: Docker Compose or script to start PostgreSQL, MySQL, SQLite (in-memory or file) with tables that have known PII, no PII, FP, FN columns; document connection details. | ⬜      |
| 2.2 | NoSQL: MongoDB and Redis seed data (collections/keys with known labels); document how to run and point config at them.                                                     | ⬜      |
| 2.3 | Extend ground-truth manifest for DB fixtures (table.column → label).                                                                                                       | ⬜      |
| 2.4 | Doc: how to run full scan on file + SQL + NoSQL fixtures and compare to manifest; optional precision/recall script.                                                        | ⬜      |

### Phase 3: Network shares and connectivity scenarios

| #   | To-do                                                                                                                                                                                         | Status |
| --- | ---------------------------------------------------------------------                                                                                                                         | ------ |
| 3.1 | Document or script minimal SMB/NFS/WebDAV server with sample files (or point to existing test env); add share fixtures to manifest.                                                           | ⬜      |
| 3.2 | Timeout/connectivity: doc “Troubleshooting” (solve: timeouts, retries, network; prevent: config timeouts, off-peak). Extend failure_hint or report with “Prevent next time” where applicable. | ⬜      |
| 3.3 | Optional: test or fixture that triggers timeout (e.g. mock slow target) and assert report shows timeout hint and guidance.                                                                    | ⬜      |

### Phase 4: Confidence bands and operator guidance in report

| #   | To-do                                                                                                                                                                                                                 | Status |
| --- | ---------------------------------------------------------------------                                                                                                                                                 | ------ |
| 4.1 | Define confidence bands (e.g. probably_nothing_serious, better_safe_than_sorry, high_risk_verify, high_risk_ml_struggling) from sensitivity_level + pattern_detected + ml_confidence (and optional validation FP/FN). | ⬜      |
| 4.2 | Map each band to operator guidance text: manual verification steps, tuning (regex_overrides, ml_patterns_file, sample_limit, timeouts), and link to docs.                                                             | ⬜      |
| 4.3 | Add “Discovery confidence” (and optionally “Operator guidance”) to report: new column in findings sheets or new section/sheet; recommendations sheet can reference bands.                                             | ⬜      |
| 4.4 | Docs: USAGE or new “Operator guidance” doc describing bands and how to manually verify and tune; EN + pt_BR.                                                                                                          | ⬜      |
| 4.5 | Tests: assert report contains confidence or guidance when run on fixture with known FP/FN; no regression.                                                                                                             | ⬜      |

### Phase 5: Validation scoring and recommendations

| #   | To-do                                                                                                                                       | Status |
| --- | ---------------------------------------------------------------------                                                                       | ------ |
| 5.1 | Optional script: run scan on full fixture set, compare to manifest, output precision/recall/F1 and per-pattern stats; can be run on-demand. | ✅ Done (`scripts/validate_detection_f1.py`; baseline in [VALIDATION.md](../VALIDATION.md)) |
| 5.2 | Document how to use fixture set and scoring to tune config (add regex, ML terms, adjust min_sensitivity) and re-run to improve.             | ⬜ Pending |
| 5.3 | Update PLANS_TODO.md and this plan; ensure “timeouts and connectivity” and “manual verify / tune” are in operator-facing docs.              | 🔄 Partial — plan + PLANS_TODO + VALIDATION for Phase 1/5.1; timeouts guidance still Phase 3 |

---

## Far horizon (H3/H4) — federated calibration research ([#1067](https://github.com/DataBoar/data-boar/issues/1067))

Off-band readonly review of privacy-preserving ML stacks (e.g. OpenMined/PySyft). **Pattern registration only** — **no roadmap commitment**, no new dependencies, no FL/DP code.

**Hypothetical Enterprise scenario:** if we ever improve ML/DL **calibration** (confidence thresholds, FN reduction) by aggregating **signals across multiple Enterprise customers** without centralising anyone’s raw data, **federated learning** with proper **differential privacy composition** is the architecturally correct shape. Natural packaging candidate: `dbtier: enterprise` (“cross-tenant model improvement with provable isolation”).

> **Technical caveat (do not simplify):** PySyft alone is **not** ready-made differential privacy. Real DP requires composition with **Opacus** (PyTorch) or TF-Privacy on the training path. Treat PySyft as an **architectural reference**, not a drop-in privacy dependency.

**Adjacent academic framing (operator thesis context, no repo action):** static dataset anonymisation (e.g. k-anonymity / l-diversity tooling such as ARX) and federated training address **different** privacy-engineering stages; Data Boar’s deterministic discovery stack remains a **third category** (inventory of where sensitive data lives).

---

## Dependencies and constraints

- **Fixtures are optional:** Main app and default tests do not depend on the full synthetic dataset; it is for validation and operator training. CI can run a subset if desired.
- **No secrets in fixtures:** Use only synthetic or anonymised data; no real PII in repo.
- **Confidence and guidance are additive:** Existing report columns and recommendation logic remain; new columns or section add information only.

---

## Conflict and placement in roadmap

- **No conflicts** with other plans. Additive (fixtures, manifest, report columns/section, docs).
- **Placement:** Independent; can follow or run in parallel with Compliance samples or Selenium QA. See [PLANS_TODO.md](PLANS_TODO.md).

---

## Changelog

- **2026-08-27:** v1.8.0 survey **[#1060](https://github.com/DataBoar/data-boar/issues/1060)** — composite eval axes (F1 + latency + throughput + re-id **privacy** risk); citation contract; no new published numbers in this PR.
- **2026-03-15:** Initial plan — synthetic/true-like fixtures, confidence bands, operator guidance; later #835 Phase 1 + 5.1 F1 harness.

---

## v1.8.0 wave — composite eval, not F1-only ([#1060](https://github.com/DataBoar/data-boar/issues/1060))

**Driver:** Landscape survey (private competitive dossier). **Docs-first** in this PR. This wave defines **what to measure** and **how to compare**. It does **not** publish a new result table, a new harness, or a fused ranking score.

**Thesis (do not dilute):** **System ranking changes when you measure only F1.** A detector that wins F1 and loses an **order of magnitude** on throughput is not “better” — it is a **different trade-off**. One-dimension eval produces a **false ordering**.

**Non-claims:** Inventory and scores here are **evidence**, not a legal conclusion ([ADR 0025](../adr/ADR-0025-compliance-positioning-evidence-inventory-not-legal-conclusion-engine.md)). Re-id risk is **not** a compliance seal. This PR restates **no** F1, latency, or speedup figures — those live only in their pinned artifacts if cited later.

### What already ships (do not invent a second lab)

| Surface | Role today | #1060 axis |
| ------- | ---------- | ---------- |
| [VALIDATION.md](../VALIDATION.md) | **F1 baseline methodology** (issue shorthand `F1_BASELINE_METHODOLOGY` — there is no separate file with that name): splits, anti-leakage, `tests/data/f1_validation/` + `scripts/validate_detection_f1.py` | **F1 / P / R** only; published numbers stay in that doc |
| This plan Phases 1 + 5.1 | Labeled synthetic text fixtures + on-demand F1 script | Accuracy axis already specified |
| [PLAN_SYNTHETIC_DATA_LAB.pt_BR.md](PLAN_SYNTHETIC_DATA_LAB.pt_BR.md) + [ADR-0007](../adr/ADR-0007-synthetic-data-corpus-before-real-data.md) | Lab corpus **before** real data; pseudo-anonymisation / residual re-id **exercises** | **Re-id risk** lab track — still not a fused score |
| Quasi-identifier aggregation (report sheet) | Heuristic **inventory** of combinations | Input to a **privacy** metric later; not F1 |
| [PLAN_BENCHMARK_SAFE_AXIS.md](PLAN_BENCHMARK_SAFE_AXIS.md) + `tests/benchmarks/README.md` | Wall-clock / recall **gates** with **benchmark id** | **Latency / throughput** only when cited from pinned JSON |
| [PLAN_CLAIMS_CONSISTENCY_AND_ANTI_OVERCLAIM.md](PLAN_CLAIMS_CONSISTENCY_AND_ANTI_OVERCLAIM.md) | Claims must be `backed_by` | Same rule for any future composite write-up |

### Four axes (report separately — never one scalar)

| Axis | Kind | What it answers | Must not |
| ---- | ---- | ---------------- | -------- |
| **F1** (with P/R) | Detection quality vs labeled synthetic truth | Did we flag the right rows/files on **this** split? | Stand in for speed or privacy |
| **Latency** | Performance | Time to a defined unit (e.g. batch, file, session) | Be compared across unmatched scopes |
| **Throughput** | Performance | Work per unit time on a defined load | Be inferred from F1 |
| **Re-id risk** | **Privacy**, not quality | How much the **system’s outputs** help re-identify a data subject | Be added to F1 in a single “overall” score that hides the trade-off |

A future dashboard may show **four columns** (or a Pareto / radar view). It must **not** collapse them into one number that re-ranks systems as if F1 were the whole story.

### Citation contract (every published number)

A number without **scope** is the defect this repo already forbids. Any later write-up **must** carry, together:

1. **Scope** — isolated filter vs connector vs end-to-end scan (these are not interchangeable).
2. **Pinned artifact** under `tests/benchmarks/` (or the F1 publish path in [VALIDATION.md](../VALIDATION.md) for accuracy-only).
3. **`benchmark` id** matching `tests/benchmarks/README.md` for that exact scope (do not reuse a hotspot id for an E2E claim).
4. **`git_sha`** of the tree that produced the artifact.
5. **Date** of the run (UTC).

This wave **does not** quote ratios from those files. Do **not** paste scar-class marketing speedups (including Rust prefilter headlines) or claims of total FP elimination. If a future PR needs a value, **open the pinned JSON** and copy only with the tuple above.

### Re-id risk (privacy dimension)

**Re-id risk** measures **privacy exposure**: the chance that a **titular** can be re-identified from what the **product exposes** (findings, samples, aggregates, reports) — **not** “how accurate is the detector.”

- Do **not** treat a high F1 as low re-id risk (a thorough detector can **increase** residual identifiability of outputs if samples leak).
- Do **not** treat quasi-id Excel flags as a scored k-anonymity proof; they are **heuristic inventory** ([GLOSSARY.md](../GLOSSARY.md) quasi-identifier row).
- Lab work for **controlled** residual re-id stays on [PLAN_SYNTHETIC_DATA_LAB.pt_BR.md](PLAN_SYNTHETIC_DATA_LAB.pt_BR.md) / ADR-0007 — still **synthetic only** in git.

### Execution table (doc-first → later slices)

| Step | Deliverable | Status |
| ---- | ----------- | ------ |
| P1 | This plan section + hub summary + `PLANS_TODO` survey rows | ✅ Done (docs PR) |
| P2 | Operator checklist: four axes + citation tuple (USAGE or VALIDATION addendum — no new numbers) | ⬜ Pending |
| P3 | Optional harness extension: emit latency/throughput **fields** beside F1 on the same labeled run (still no fused score) | ⬜ Pending |
| P4 | Re-id risk **protocol** on synthetic lab outputs (privacy metric spec; not a legal conclusion) | ⬜ Pending |

---

## Last updated with plan file. Update PLANS_TODO.md when completing or adding to-dos.
