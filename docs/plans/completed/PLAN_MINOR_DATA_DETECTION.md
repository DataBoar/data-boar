# Plan: Detection and differential treatment of possible minor data

## Goal

Detect when gathered personal data may relate to **minors** (e.g. inferred from date of birth in samples) and treat it as **highest sensitivity**. Cross-reference with name, official documents (CPF, RG, etc.), and health information when available. When there is an indication of data from a minor, optionally perform a **full scan** of the relevant columns and adjacent information to confirm the condition and apply **differential treatment** in the report (LGPD Art. 14, GDPR Art. 8, consent of holder, etc.), surfacing it as more important than other findings.

## Principles (non-destructive, no regression)

- **Additive only:** New logic is optional (config or automatic but backward-compatible). Existing sensitivity levels (HIGH/MEDIUM/LOW) and report layout remain valid.
- **No performance regression:** Full-scan of columns for minor confirmation is optional and scoped (e.g. only when DOB suggests minor).
- **No weakening of security:** No storage of raw sample content; only metadata (e.g. possible_minor flag, norm_tag extension).
- **Tests:** New code paths covered by tests; existing tests must still pass.

---

## Approach (high level)

1. **Age from DOB**

   In the detector (or a dedicated post-step), identify DOB/age using **column names and sample text** in both **English and Brazilian Portuguese**, including **acronyms** (e.g. DOB, DDN, NASC, IDD, AGE). Parse **date-of-birth** from values (reuse DATE_DMY and similar; support DMY, YMD, MDY; see “DOB/age identification” below). For **numeric age** columns (name suggests “age”/“idade” or acronyms), compare value directly to threshold. Compute age from DOB as (reference date − DOB). If age &lt; 18 (or configurable threshold), treat as **possible minor**. See section **DOB/age identification: names, formats, acronyms** for name variations, formats, and acronyms.

1. **Highest sensitivity**

   Either:

   - Introduce a new level **CRITICAL** (or **MINOR**) ordered above HIGH in filters and reporting, or
   - Keep HIGH and add an optional **flag** (e.g. `possible_minor` / `minor_data_indicator`) on findings so reports can show “possible minor data” with highest priority.

   Recommendation: **flag** to avoid changing the existing three-level contract everywhere; report and filters treat “HIGH + possible_minor” as highest.

1. **Cross-reference**

   When a finding is DOB/age suggesting minor, **cross-reference** with:

   - Same row/record: name-like columns, official doc (CPF, RG, SSN), health-related columns.

   If the same logical record has DOB (minor) + name/doc/health, treat as **confirmed or high-confidence** “possible minor data” and ensure it is clearly prioritized in the report.

1. **Full scan when possible minor**

   When DOB/age suggests a minor, optionally:

   - **Full scan** of that column (all values, not only sample) to confirm presence of dates indicating minors.
   - **Scan adjacent columns** (same table: name, doc, health) to support cross-reference.

   This may require connector/engine support (e.g. “rescan column with full content”, “scan related columns”). Implement as **optional** (config-driven) to avoid performance impact.

1. **Report**
   - Add a **recommendation** (or dedicated section/sheet) for **“Possible data of minors”** with **highest priority** (above CRÍTICA where applicable) and **differential treatment** text (LGPD Art. 14, GDPR Art. 8, consent, parental responsibility, etc.).
   - In Report info or Recommendations, **surface possible-minor findings** so they are clearly more prominent than other gathered data that triggered notifications.

1. **Config**

   Optional settings, e.g.:

   - `detection.minor_age_threshold` (default 18).
   - `detection.minor_full_scan` (default false): when true, full-scan column and adjacent when DOB suggests minor.
   - `detection.minor_cross_reference` (default true): use name/doc/health in same row to boost confidence.

---

## DOB/age identification: names, formats, acronyms

Scanned files and databases may expose date-of-birth or age under **different languages** (English and Brazilian Portuguese), **data names** (full words or acronyms), and **data formats**. The detector and cross-reference logic must consider the following so minor-related columns and values are reliably recognized.

### Field / column name variations

Treat as DOB- or age-related when the **column name** (or sampled header/label) matches any of the below (case-insensitive, normalizing accents where applicable).

