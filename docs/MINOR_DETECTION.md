# Minor data detection: configuration and fine-tuning

The application can detect when gathered data may relate to **minors** (e.g. age or date of birth in columns) and treat it as **highest sensitivity**, with differential treatment in reports (LGPD Art. 14, GDPR Art. 8). This page describes how to **configure and fine-tune** the feature via the **external config file**, without changing application code.

**Português (Brasil):** [MINOR_DETECTION.pt_BR.md](MINOR_DETECTION.pt_BR.md)

---

## What is detected

- **Column names** that suggest date of birth or age, in **English and Brazilian Portuguese**, including acronyms (e.g. DOB, DDN, NASC, idade, age).
- **Sample values**: numeric ages (e.g. `17`) or dates that, when interpreted as date of birth, imply an age below the configurable **threshold** (default **18**). Those findings are flagged as **possible minor data** (`DOB_POSSIBLE_MINOR`) and get a dedicated high-priority recommendation in the report.

Design rationale and historical column-name tables live in the archived plan **`PLAN_MINOR_DATA_DETECTION`** under `docs/plans/completed/` (in checkout; not linked here from this operator guide).

---

## Config file: where and what

The **minor/adult age threshold** is set in your **main config file** (e.g. `config.yaml` or the file pointed to by `CONFIG_PATH`). No code changes are required.

| Key                               | Type    | Default   | Description                                                                                                                                                                                                                                                                                                                                                                                             |
| ---                               | ---     | ---       | ---                                                                                                                                                                                                                                                                                                                                                                                                     |
| `detection.minor_age_threshold`   | integer | **18**    | Age below this value (inclusive) is treated as possible minor. Use e.g. 21 if your policy treats people under 21 as minors.                                                                                                                                                                                                                                                                             |
| `detection.minor_full_scan`       | boolean | **false** | When **true**, for **database** targets only: if a column sample suggests possible minor (DOB_POSSIBLE_MINOR), the connector re-samples that column with a larger limit (`minor_full_scan_limit`) and re-runs detection. If the finding is still possible minor, it is saved (optionally with norm_tag “(full-scan confirmed)”). **Optional; default off** to avoid extra load on large tables.         |
| `detection.minor_full_scan_limit` | integer | **100**   | Maximum number of values to fetch when `minor_full_scan` is true. Ignored when `minor_full_scan` is false.                                                                                                                                                                                                                                                                                              |
| `detection.minor_cross_reference` | boolean | **true**  | When true, the report generator cross-references possible-minor findings with other findings in the **same table** (database) or **same path** (filesystem). If the same table/path also has identifier or health-like data (e.g. name, CPF/RG/SSN, health), possible-minor rows are marked with **Minor confidence** = **“high (cross-ref)”** and a dedicated high-confidence recommendation is added. |

If the **`detection`** section is **omitted**, the threshold defaults to **18** and the application behaves as before (no errors). Adding the section allows you to adjust the threshold without breaking existing runs.

---

## How to adjust and fine-tune

### 1. Use the default (18)

Do nothing: omit the `detection` section. Anyone under 18 (by age or inferred from DOB) is flagged as possible minor.

### 2. Raise the threshold (e.g. under-21 policy)

If your organisation treats people under 21 as minors, set the threshold to 21 in your config file:

```yaml
# config.yaml
targets: []
report:
  output_dir: .
sqlite_path: audit_results.db

detection:
  minor_age_threshold: 21
```

Then run the audit as usual. Columns that look like age/DOB with values indicating age under 21 will be flagged as possible minor.

### 3. Lower the threshold (e.g. only young children)

To flag only very young ages (e.g. under 14), set:

```yaml
detection:
  minor_age_threshold: 14
```

### 4. Full example with other options

```yaml
targets:

- name: my-db

    type: database
    host: localhost
    database: app_db
file_scan:
  extensions: [.csv, .xlsx, .txt]
  recursive: true
report:
  output_dir: ./reports
  min_sensitivity: LOW

detection:
  minor_age_threshold: 18
  minor_full_scan: false      # optional: re-sample column with minor_full_scan_limit when DOB suggests minor (default off)
  minor_full_scan_limit: 100  # max rows for full-scan pass (database only)
  minor_cross_reference: true # add "Minor confidence" column and high-confidence recommendation when same table/path has identifier/health

sqlite_path: audit_results.db
scan:
  max_workers: 1
```

