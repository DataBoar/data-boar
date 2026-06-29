# Plan: Additional detection techniques and false-negative reduction

**Status:** Completed (priorities 1–11 POC on `main`); **v1.8.0 slice active** ([#1056](https://github.com/FabioLeitao/data-boar/issues/1056))
**Date:** 2026-03-15 (v1.8.0 wave: 2026-06-21)
**Authors:** Fabio Leitao
**Priority:** H2
**Milestone:** v1.8.0
**GitHub:** [#1056](https://github.com/FabioLeitao/data-boar/issues/1056)
**Depends on:** ADR-0043 · optional: [PLAN_YAML_PLUGIN_SYSTEM.md](PLAN_YAML_PLUGIN_SYSTEM.md) (Phase 1b / [#865](https://github.com/FabioLeitao/data-boar/issues/865) registrable validators)

<!-- plans-hub-summary: POC priorities 1-11 on main; v1.8.0 #1056 adds entity taxonomy, country checksum gates, span-alignment, plugin validators; priorities 5-7 NER/dictionaries still backlog. -->
<!-- plans-hub-related: PLAN_EXTENDED_SENSITIVE_DISCOVERY_POSITIONING.md, PLAN_YAML_PLUGIN_SYSTEM.md, PLAN_SYNTHETIC_DATA_AND_CONFIDENCE_VALIDATION.md -->

**Goal:** Explore techniques, frameworks, and libraries (beyond Regex, ML, and DL) to improve report quality, with emphasis on **reducing false negatives** (missed PII) even at the cost of more false positives (which can be handled later by human review).

---

## Current detection stack (recap)

| Layer     | Technology                                                                    | Role                                                                                              |
| -------   | ------------                                                                  | ------                                                                                            |
| **Regex** | Built-in + `regex_overrides_file`                                             | Strong pattern match (CPF, SSN, email, credit card, etc.) → HIGH. Runs first.                     |
| **ML**    | TF-IDF + RandomForest (`ml_patterns_file` / `sensitivity_detection.ml_terms`) | Column name + sample text → confidence 0–100; thresholds 70→HIGH, 40→MEDIUM.                      |
| **DL**    | Sentence-transformers + LogisticRegression (`dl_patterns_file` / `dl_terms`)  | Semantic similarity on same (text, label) terms; confidence combined with ML via **max(ml, dl)**. |

Combined logic: regex wins when matched; otherwise `combined_confidence = max(ml_confidence, dl_confidence)`; ambiguous column names (e.g. `doc_id`) → MEDIUM + PII_AMBIGUOUS with “confirm manually”. Entertainment context (lyrics/tabs) and weak patterns are downgraded to reduce false positives.

---

## Principles

- **False negatives are worse than false positives** in this context: missed PII can lead to compliance gaps and regulatory punishment; extra findings can be reviewed by a human. **Balance: prefer a few false positives and ask for human confirmation rather than a false negative and a violation we missed.**
- **When inferring from incomplete or aggregated data**, bias toward flagging for human confirmation rather than dismissing. Regulatory risk of a missed violation outweighs the cost of extra review.
- New techniques should be **additive** where possible (optional engines, config flags) so existing deployments are unchanged.
- Any new path must be **verifiable**: we need a way to measure FN/FP (e.g. synthetic fixtures with ground truth, or spot audits).
- Prefer **simple, explainable** additions first; heavier AI/APIs only if justified by measurable FN reduction.

---

## Additional techniques (beyond Regex, ML, DL)

### 1. Rule-based / knowledge expansion (low risk, high value)

| Technique                               | Description                                                                                                | FN reduction idea                                                              | FP risk                                      | Feasibility                                                                                               |
| -----------                             | -------------                                                                                              | -------------------                                                            | ---------                                    | -------------                                                                                             |
| **Synonym / alias lists**               | Expand ML/DL terms with regional synonyms and nicknames (e.g. “carte bleue”, “doc_id” → confirm manually). | Catch columns named with local or informal terms.                              | Low if terms are scoped (e.g. ID-like only). | ✅ Already partially in place (DEFAULT_ML_TERMS, AMBIGUOUS_COLUMN_TOKENS). Extend via config.              |
| **Column-name dictionaries per region** | Optional YAML: locale/region → list of (column_name_pattern, category).                                    | Better coverage for FR, DE, ES, PT-BR, etc., without bloating global ML terms. | Low.                                         | ✅ Config-driven; no code change to detector logic beyond loading and applying.                            |
| **Stemming / normalisation**            | Normalise column names (e.g. stem, remove accents) before ML/vocabulary match.                             | “telefones”, “telefoni” → match “telefone”.                                    | Slight (similar tokens might collide).       | ✅ Use a small library (e.g. `stemming`, or simple strip-accents); apply only to column name for matching. |

**Recommendation:** Prioritise **region-specific column dictionaries** and **stemming/normalisation** for column names; keep as optional config so default behaviour is unchanged.

---

### 2. Fuzzy and typo-tolerant matching (medium value)

| Technique                     | Description                                                                                                                             | FN reduction idea                           | FP risk                                                    | Feasibility                                                                                                               |
| -----------                   | -------------                                                                                                                           | -------------------                         | ---------                                                  | -------------                                                                                                             |
| **Fuzzy column name match**   | Compare column name to sensitive terms with edit distance or token overlap (e.g. `rapidfuzz`, `python-Levenshtein`).                    | “documnet_id”, “telefone_cel” → still flag. | Medium (generic names like “id” could match).              | ✅ Optional post-step: if ML/DL confidence &lt; threshold but fuzzy score above a limit → MEDIUM “possible PII – confirm”. |
| **Token/substring allowlist** | Flag columns that contain tokens from a small “suspicious” set (e.g. “cpf”, “email”, “phone”) even with typo (e.g. “emial”, “telefne”). | Catches typos in column names.              | Medium; constrain to known PII tokens and high similarity. | ✅ Same as above; use high similarity threshold to limit FP.                                                               |

**Recommendation:** Add an **optional** “fuzzy column match” step: only when **no** regex match and ML/DL confidence in a band (e.g. 25–45). If column name is very similar to a known sensitive term → MEDIUM with pattern e.g. `FUZZY_COLUMN_MATCH`. Library: `rapidfuzz` (optional dependency).

---

### 3. Schema and metadata signals (low FP, good for FN)

| Technique                            | Description                                                                                  | FN reduction idea                                                                                             | FP risk                                                          | Feasibility                                                                                                            |
| -----------                          | -------------                                                                                | -------------------                                                                                           | ---------                                                        | -------------                                                                                                          |
| **Data type + length heuristics**    | e.g. String length in “typical CPF/email range”, or “all digits” + length.                   | Suggest “possible identifier” when format is plausible even if regex didn’t match (e.g. masked or malformed). | Low if used only to **suggest** MEDIUM / review.                 | ✅ Connectors already have sample values; add optional “format hint” (digits_only, length, etc.) to detector or report. |
| **Foreign key / table name context** | If column is FK to a “users” / “people” table, or table name suggests “customer”, “patient”. | Elevate confidence or add “possible PII” when context suggests person-related.                                | Low if we only **boost** existing MEDIUM or add a “review” flag. | ⚠️ Requires schema/metadata from connector (SQL already has this; filesystem would need conventions).                  |
| **Uniqueness / cardinality**         | High uniqueness (e.g. unique count ≈ row count) on a string column.                          | Columns that behave like identifiers but have generic names could be flagged for review.                      | Medium (many non-PII columns are unique).                        | ⚠️ Needs extra scan or statistics; possible as optional “post-scan” or second pass.                                    |

**Recommendation:** Start with **data type + length** as an optional hint (e.g. “looks like numeric id” or “length consistent with email”) and use it only to **suggest MEDIUM** or “confirm manually”. FK/table context is high value where available (SQL); document as optional enhancement for connectors that can expose schema.

---

### 4. Ensemble and voting (maximise recall)

| Technique                    | Description                                                                                                                                                              | FN reduction idea                                     | FP risk                                                      | Feasibility                                                                                                                                      |
| -----------                  | -------------                                                                                                                                                            | -------------------                                   | ---------                                                    | -------------                                                                                                                                    |
| **“Any engine says HIGH”**   | Today we already use max(ml_confidence, dl_confidence). Extend: if **any** optional engine (e.g. fuzzy, format hint) says “sensitive”, combine with OR or weighted vote. | Reduces FN when one engine misses.                    | Higher FP by design; acceptable if human review is in place. | ✅ Design: add optional engines that return a 0–100 score or a boolean “suggest_sensitive”; combine with existing combined_confidence (e.g. max). |
| **Lower MEDIUM threshold**   | e.g. 35 instead of 40 for MEDIUM.                                                                                                                                        | More borderline cases get human review.               | More MEDIUM findings.                                        | ✅ Single config knob (e.g. `sensitivity_detection.medium_confidence_threshold`).                                                                 |
| **“Suspicious column” list** | Columns matching heuristics (e.g. `*_id`, `*_num`, `*_number`) that were classified LOW → optional second pass or flag in report as “Suggested review”.                  | Surfaces possible identifiers that no engine flagged. | Low if we only **suggest** and do not change LOW to HIGH.    | ✅ Report-only or optional second pass with stricter ML/term list.                                                                                |

**Recommendation:** Implement **configurable MEDIUM threshold** and a **“suggested review”** list in the report (columns that look like IDs but got LOW) as low-effort, high-transparency improvements. Keep “any engine says HIGH” as the existing max(ml, dl) and document that adding more engines will follow the same “max” policy to avoid FN.

---

### 5. NLP / NER and external APIs (higher effort, optional)

| Technique                                           | Description                                                                                                                    | FN reduction idea                                                  | FP risk                                      | Feasibility                                                                                            |
| -----------                                         | -------------                                                                                                                  | -------------------                                                | ---------                                    | -------------                                                                                          |
| **Named-entity recognition (NER)**                  | Use a pre-trained NER model (e.g. spaCy, or a small transformer) on **sample values** to detect person names, locations, orgs. | Catch names and other entities in free text that ML/DL might miss. | Medium (fiction, place names).               | ⚠️ Optional extra dependency; run only on sample text; best as **optional** engine with config switch. |
| **Presidio or similar PII APIs**                    | Call external or local Presidio (or AWS Comprehend, etc.) on sample text.                                                      | Strong at structured PII in text.                                  | Depends on API; usually tuned for precision. | ⚠️ Network/local API; privacy and latency; good for “audit mode” or optional enrichment.               |
| **Embedding similarity to a “sensitive” prototype** | One vector per category (e.g. “PII”, “health”) from DL embedder; compare column+sample embedding to prototypes.                | Semantic match without training a classifier.                      | Medium.                                      | ✅ Reuse existing sentence-transformers embedder; no new deps; optional.                                |

**Recommendation:** **Embedding prototype similarity** is the most aligned with current stack (reuse DL embedder); add as optional “semantic hint” that can elevate MEDIUM. NER and Presidio: document as **future options** and implement only if FN metrics justify (e.g. after synthetic fixtures and validation).

---

### 6. Human-in-the-loop and continuous improvement

| Technique                                   | Description                                                                                                                                          | FN reduction idea                           | FP risk   | Feasibility                                                                                                                        |
| -----------                                 | -------------                                                                                                                                        | -------------------                         | --------- | -------------                                                                                                                      |
| **Uncertainty sampling**                    | Flag findings in confidence band (e.g. 40–60) for “operator review”; use confirmations/corrections to feed back into ML/DL terms (learned_patterns). | Improves future runs.                       | N/A.      | ✅ Already have learned_patterns; add explicit “uncertainty” band in report and doc “merge learned_patterns into ml_patterns_file”. |
| **Ground-truth fixtures and FN/FP metrics** | Synthetic (and optionally real) datasets with labels; run detector and compute precision/recall per pattern or per run.                              | Drives which techniques actually reduce FN. | N/A.      | ✅ See PLAN_SYNTHETIC_DATA_AND_CONFIDENCE_VALIDATION.md; use same fixtures to validate new engines.                                 |

**Recommendation:** Treat **learned_patterns** and **ground-truth validation** as the backbone for measuring and improving FN: any new technique should be evaluated on the same fixtures and show a measurable recall improvement.

---

## Inference on aggregated and incomplete data

We already infer personal or sensitive data under LGPD/GDPR/CCPA etc. from an **incomplete set**: column names plus a **sample** of values (e.g. `sample_limit` rows), not the full population. Aggregation then groups findings by table or file and infers **“possible identification”** when multiple quasi-identifier categories (gender, health, phone, address, other) appear together in the same group. That inference is therefore uncertain: we may miss columns that are PII but didn’t show up in the sample, or we may under-count categories and miss a high-risk combination.

## Policy for aggregated and incomplete inference:
Prefer **more false positives and human confirmation** over **false negatives and regulatory punishment**. When in doubt, flag as “possible” / “suggested review” so the operator can confirm, rather than dismissing and risking a violation.

### Tactics to improve aggregated/incomplete inference (FN‑first balance)

| Tactic                                                       | Description                                                                                                                                                                                                                                                                                                                                                  | FN reduction                                                                                                                                               | FP impact                                                                                  |
| --------                                                     | -------------                                                                                                                                                                                                                                                                                                                                                | ---------------                                                                                                                                            | -----------                                                                                |
| **Conservative category mapping**                            | When a finding could map to more than one quasi-identifier category, or the pattern is weak/ambiguous, still map it to at least one category (e.g. `other`) so it counts toward aggregation. Avoid “no category” when the column name or pattern is suggestive.                                                                                              | Tables with borderline columns still get flagged if they reach min_categories.                                                                             | Slight: more groups may reach threshold.                                                   |
| **Lower bar when data is incomplete**                        | Optional config: when `sample_limit` is low or coverage is known partial (e.g. only some tables scanned), allow **lower `aggregated_min_categories`** (e.g. 1 for high-risk categories like health) or a dedicated “incomplete data” mode that flags more groups as “suggested review”.                                                                      | Reduces FN when we have few samples per column.                                                                                                            | More aggregated rows; report should state “based on incomplete sample – confirm manually”. |
| **Single high-risk category can trigger “suggested review”** | Optionally, when a group has only one category but it is high-risk (e.g. health, or multiple columns in “other” that look like identifiers), still produce a row with sensitivity “suggested review” or MEDIUM so the operator sees it.                                                                                                                      | Catches tables that would otherwise need exactly two categories but only one was detected due to incomplete data.                                          | Configurable; report wording clarifies “possible” risk.                                    |
| **Report wording and transparency**                          | In the “Cross-referenced data – possible identification” sheet and recommendations, state explicitly that results are **based on sampled/incomplete data** and **human confirmation is recommended**. Use “possible”, “suggested”, “may allow identification” so we never imply certainty when we only had a sample.                                         | Builds trust and ensures operators don’t treat low-sample findings as definitive; reduces risk of acting as if we had no PII when we might have missed it. | None.                                                                                      |
| **Include MEDIUM and PII_AMBIGUOUS in aggregation**          | Ensure findings classified as MEDIUM or pattern PII_AMBIGUOUS still contribute to category mapping (e.g. map to `other`) and count toward `min_categories`. Do not exclude them from aggregation.                                                                                                                                                            | Avoids missing a table that only had “doc_id”‑style columns and no strong regex match.                                                                     | Already aligned with “confirm manually”; may add more aggregated rows.                     |
| **Optional “incomplete data” mode**                          | Config flag (e.g. `detection.aggregated_incomplete_data_mode: true`): when set, (1) use a lower threshold for per-column MEDIUM for aggregation purposes only, and/or (2) lower `aggregated_min_categories` by 1 (min 1), and (3) add a note in the report that findings are based on incomplete data and all flagged groups should be confirmed by a human. | Maximises recall when the operator knows coverage is partial.                                                                                              | More findings; acceptable under the FN‑first balance.                                      |

**Recommendation:** Implement **report wording and transparency** first (no logic change, just text). Then ensure **MEDIUM and PII_AMBIGUOUS contribute to aggregation** (already the case if they map to a category; verify and document). Add **optional “incomplete data” mode** and **single high-risk category “suggested review”** as config-driven options so deployments that must minimise regulatory risk can opt in.

---

## Implementation priorities (recommended order)

1. **Configurable MEDIUM threshold** and **“suggested review”** (report) for ID-like columns classified LOW — minimal code, immediate value.
1. **Stemming/normalisation** for column names in ML/term matching — **done (slice 2):** optional `sensitivity_detection.column_name_normalize_for_ml` applies **accent folding + separator normalisation** to the column name **for ML/DL input only** (`core/column_name_normalize.py`); not full Porter stemming. See `docs/SENSITIVITY_DETECTION.md`.
1. **Optional fuzzy column name match** (e.g. rapidfuzz), only in 25–45 confidence band, → MEDIUM + FUZZY_COLUMN_MATCH — **done:** `sensitivity_detection.fuzzy_column_match` + optional extra `detection-fuzzy`; see `docs/SENSITIVITY_DETECTION.md`, `core/fuzzy_column_match.py`.
1. **Data type / length hint** from connectors → optional “format hint” in detector and MEDIUM suggestion when format suggests identifier but no regex hit — **done:** `sensitivity_detection.connector_format_id_hint` + `FORMAT_LENGTH_HINT_ID` / `FORMAT_TYPE_HINT_ID_INT` / `FORMAT_LENGTH_HINT_EMAIL`; SQL `CHAR`/`VARCHAR(N)` length parsed from connector metadata; conservative name heuristics (CPF/CNPJ/SSN; **UUID** `VARCHAR(36)` / hex `VARCHAR(32)` when column name contains `uuid`, `guid`, or `uniqueidentifier`); wired through `DataScanner.scan_column` / SQL, Snowflake, Dataverse, Power BI, SQLite-in-file path in filesystem connector. **Email-length hint** extended to common schema sizes (**128, 191, 254, 255, 256, 320**) with existing email-like name tokens. **REST/API** connector passes inferred `VARCHAR(n)` / `BIGINT` from JSON scalar samples (`connectors/rest_connector.py`). Optional further work: MongoDB/Redis key-value typing hints if needed.
1. **Embedding prototype similarity** (reuse DL embedder) as optional “semantic hint” to elevate MEDIUM.
1. **Region-specific column dictionaries** (config) and, where connector supports it, **FK/table context**.
1. NER / Presidio as **optional, documented** extensions once fixtures and FN metrics are in place.

## Aggregated and incomplete-data inference (FN-first balance)

1. **Report wording and transparency**: in aggregated sheet and recommendations, state that results are based on sampled/incomplete data and human confirmation is recommended; use "possible", "suggested", "may allow identification".
1. **Verify MEDIUM and PII_AMBIGUOUS contribute to aggregation** (map to category and count toward min_categories); document behaviour.
1. **Optional "incomplete data" mode**: config flag to lower aggregated_min_categories when coverage is partial and add report note that all flagged groups should be confirmed by a human.
1. **Optional single high-risk category "suggested review"**: when a group has only one category but it is high-risk (e.g. health), still produce a row with "suggested review" so the operator sees it.

---

## Verification plan (how to confirm it works)

1. **Define a small ground-truth set**
   - Use or extend the synthetic/fixture approach from PLAN_SYNTHETIC_DATA_AND_CONFIDENCE_VALIDATION.
   - Include: clear PII (CPF, email, names), clear non-PII (counts, logs), and **intentional FN** (e.g. misspelled column names, masked values, regional nicknames).

1. **Baseline**
   - Run current detector (regex + ML + DL) on the set; record per-column sensitivity and pattern.
   - Compute recall (how many of the known PII columns were flagged as HIGH or MEDIUM).

1. **Per-technique validation**
   - Enable one new technique at a time (e.g. fuzzy match, or lower MEDIUM threshold).
   - Re-run and compare recall and precision.
   - Accept a technique if recall increases and precision stays acceptable (or FP are documented as “review”).

1. **Regression**
   - Ensure existing tests still pass; add tests for new code paths and for “no change when optional feature off”.

1. **Documentation**
   - Document each optional technique in `docs/SENSITIVITY_DETECTION.md`: when it runs, how to enable/disable, and how it affects FN/FP.

---

## Feasibility summary

| Approach                                                                                            | Feasible?   | Notes                                                                 |
| ----------                                                                                          | ----------- | --------                                                              |
| Rule-based / synonyms / region dictionaries                                                         | ✅ Yes       | Config and term list expansion; no new dependencies.                  |
| Stemming / normalisation                                                                            | ✅ Yes       | Small lib or minimal code; apply to column name only.                 |
| Fuzzy column match                                                                                  | ✅ Yes       | Optional dependency (rapidfuzz); clear band (e.g. 25–45) to limit FP. |
| Schema/metadata (type, length, FK)                                                                  | ✅ Partially | Type/length: yes. FK/table: only where connectors expose schema.      |
| Ensemble (max, lower threshold, “suggested review”)                                                 | ✅ Yes       | Config and report changes.                                            |
| Embedding prototype similarity                                                                      | ✅ Yes       | Reuse DL embedder; optional.                                          |
| NER / Presidio                                                                                      | ⚠️ Later    | Optional; validate with fixtures first.                               |
| Aggregated / incomplete-data inference (conservative mapping, incomplete-data mode, report wording) | ✅ Yes       | Config and report text; optional lower bar when data is incomplete.   |

Overall: **yes, it is possible** to add several techniques that improve quality and reduce false negatives. The safest and most measurable path is: (1) configurable thresholds and “suggested review”, (2) stemming and optional fuzzy match, (3) format/schema hints, (4) embedding prototype, (5) region dictionaries and FK context; then NER/APIs if metrics justify.

---

## Libraries and frameworks (concrete options)

| Purpose                  | Library / framework                                                                                         | Notes                                                                                            |
| --------                 | ----------------------                                                                                      | --------                                                                                         |
| Fuzzy string match       | `rapidfuzz`                                                                                                 | Optional dep; use for column name vs sensitive term similarity (e.g. fuzz.ratio, partial_ratio). |
| Edit distance            | `python-Levenshtein`                                                                                        | Alternative or complement to rapidfuzz; optional.                                                |
| Stemming / normalisation | `stemming` (e.g. `stemming.porter2`) or `nltk.stem`, or simple strip-accents (e.g. `unicodedata.normalize`) | For column names only; keep dependency minimal.                                                  |
| NER (future)             | `spaCy` (e.g. `en_core_web_sm`) or Hugging Face NER                                                         | Optional; run on sample text only; config switch.                                                |
| PII detection API        | Microsoft Presidio, AWS Comprehend                                                                          | Optional; privacy/latency; “audit mode” or enrichment only.                                      |
| Embeddings (current DL)  | `sentence-transformers`                                                                                     | Already used; reuse for prototype similarity (no new dep).                                       |
| ML (current)             | `scikit-learn` (TF-IDF, RandomForest)                                                                       | No change.                                                                                       |

All new dependencies should be **optional** (extras in pyproject.toml, e.g. `[detection-fuzzy]`) so default install and CI remain light.

---

## v1.8.0 wave — competitive survey entity taxonomy ([#1056](https://github.com/FabioLeitao/data-boar/issues/1056))

**Driver:** Landscape survey (private competitive dossier, 2026-06). **Docs-first** in this PR; implementation follows in thin code PRs with the same compliance-sample discipline as existing `docs/compliance-samples/compliance-sample-*.yaml` packs.

**Non-claims (align with [COMPLIANCE_AND_LEGAL.md](../COMPLIANCE_AND_LEGAL.md)):** `norm_tag` values and recommendation text are **inventory and technical-mapping aids** — not legal advice, not a determination that a matched string is personal data in your jurisdiction, and not proof of regulatory compliance. Operators tune overrides with counsel; checksum gates **reduce false positives** on shape-only hits; they do **not** prove validity for enforcement purposes.

### Execution table (doc-first → code slices)

| Step | Deliverable | Status |
| ---- | ----------- | ------ |
| D1 | This plan section + [PLAN_EXTENDED_SENSITIVE_DISCOVERY_POSITIONING.md](PLAN_EXTENDED_SENSITIVE_DISCOVERY_POSITIONING.md) wave 2; `plans_hub_sync` + `PLANS_TODO` | ✅ Done (docs PR) |
| D2 | Sketch `docs/compliance-samples/compliance-sample-global_identifiers.yaml` (or extend existing packs): `regex` rows + `recommendation_overrides` + header disclaimers | ⬜ Pending |
| D3 | Built-in or override entity-types: SWIFT/BIC, IBAN, VIN, MAC, CVV/expiry (separate from PAN), AWS access/secret key shapes, PIN — distinct `pattern` names in `DEFAULT_PATTERNS` / overrides | ⬜ Pending |
| D4 | Country checksum validators: UK NHS (final-digit checksum); CA SIN (Luhn) — **format matches but DV fails → suppress** (same contract as CPF Mod-11 in `core/brazilian_cpf.py`) | ⬜ Pending |
| D5 | Span-alignment post-process in `boar_fast_filter` (Rust): multi-token entities (e.g. compound names) emit as one contiguous span | ⬜ Pending |
| D6 | Registrable checksum/validator hooks via Plugin SDK ([#865](https://github.com/FabioLeitao/data-boar/issues/865)) + `plugin_schema` extension (coordinate with `PLANS_TODO` **S4b**) | ⬜ Pending |
| D7 | `docs/SENSITIVITY_DETECTION.md` FP-scope note for new digit-heavy patterns; tests + `check-all` | ⬜ Pending |

### Entity-types to distinguish (today generic or absent)

| Entity | Detection intent | `norm_tag` / framing | FP-scope note |
| ------ | ---------------- | -------------------- | --------------- |
| **SWIFT/BIC** | Bank identifier (8 or 11 chars) | PCI / financial inventory or sector override | Not account numbers; validate BIC structure where implemented |
| **IBAN** | International bank account | GDPR / PSD2-adjacent inventory | Country check digits; suppress on failed mod-97 when validator ships |
| **VIN** | Vehicle identifier (17 chars) | Sector / motor registry hints | Exclude I/O/Q; checksum digit where applicable |
| **MAC** | Hardware address | Security / asset inventory | High FP in logs and hex dumps — prefer context or length bounds |
| **CVV / expiry** | Card security code / expiry (not PAN) | PCI-DSS sample alignment | **Separate** from `CREDIT_CARD` / Luhn PAN path ([compliance-sample-pci_dss.yaml](../compliance-samples/compliance-sample-pci_dss.yaml)) |
| **AWS access / secret keys** | Cloud credential shapes | Secrets / security artifact (see extended discovery plan) | Pair with extended discovery positioning; not exhaustive vs dedicated secret scanners |
| **PIN** | Short numeric secrets | PCI / auth inventory | Very high FP on counters and ordinals — checksum or context gate required |

Secrets and IP column semantics stay aligned with [PLAN_EXTENDED_SENSITIVE_DISCOVERY_POSITIONING.md](PLAN_EXTENDED_SENSITIVE_DISCOVERY_POSITIONING.md) (wave 2 table).

### Country checksum gates (suppress shape-only false positives)

Follow the **CPF Mod-11** precedent documented in [SENSITIVITY_DETECTION.md](../SENSITIVITY_DETECTION.md): regex (or plugin) may match **shape**; an optional validator runs **after** match; **invalid check digit → drop finding** (not downgrade to LOW).

| Identifier | Gate | Reference pattern |
| ---------- | ---- | ----------------- |
| **BR CPF** | Modulo-11 | `core/brazilian_cpf.py` (`cpf_checksum_valid`) — shipped for lab/contracts; wire into detector path in implementation slice |
| **UK NHS number** | Checksum on final digit | Compliance-sample row + registrable validator ([#865](https://github.com/FabioLeitao/data-boar/issues/865)) |
| **CA SIN** | Luhn | Extend [compliance-sample-pipeda.yaml](../compliance-samples/compliance-sample-pipeda.yaml) `SIN_CA` with validator gate (shape already present; Luhn reduces FP on random 9-digit runs) |

### Span-alignment (multi-token entities)

**Problem:** Fast prefilter may emit adjacent token hits (e.g. given + family name) as separate spans; reports and aggregation treat them as unrelated.

**Direction:** Post-processing in `boar_fast_filter` merges compatible adjacent spans into one **entity span** before Python detector enrichment. Configurable gap (whitespace/punctuation) and category allowlist; default off until benchmarks show FN reduction without report noise.

### Compliance-sample methodology (mandatory for new patterns)

1. Add rows to `regex:` with explicit `name`, `pattern`, `norm_tag` (framework label — **not** legal conclusion).
2. Merge matching bullets into `report.recommendation_overrides` in operator config (see sample file footers).
3. File header: operator must merge overrides; counsel reviews production patterns.
4. Document digit-heavy patterns under **Generic digit patterns and false-positive scope** in [SENSITIVITY_DETECTION.md](../SENSITIVITY_DETECTION.md).
5. No weakening of built-in gates to pass CI; false positives → tighten pattern or add checksum gate ([ADR-0049](../adr/ADR-0049-no-brittle-mitigations-robust-input-handling.md)).

### Revisit (completed plans — survey notes only)

- [PLAN_SENSITIVE_CATEGORIES_ML_DL.md](completed/PLAN_SENSITIVE_CATEGORIES_ML_DL.md): optional taxonomy enrichment when entity-types above ship (ML/DL terms for `FINANCIAL_ID`, `VEHICLE_ID`, `NETWORK_ID` buckets) — **no reopen** unless operator promotes a new slice.
- [PLAN_CONTENT_TYPE_AND_CLOAKING_DETECTION.md](completed/PLAN_CONTENT_TYPE_AND_CLOAKING_DETECTION.md): hidden metadata (EXIF GPS = location), steg hints, anti-cloaking via pHash/bHash ([#884](https://github.com/FabioLeitao/data-boar/issues/884)) — **evaluate separately** from #1056; addendum only unless operator reopens.

---

## References

- [core/detector.py](../../core/detector.py) — Regex, ML, DL pipeline and thresholds.
- [core/dl_backend.py](../../core/dl_backend.py) — Sentence-transformers + classifier.
- [docs/SENSITIVITY_DETECTION.md](SENSITIVITY_DETECTION.md) — Current detection and config.
- [docs/plans/PLAN_SYNTHETIC_DATA_AND_CONFIDENCE_VALIDATION.md](PLAN_SYNTHETIC_DATA_AND_CONFIDENCE_VALIDATION.md) — Fixtures and confidence bands.
- [core/learned_patterns.py](../../core/learned_patterns.py) — Writing learned terms for ML.
- [core/aggregated_identification.py](../../core/aggregated_identification.py) — Quasi-identifier categories, mapping, and run_aggregation (grouping by table/file, min_categories).
- [core/aggregated_identification.py](../../core/aggregated_identification.py) — Quasi-identifier categories, mapping, and run_aggregation (grouping by table/file, min_categories).