| Concept           | English                                                         | Brazilian Portuguese                                                            | Notes                                                           |
| ---               | ---                                                             | ---                                                                             | ---                                                             |
| **Date of birth** | date of birth, birth date, birthdate, date_of_birth, birth_date | data de nascimento, data nascimento, nascimento, data de nasc., nascimento_data | Prefer matching “birth”/“nascimento”/“nasc” in context of date. |
| **Age**           | age, person age, current age                                    | idade, idade_atual, idade_pessoa, faixa etária (age range)                      | “idade” is the standard PT-BR term.                             |

### Three-letter and short acronyms

Many schemas use short codes instead of full names. The detector should recognize (e.g. in column names or metadata):

| Acronym  | Meaning                                         | Language                       |
| ---      | ---                                             | ---                            |
| **DOB**  | date of birth                                   | EN                             |
| **DN**   | data de nascimento / date of birth              | PT-BR / EN (context-dependent) |
| **DDN**  | data de nascimento                              | PT-BR                          |
| **NASC** | nascimento (birth)                              | PT-BR                          |
| **DTN**  | data de nascimento                              | PT-BR (less common)            |
| **AGE**  | age                                             | EN                             |
| **IDD**  | idade (age)                                     | PT-BR (less common)            |
| **DOJ**  | date of joining (not DOB; avoid false positive) | —                              |

**Implementation note:** Match acronyms as whole tokens (e.g. `\bDOB\b`, `\bDDN\b`, `\bNASC\b`, `\bidade\b`) when scanning column names and labels to avoid matching substrings inside unrelated identifiers.

### Data formats

- **Dates (DOB):**
- **DMY:** `dd/mm/yyyy`, `dd/mm/yy`, `d/m/yyyy` (e.g. 15/03/2010, 1/5/12) — common in BR and many locales.
- **YMD:** `yyyy-mm-dd`, `yyyy/mm/dd` (e.g. 2010-03-15) — ISO / databases.
- **MDY:** `mm/dd/yyyy`, `mm-dd-yyyy` (e.g. 03/15/2010) — US style.
- **Other:** `dd-mm-yyyy`, `dd.mm.yyyy`; 4-digit year preferred for age calculation; 2-digit year (e.g. `yy`) should use a sensible century (e.g. 00–30 → 2000–2030).
- **Age (numeric):**
- Integer or decimal: e.g. `17`, `18`, `0`–`120`. When **column or context** indicates “age”/“idade” (or acronyms above) and value is numeric, compare directly to `minor_age_threshold` (no date parsing).

### Substitutions and synonyms

- **“Data” vs “Date”:** “data” (PT-BR) = “date”; “data de nascimento” = “date of birth”.
- **“Nascimento” / “Nasc”:** birth; “nasc” often used in DB/legacy column names.
- **“Idade”:** age; “faixa etária” = age range (still relevant for minor detection when values or ranges indicate &lt; 18).

The detector should use a **single internal list** of normalized tokens (full names + acronyms) for “DOB-like” and “age-like” columns so that any of these variations, in EN or PT-BR, is treated consistently for possible-minor logic.

---

## Config wiring (to-do 8)

The optional `detection` section in the main config file is normalized by `config/loader.py` and passed through to the detector:

- **Loader** (`config/loader.py`): Normalizes `detection.minor_age_threshold` (default 18), `detection.minor_full_scan` (default false), `detection.minor_full_scan_limit` (default 100), `detection.minor_cross_reference` (default true). Keys are under `config["detection"]`.
- **Engine** (`core/engine.py`): Reads `config.get("detection")` and passes it as `detection_config` to `DataScanner` and to database connectors (for optional minor full-scan).
- **Scanner** (`core/scanner.py`): Accepts optional `detection_config` and forwards it to `SensitivityDetector`.
- **Detector** (`core/detector.py`): Accepts optional `detection_config` in `__init__`; sets `_minor_age_threshold` from `detection_config.get("minor_age_threshold", 18)`.
- **SQL connector** (`connectors/sql_connector.py`): Accepts optional `detection_config`; when `minor_full_scan` is true and a column yields DOB_POSSIBLE_MINOR, re-samples that column with `minor_full_scan_limit` and re-runs detection; may append “(full-scan confirmed)” to norm_tag.
- **Report generator** (`report/generator.py`): When `minor_cross_reference` is true, groups findings by table/path, marks possible-minor rows with Minor confidence “high (cross-ref)” when the same group has identifier/health, and adds a high-confidence recommendation row.