---

## Column names and formats recognised

The detector looks for **DOB- or age-like** column names (and sample content). Recognised names include:

| Concept       | English                              | Brazilian Portuguese                           | Acronyms                |
| ---           | ---                                  | ---                                            | ---                     |
| Date of birth | date of birth, birth date, birthdate | data de nascimento, nascimento, data de nasc.  | DOB, DDN, DN, NASC, DTN |
| Age           | age, person age                      | idade, idade_atual, idade_pessoa, faixa etária | AGE, IDD                |

**Date formats** in sample text: `dd/mm/yyyy`, `yyyy-mm-dd`, `mm/dd/yyyy` (and common variants). **Numeric age**: integers in the sample (e.g. 0–120) when the column name suggests age.

If a column name does **not** suggest DOB or age, a value like `17` or a date in the sample will **not** by itself trigger possible-minor (avoids false positives on generic numeric/date columns).

---

## Cross-reference and “Minor confidence” column

When **`detection.minor_cross_reference`** is **true** (default), the report generator groups findings by **table** (database) or **path** (filesystem). For each group, if there is at least one finding with **DOB_POSSIBLE_MINOR** and at least one finding that looks like **identifier or health** data (e.g. name, CPF/RG/SSN, health-related column or pattern), then every possible-minor finding in that group is marked with **Minor confidence** = **“high (cross-ref)”** in the **Database findings** and **Filesystem findings** sheets. When that happens, an extra **recommendation row** is added at the top of the **Recommendations** sheet: “DOB_POSSIBLE_MINOR (high confidence – cross-ref)”, explaining that the same table/file contains DOB suggesting minor and identifier/health data, and should be treated as high priority for the DPO. Set **`minor_cross_reference: false`** to disable this behaviour and leave the Minor confidence column empty.

---

## Full scan (optional, database only)

When **`detection.minor_full_scan`** is **true**, **database** connectors (PostgreSQL, MySQL, SQLite, etc.) behave as follows: after the usual small sample of a column is scanned, if the result indicates **DOB_POSSIBLE_MINOR**, the connector fetches up to **`minor_full_scan_limit`** values (default **100**) from that same column and runs detection again. If the finding is still possible minor, the finding is saved; the **norm_tag** may include “(full-scan confirmed)” to indicate that a larger sample was used. This is **optional** and **default off** to avoid performance impact on large tables. Filesystem and other target types do not perform this second pass.

---

## Report and recommendations

Findings flagged as possible minor get:

- **Sensitivity:** HIGH
- **Pattern:** `DOB_POSSIBLE_MINOR` (possibly combined with other patterns)
- **Norm tag:** LGPD Art. 14 – possible minor data; GDPR Art. 8 (and “(full-scan confirmed)” when full-scan was used)
- **Minor confidence:** “high (cross-ref)” when cross-reference found identifier/health in the same table/path; otherwise empty

In the Excel report, the **Recommendations** sheet includes a dedicated row for possible minor data with **highest priority** (CRÍTICA) and differential treatment text (consent, storage, use, sharing, parental responsibility). That row is listed **first** in the Recommendations sheet. When cross-reference identifies high-confidence cases, an additional row “DOB_POSSIBLE_MINOR (high confidence – cross-ref)” appears at the top. See the report generator source for the exact wording.

---

## Related documentation

- **Documentation index** (all topics, both languages): [README.md](README.md) · [README.pt_BR.md](README.pt_BR.md).
- Archived plan **`PLAN_MINOR_DATA_DETECTION`** in `docs/plans/completed/` — historical design and completion checklist (maintainers).
- [SENSITIVITY_DETECTION.md](SENSITIVITY_DETECTION.md) ([pt-BR](SENSITIVITY_DETECTION.pt_BR.md)) – ML/DL and regex sensitivity detection.
- [USAGE.md](USAGE.md) ([pt-BR](USAGE.pt_BR.md)) – General configuration and API usage.
