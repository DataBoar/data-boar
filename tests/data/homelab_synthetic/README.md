# Homelab synthetic file fixtures

**Purpose:** Files for **multi-host** Data Boar lab rounds (bind mounts, SMB/NFS/sshfs, cloud-sync folders).

**Rules:** Contents are **fictional** test strings (same style as `scripts/populate_poc_database.py`). Do not replace with real PII.

| File | Intent |
| ---- | ------ |
| `person_a_notes.txt` | Free text with name + synthetic CPF — pair with CSV for same “person” |
| `person_a_sheet.csv` | Same display name and overlapping token as notes file — aggregation / linkage experiments |
| `innocuous_ops.txt` | SKU / ticket IDs only — negative control for obvious false positives |
| `synthetic_pan_luhn.txt` | Visa test PAN `4111111111111111` (Luhn-valid). RC sentinel `filesystem_credit_card` requires `CREDIT_CARD` on this corpus |

**Detector hints:** Names match the SQL seed theme in `deploy/lab-smoke-stack/init/*/02_lab_smoke_linkage.sql` only where noted in comments inside files.

See [LAB_SMOKE_MULTI_HOST.md](../../../docs/ops/LAB_SMOKE_MULTI_HOST.md).
