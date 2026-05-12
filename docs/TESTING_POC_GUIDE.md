# Data Boar — POC Testing Guide

> **Audience:** collaborators (team members, lab-op team) running validation passes on the scanner.
> **Version:** 2026-04-05 | **Related:** `scripts/generate_synthetic_poc_corpus.py`
>
> **Português (Brasil):** [TESTING_POC_GUIDE.pt_BR.md](TESTING_POC_GUIDE.pt_BR.md) (SBOM section + link to full EN guide)

This guide walks through the full test coverage plan for Data Boar POC validation:
how to generate the synthetic test corpus, what each scenario tests, and how to
interpret and document findings.

---

## 1. Quick start (5 minutes)

```bash
# 1. Clone and set up
git clone https://github.com/FabioLeitao/data-boar.git
cd data-boar

# 2. Install dependencies
pip install uv
uv sync

# 3. Generate the full synthetic corpus
uv run python scripts/generate_synthetic_poc_corpus.py

# 4. Point the scanner at the corpus
uv run python main.py --config deploy/config.example.yaml \
    --scan --target tests/synthetic_corpus --report

# 5. Compare findings to expected results
# Each sub-folder in tests/synthetic_corpus/ has an EXPECTED.txt file.
```

---

## 2. What the corpus covers

| Folder | Scenario | Goal |
|---|---|---|
| `1_happy/` | **Happy path** | Scanner finds CPF/RG/email in clear text, PDF, DOCX, XLSX, SQLite, PNG (OCR) |
| `2_unhappy/` | **Unhappy path** | Scanner handles OCR noise, latin-1 encoding, BOM, CRLF, base64-embedded PII |
| `3_catastrophic/` | **Catastrophic** | Scanner attempts nested ZIPs, password-protected ZIP, tar.gz, disguised extensions |
| `4_false_positive/` | **False positive** | Scanner does NOT trigger on invalid CPF-shaped serials, IP addresses, versions |
| `5_manual_review/` | **Manual review** | Scanner flags partially masked PII for human review (not a hard positive) |
| `6_stego/` | **Steganography** | Scanner does NOT find CPF hidden in PNG LSB (expected gap — document it) |
| `7_extensions/` | **Extension coverage** | Every supported format has one CPF — map which formats are found vs missed |

---

## 3. Detailed scenario expectations

### Scenario 1 — Happy path

**Files:** `.txt`, `.csv`, `.json`, `.pdf`, `.docx`, `.xlsx`, `.db` (SQLite), `.png` (OCR)

**Expected:** scanner finds CPF `123.456.789-09` in ALL files.

**How to validate:**
1. Run scanner against `1_happy/`
2. Check the report for findings in each file type
3. Record any missed files in the gap table (Section 5)

**Common failure mode:** OCR not enabled — `id_card_visible.png` is missed.
To enable: set `ocr.enabled: true` in `config.yaml`.

---

### Scenario 2 — Unhappy path

**Files:** OCR-noisy text, latin-1, BOM CSV, CRLF, partial redaction, base64-embedded

**Expected:** scanner finds PII in most files; base64 detection is optional.

**Key test — base64:**
- File: `base64_embedded.txt`
- Contains: `campo_documento: <base64-encoded CPF + Nome>`
- If scanner decodes base64 before scanning: **FOUND** (good)
- If scanner reads raw text only: **NOT FOUND** (document as gap)

**Key test — encoding:**
- `latin1_encoded.txt`: scanner must handle non-UTF-8 gracefully (no crash, finding or miss)
- `bom_utf8.csv`: BOM should be stripped before scanning

---

### Scenario 3 — Catastrophic

**Files:** nested ZIP, password-protected ZIP, tar.gz, disguised `.jpg` extension, 500KB+ line

**Password for `password_protected.zip`:** `poc-test-123`

To configure: add to `config.yaml`:

```yaml
file_scan:
  zip_passwords:
    - poc-test-123
```

**Expected outcomes:**

| File | Expected without password config | Expected with password config |
|---|---|---|
| `nested.zip` | MAY be found (depends on depth limit) | Same |
| `password_protected.zip` | NOT found | FOUND |
| `archive.tar.gz` | FOUND | FOUND |
| `report_2026.jpg` | FOUND (magic-byte detection) or MISSED (extension filter) | Same |
| `long_line_stress.txt` | FOUND (no crash) | Same |

---

### Scenario 4 — False positive pressure

**Files:** invalid CPF-shaped serials, IP addresses, version strings, invalid CNPJs

**Expected:** scanner does NOT flag any file.

