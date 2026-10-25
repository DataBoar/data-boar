# Next session — format hint follow-up (priority 4) + aggregated phases 8–11 (context)

**Intent:** Work **priority 4** first (incremental format hints + connectors), then **priority 5** (embedding semantic hint) in a later session. Phases **8–11** are a **different layer** (aggregation / incomplete-sample policy); schedule when you want **report/UX + config** without blocking product detection work.

**Deferred note (Option B):** Keep a follow-up slice for **config discoverability hardening** (where/how to set aggregated and embedding toggles in one place) if reviewers report onboarding friction. This is a docs-focused maintenance item and can be batched separately from detector/report behavior changes.

---

## Why phases 8–11 are called “aggregated / incomplete”

Two different stages in the pipeline:

| Stage                                                               | What it does                                                                                                                                                                     | Why “incomplete” matters                                                                                                                                |
| -----                                                               | --------------                                                                                                                                                                   | -------------------------                                                                                                                               |
| **Per-column detection** (regex, ML, DL, **format hints**)          | Classifies **each column** using **name + sample values** (and optional SQL type string).                                                                                        | You almost never scan **every** row — `sample_limit` means values are **incomplete** vs the full population.                                            |
| **Aggregated identification** (`core/aggregated_identification.py`) | Groups findings **by table/file** and asks: do **several quasi-identifier categories** together allow **re-identification** (“cross-referenced data – possible identification”)? | Uses **only what the scan already found**. If the sample missed a column or only one category surfaced, the **aggregate** can **under-represent** risk. |

Phases **8–11** don’t add new regex engines; they improve **honesty and recall on that second layer**: clearer **wording** (8), **counting** MEDIUM/ambiguous toward categories (9), **config** when the operator **knows** coverage is partial (10), and **single high-risk** “still show a row” (11). That’s why the plan groups them under **“Inference on aggregated and incomplete data”** — regulatory framing: **sampled data ≠ certainty**.

---

## Priority 4 follow-up — concrete actions (product / stars line first)

**Goal:** Extend `connector_format_id_hint` / `FORMAT_LENGTH_HINT_ID` without duplicating priority 5 (embeddings).

**Code anchors:** `core/detector.py` — `_parse_declared_char_length`, `_format_length_suggests_id_column`, and the block that returns `FORMAT_LENGTH_HINT_ID` (~L929–941). Callers pass `connector_data_type` from `DataScanner.scan_column` / connectors.

| Step   | Action                                                                                                                                                                                                                                                                                                     | Outcome                                       |
| ----   | ------                                                                                                                                                                                                                                                                                                     | -------                                       |
| **4a** | **Numeric / INT lengths:** Parse `INT`, `BIGINT`, `INTEGER`, `DECIMAL(p,s)` where useful (e.g. `BIGINT` for surrogate keys). Decide rule: e.g. only elevate when **name is ID-like** + type is integer-like (avoid flagging every `INT` counts column).                                                    | More schema signal for non-VARCHAR IDs.       |
| **4b** | **Email-length heuristics:** If declared length is in **email-typical ranges** (e.g. 254, 255, 320) **and** column name suggests email (`email`, `mail`, `e_mail`, locale variants), suggest MEDIUM / dedicated pattern tag (or reuse `FORMAT_LENGTH_HINT_ID` with distinct norm text — product decision). | Catches mail columns where regex didn’t fire. |
| **4c** | **More connectors:** Audit who passes `connector_data_type` into `analyze()` today (SQL, Snowflake, Dataverse, Power BI, SQLite-in-file path per plan). **List gaps** (e.g. Postgres-only paths, REST, CSV) and pass **declared type string** where metadata exists.                                       | Same detector logic, more coverage.           |
| **4d** | **Tests:** Extend `tests/test_format_length_hint.py` for new parsers and name heuristics; keep **conservative** FP bar.                                                                                                                                                                                    | Regression safety.                            |
| **4e** | **Docs:** `docs/SENSITIVITY_DETECTION.md` (+ pt-BR) — new sub-section under format hint; mention `connector_format_id_hint`.                                                                                                                                                                               | Operators know how to turn on and interpret.  |

**Done when:** New cases covered by tests; docs updated; plan table row for priority 4 updated to list what shipped in this slice.

---

## Phases 8–11 — concrete actions (tomorrow or a later day; lower-code first)

Recommended order (from plan): **8 → verify 9 → 10 → 11**.

| Phase  | Concrete action                                                                                                                                                                                                                                                                               | Explanation                                                                     |
| -----  | -----------------                                                                                                                                                                                                                                                                             | -----------                                                                     |
| **8**  | **Report wording:** In Excel **“Cross-referenced data – possible identification”** (and any parallel recommendations text), add explicit **sampled / incomplete** language: “possible”, “suggested”, “may allow identification”, “human confirmation recommended”.                            | **No logic change** — reduces legal/UX risk of over-certainty.                  |
| **9**  | **Verify MEDIUM + PII_AMBIGUOUS in aggregation:** Trace `aggregated_identification` category mapping; add or extend **unit tests** proving MEDIUM / `PII_AMBIGUOUS` map to a **quasi-identifier category** and **count** toward `aggregated_min_categories`. Document in code comment + plan. | Ensures borderline columns don’t **silently drop** from aggregation.            |
| **10** | **Optional “incomplete data” mode:** New config flag (e.g. `detection.aggregated_incomplete_data_mode`) — lower `aggregated_min_categories` for aggregation pass only and/or add **report banner** “based on incomplete coverage”.                                                            | For operators who **know** they only scanned part of the estate.                |
| **11** | **Single high-risk “suggested review”:** When a group has **one** category but it is **high-risk** (e.g. health), still emit a row or flag **suggested review** (config-gated).                                                                                                               | Avoids missing a table that only showed **one** sensitive signal in the sample. |

---

## After priority 4 — priority 5 (embedding prototype)

**Next major slice:** optional **semantic hint** using existing **DL embedder** to elevate borderline columns toward MEDIUM — see `PLAN_ADDITIONAL_DETECTION_TECHNIQUES_AND_FN_REDUCTION.md` § implementation priorities item **5**.

---

## Last updated: session planning note; not a substitute for `PLANS_TODO.md`.