## Example config:

```yaml
detection:
  minor_age_threshold: 18   # age below this triggers possible_minor (default 18)
  minor_full_scan: false    # optional: re-sample column when DOB suggests minor (default off)
  minor_full_scan_limit: 100
  minor_cross_reference: true  # add Minor confidence column and high-confidence recommendation
```

When no `detection` section is present or `minor_age_threshold` is missing, the detector uses 18. Tests that instantiate `DataScanner()` or `SensitivityDetector()` without `detection_config` keep this default.

---

## Sequential to-dos

Execute in order; each step should be tested and non-regressing before the next.

| #   | To-do                                                                                                                                                                                                                                                                               | Status                                        |
| --- | ---                                                                                                                                                                                                                                                                                 | ---                                           |
| 1   | **Design & doc:** Finalize approach (age inference, flag vs new level, cross-ref, full-scan scope) and document in this file; ensure schema/API impact is minimal (optional column or flag).                                                                                        | ✅ Done                                        |
| 2   | **Detector – DOB/age:** Add date parsing (DOB) and age calculation (stdlib); when age &lt; threshold, set internal flag or level for “possible minor”. Do not change existing HIGH/MEDIUM/LOW for non-minor findings.                                                               | ✅ Done                                        |
| 3   | **Schema (optional):** Add optional column `possible_minor` (or `minor_data_indicator`) to database_findings and filesystem_findings with migration; or encode via norm_tag/pattern_detected (e.g. pattern “DOB_POSSIBLE_MINOR”).                                                   | ✅ Done (encode via pattern_detected/norm_tag) |
| 4   | **Scanner/connector:** Pass “possible minor” from detector into saved findings (store flag or special pattern/norm_tag).                                                                                                                                                            | ✅ Done                                        |
| 5   | **Cross-reference:** When a finding is DOB/possible_minor, correlate with other columns in same table/row (name, CPF/RG/SSN, health-related). Optionally set “confirmed” or “high_confidence” minor indicator. May require scanner to supply row context or a post-processing step. | ✅ Done                                        |
| 6   | **Full scan (optional):** When DOB suggests minor and config enables it, trigger full scan of that column and related columns (engine/connector). Document as optional; default off.                                                                                                | ✅ Done                                        |
| 7   | **Report:** Add recommendation row or section for “Possible data of minors” with highest priority and differential treatment (LGPD Art. 14, GDPR Art. 8, consent, etc.). Ensure possible-minor findings are listed and clearly prioritized above other findings.                    | ✅ Done                                        |
| 8   | **Config:** Add optional `detection.minor_age_threshold`, `detection.minor_full_scan`, `detection.minor_cross_reference` in config loader (defaults: 18, false, true). Wire config from loader → engine → scanner → detector so threshold is applied.                               | ✅ Done                                        |
| 9   | **Tests:** Unit tests for age inference, for possible_minor flag, for report prioritization; full test suite passes with no regression.                                                                                                                                             | ✅ Done                                        |
| 10  | **Docs:** Update sensitivity-detection and compliance docs (EN and PT-BR) to describe possible-minor detection and differential treatment.                                                                                                                                          | ✅ Done                                        |

---

## References

- LGPD Art. 14 (children’s data).
- GDPR Art. 8 (child’s consent in relation to information society services).
- Existing detector: `core/detector.py` (regex + ML + DL; returns sensitivity_level, pattern_detected, norm_tag).
- Existing report: `report/generator.py` (`_recommendations_rows`, Report info, findings sheets).
- DB schema: `core/database.py` (DatabaseFinding, FilesystemFinding; sensitivity_level String(20)).

---

*This plan is additive and aims to avoid breaking existing behaviour, performance, or sensitivity for non-minor data.*