**How to validate:** run scanner and confirm the report shows **zero findings** for this folder.

If findings appear: check whether the CPF validator is using checksum validation.
False positives here indicate missing checksum enforcement (report as gap, not bug).

---

### Scenario 5 — Manual review triggers

**Files:** partially masked CPF, PII in prose, foreign patterns (DNI, SSN), anonymized columns

**Expected:** scanner flags some content for **manual review** (not a hard positive finding).

Look for findings with confidence `LOW` or `REVIEW_RECOMMENDED` in the report.

If scanner returns hard positives here: may indicate false positive risk in production.
Document in gap table with the specific pattern that triggered.

---

### Scenario 6 — Steganography (expected gap)

**Files:** `innocent_photo.png` (CPF in LSB), `photo_with_exif_pii.png` (CPF in PNG metadata)

**Expected:**
- `innocent_photo.png`: scanner does **NOT** find CPF (LSB is invisible to standard scanners)
- `photo_with_exif_pii.png`: scanner **MAY** find CPF if it reads PNG metadata/comments

**This is a known gap.** Document it, do not treat as a bug.

To manually verify the LSB-hidden CPF is there:

```bash
uv run python -c "
from scripts.generate_synthetic_poc_corpus import _extract_lsb
from pathlib import Path
print(_extract_lsb(Path('tests/synthetic_corpus/6_stego/innocent_photo.png')))
"
```

Expected output: `CPF:123.456.789-09;Nome:Ana Paula Souza`

---

### Scenario 7 — Extension coverage

**Files:** one file per supported extension, all containing `CPF: 123.456.789-09`

**Expected:** scanner finds CPF in all files. Missing = gap.

**How to fill the gap table:**

| Extension | Found | Notes |
|---|---|---|
| .txt | | |
| .csv | | |
| .json | | |
| .xml | | |
| .pdf | | |
| .docx | | |
| .xlsx | | |
| .db (SQLite) | | |
| .png (OCR) | | |
| .jpg (OCR) | | |
| .zip | | |
| .tar.gz | | |
| .tar.bz2 | | |
| .md | | |
| .log | | |
| .yml / .yaml | | |
| .ini / .cfg | | |

---

## 4. How to run against your lab-op environment

```bash
# On the lab node (LAB-NODE-01 or any host with Data Boar deployed via Ansible):
ssh your-user@lab-node

# Generate corpus on the target
cd /opt/data_boar
uv run python scripts/generate_synthetic_poc_corpus.py --output /tmp/poc_corpus

# Run scan
uv run python main.py --config config.yaml \
    --scan --target /tmp/poc_corpus --report

# Download report to your machine
scp your-user@lab-node:/opt/data_boar/reports/latest.* ./
```

---

## 5. Gap reporting template

When you find a gap, add a row to this table and open a GitHub issue:

| Scenario | File / Format | Expected | Actual | Notes | Issue |
|---|---|---|---|---|---|
| 1_happy | .parquet | FOUND | NOT FOUND | pyarrow not installed in Docker image | #XX |
| 6_stego | innocent_photo.png | NOT FOUND (expected) | NOT FOUND | Known gap — LSB invisible to scanner | — |

---

## 6. Regenerating the corpus

If you change the scanner or add new detection rules, regenerate the corpus:

```bash
# Full regeneration
uv run python scripts/generate_synthetic_poc_corpus.py --output tests/synthetic_corpus

# Specific scenarios only
uv run python scripts/generate_synthetic_poc_corpus.py --scenario stego,extensions
```

The corpus is gitignored (`tests/synthetic_corpus/`) — it is generated on demand,
never committed. This prevents test data bloat and keeps the repo clean.

---

## 7. Related documentation

- `scripts/generate_synthetic_poc_corpus.py` — the corpus generator
- `docs/private/plans/OPEN_CORE_POC_GAP_ANALYSIS.pt_BR.md` — gap analysis and priorities
- `deploy/ansible/README.md` — how to deploy Data Boar for lab-op testing
- `docs/TECH_GUIDE.md` — architecture and connector reference
- `docs/USAGE.md` — CLI and configuration reference

---

## 8. Stress and load testing (Scenario 8)

**Generate (stress and load):**

```bash
uv run python scripts/generate_synthetic_poc_corpus.py --scenario stress_load
```

**Files:** 50 MB large file, 500-file directory flood, 10-level deep nesting, 1 million lines file.

**Measure performance:**

