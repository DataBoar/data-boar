# ADR 0015 — POC Test Infrastructure: Synthetic Corpus, Postman Collection, and Ansible Database Role

- **Status:** Accepted
- **Date (UTC):** 2026-04-05
- **Authors:** Fabio Leitao
- **Deciders:** Fabio Leitao

## Context

Data Boar was approaching its first real client POC. The team needed:

1. **Test data** covering the full scanner surface — OCR-noisy files, nested archives, steganography, false-positive pressure, and catastrophic scenarios.
2. **Database coverage** — enterprise clients store PII in PostgreSQL, MariaDB, and MSSQL.
3. **API testing** — the REST API must be validated by collaborators not comfortable with Python/CLI.
4. **Reproducibility** — collaborators (team members) must run the same test pass independently and get comparable results.
5. **Gap discovery** — false negatives, error message quality, and troubleshooting UX are as important as detection coverage for a first POC.

## Decision

### 1. Synthetic corpus generator (`scripts/generate_synthetic_poc_corpus.py`)

Generates a structured test corpus under `tests/synthetic_corpus/` (gitignored) with nine scenario directories:

| Folder | Scenario |
|---|---|
| `1_happy/` | Clear PII in all supported file types |
| `2_unhappy/` | OCR noise, encoding quirks (latin-1, BOM), base64 blobs |
| `3_catastrophic/` | Nested/password ZIPs, deep nesting, very long lines |
| `4_false_positive/` | PII-shaped data that is NOT PII |
| `5_manual_review/` | Partially masked PII, PII in prose, foreign IDs (DNI, SSN) |
| `6_stego/` | CPF embedded in PNG LSB and EXIF — expected NOT found by default |
| `7_extensions/` | One file per supported extension, each containing PII |
| `8_stress_load/` | 50 MB files, 500-file floods, 10-level nesting, 1M-line files |
| `9_config_errors/` | Intentionally broken configs + `run_error_tests.sh` |

Rationale: No privacy risk; fully reproducible; expected outcomes explicit per scenario.

### 2. Database population script (`scripts/populate_poc_database.py`)

Populates PostgreSQL or MariaDB with synthetic PII across 11 tables: happy path, innocent/bait, multilingual, encoding stress, FK-spread PII, and 10,000-row SRE load table. Supports `--docker-setup`, `--write-config`, `--dry-run`.

### 3. Ansible role for automated DB setup (`deploy/ansible/roles/poc_database/`)

Idempotent Ansible role + playbook (`site-poc-db.yml`): pulls DB image, starts container, installs Python drivers, runs `populate_poc_database.py`. One-command reproducible DB setup for remote collaborators.

### 4. Postman collection (`tests/postman/Data_Boar_POC_ErrorScenarios.postman_collection.json`)

Covers the REST API surface: scan trigger, scan status, report download, and error responses from broken configs. Primary API testing artifact for non-developer collaborators.

### 5. Collaborator testing guide (`docs/TESTING_POC_GUIDE.md`)

Public tracked guide: corpus generation, expected outcomes per scenario, validation steps, expected failure modes, and a gap report template.

## Alternatives Considered

| Alternative | Reason not chosen |
|---|---|
| Use real sanitized client data | Privacy risk; cannot ship in repo or public guides |
| CI unit tests only | Cannot cover full pipeline (filesystem + connector + report) |
| Manual DB setup instructions | Not reproducible; high friction for remote collaborators |
| Pytest fixtures at runtime | Too slow for large stress scenarios |

## Consequences

**Positive:**
- Collaborators can run full-surface POC validation independently.
- Each Data Boar release can be regression-tested against the same corpus.
- Stress scenarios provide a repeatable performance baseline (time, memory/RSS) per release.
- Postman collection enables live API demos during client POC calls.

**Negative / Trade-offs:**
- Optional libs (`Pillow`, `reportlab`, `python-docx`, `openpyxl`) needed for binary-format scenarios.
- `run_error_tests.sh` assumes POSIX shell — Windows collaborators need WSL or Git Bash.
- Synthetic DB does not yet cover MSSQL or Oracle.

## Related

- ADR 0012: OCR image sensitive data detection
- ADR 0013: Browser artifact (SQLite/LevelDB) scan strategy
- `docs/TESTING_POC_GUIDE.md`
- `docs/private/plans/POC_METRICS_TEMPLATE.pt_BR.md`
- `scripts/generate_synthetic_poc_corpus.py`
- `scripts/populate_poc_database.py`
- `deploy/ansible/roles/poc_database/`