```bash
# Linux (shows max RSS, elapsed time):
/usr/bin/time -v uv run python main.py --config config.yaml \
    --scan --target tests/synthetic_corpus/8_stress_load 2> stress_metrics.txt
grep -E "Maximum resident|Elapsed" stress_metrics.txt

# PowerShell:
Measure-Command { uv run python main.py --config config.yaml --scan --target tests/synthetic_corpus/8_stress_load }
```

**Acceptable baseline:** < 15 min, < 1 GB RAM, no crash, all PIIs found.

---

## 9. Config error QA (Scenario 9)

Tests 8 intentional misconfigs to evaluate error message quality and troubleshooting UX.

**Generate (config error QA):**

```bash
uv run python scripts/generate_synthetic_poc_corpus.py --scenario config_errors
cd tests/synthetic_corpus/9_config_errors
bash run_error_tests.sh 2>&1 | tee error_test_results.txt
```

**Evaluate each config** (doc_*.txt files describe the expected error and troubleshoot hint):

| Config | Error type |
|---|---|
| `config_wrong_db_host.yaml` | DNS failure / connection refused |
| `config_wrong_db_credentials.yaml` | Auth failure |
| `config_missing_output_dir.yaml` | Permission denied / dir not found |
| `config_invalid_target_type.yaml` | Unknown connector type |
| `config_malformed_yaml.yaml` | YAML parse error |
| `config_missing_required_field.yaml` | Missing required key |
| `config_path_not_found.yaml` | Filesystem path not found |
| `config_api_key_wrong.yaml` | HTTP 401 on API (test with curl) |

**Score each on 1-5** using `docs/private/plans/POC_METRICS_TEMPLATE.pt_BR.md` Section 2.1.

---

## 10. Prerequisites for Windows 11 collaborators (team members)

If you are running on **Windows 11** (not Linux/macOS), follow these steps before the quick
start in §1.

### Step A — Install WSL2 + Ubuntu

```powershell
# Run in PowerShell as Administrator (one-time)
wsl --install -d Ubuntu-24.04
# Restart when prompted, then open "Ubuntu" from the Start menu and set up a username/password.
```

### Step B — Install Docker Desktop

1. Download from <https://www.docker.com/products/docker-desktop/>
2. Install with default settings.
3. Open Docker Desktop → Settings → **Resources → WSL Integration** → enable for **Ubuntu-24.04**.
4. Confirm Docker is available inside WSL:

```bash
# Run inside Ubuntu WSL terminal
docker run --rm hello-world
```

### Step C — Clone and run inside WSL

```bash
# Inside Ubuntu WSL terminal
git clone https://github.com/FabioLeitao/data-boar.git
cd data-boar
pip install uv
uv sync
uv run python scripts/generate_synthetic_poc_corpus.py
```

> **Note:** all `uv run` and `docker` commands in this guide should be run inside the WSL
> Ubuntu terminal, **not** PowerShell, unless noted otherwise.

### Step D — Database scenarios on Windows

The `scripts/populate_poc_database.py --docker-setup` flag spins up PostgreSQL and MariaDB via
Docker Compose. On Windows, run it inside the WSL terminal (Docker Desktop routes the daemon
from WSL automatically):

```bash
# Inside WSL Ubuntu
uv run python scripts/populate_poc_database.py --docker-setup --dry-run
uv run python scripts/populate_poc_database.py --docker-setup
```

### Step E — Postman on Windows (GUI, no WSL needed)

Download and install [Postman for Windows](https://www.postman.com/downloads/).
Import `tests/postman/Data_Boar_POC_ErrorScenarios.postman_collection.json` via
**File → Import → Upload Files**.

> The Data Boar API must be running (Step C above via WSL) before sending requests.

---

## Supply Colleague-Nn evidence (SBOM) for POC / security reviewers

For **procurement** and **incident-response** inventory (not organizational ISO 31000 risk management), the project publishes **two CycloneDX 1.6 JSON files** per release workflow:

| File | Contents |
| --- | --- |
| `sbom-python.cdx.json` | Python dependencies aligned with `uv.lock` |
| `sbom-docker-image.cdx.json` | Packages observed in the built Docker image (Syft) |

**Where to get them:** GitHub Actions workflow **SBOM** (`.github/workflows/sbom.yml`) — artifacts on the run, and attached to the **GitHub Release** when a release exists for the tag. **Documentation:** [SECURITY.md](SECURITY.md) (SBOM section), [ADR 0003](adr/ADR-0003-sbom-roadmap-cyclonedx-then-syft.md). **Local regeneration:** `scripts/generate-sbom.ps1` (outputs are gitignored).

