# Use Cases Hub — Data Boar

**Português (Brasil):** [USE_CASES_HUB.pt_BR.md](USE_CASES_HUB.pt_BR.md)

Entry point for **concrete product scenarios** (discovery, remediation hand-off, compliance evidence). Each file stands alone; read in sequence for the full **scan → remediate → prove** story.

**Workshop storyboards** (sector narratives for sales engineering) remain in [README.md](README.md) ([pt-BR](README.pt_BR.md)).

---

## Discovery and remediation

| Use case | Summary |
| -------- | ------- |
| [USE_CASE_SCAN_AND_REMEDIATE.md](USE_CASE_SCAN_AND_REMEDIATE.md) ([pt-BR](USE_CASE_SCAN_AND_REMEDIATE.pt_BR.md)) | Discovery-to-remediation pipeline with immutable audit trail |
| [USE_CASE_TOKENIZED_FINDINGS.md](USE_CASE_TOKENIZED_FINDINGS.md) ([pt-BR](USE_CASE_TOKENIZED_FINDINGS.pt_BR.md)) | Shareable findings reports with format-preserving tokens instead of live PII samples |

## Sensitive categories

| Use case | Summary |
| -------- | ------- |
| [USE_CASE_BIOMETRIC_DATA_PROTECTION.md](USE_CASE_BIOMETRIC_DATA_PROTECTION.md) ([pt-BR](USE_CASE_BIOMETRIC_DATA_PROTECTION.pt_BR.md)) | Discover and govern biometric data (LGPD Art. 11 / GDPR Art. 9) |

## Sector storyboards (workshop flows)

| Hub | Summary |
| --- | ------- |
| [README.md](README.md) ([pt-BR](README.pt_BR.md)) | Port, legal, pharma, EdTech, MSP, insurance, RPO, real estate, NGO, and related flows |

## Maintainer implementation

| Item | Summary |
| ---- | ------- |
| `docs/plans/PLAN_REMEDIATION_INTERFACE.md` (+ `.pt_BR.md`) | Enterprise post-scan remediation plugin contract (tokenization, masking, field crypto); GitHub **#601**, **#606** |

---

## Anti-drift ritual (3 steps)

1. Add or update **`docs/use-cases/USE_CASE_<NAME>.md`** (and **`.pt_BR.md`** mirror).
1. Register the row in **this hub** and, when relevant, in [README.md](README.md) storyboard table.
1. Run **`.\scripts\check-all.ps1`** (or **`lint-only`** for docs-only slices).

---

## Related docs

- [DECISION_MAKER_VALUE_BRIEF.md](../DECISION_MAKER_VALUE_BRIEF.md) ([pt-BR](../DECISION_MAKER_VALUE_BRIEF.pt_BR.md))
- [REPORTS_AND_COMPLIANCE_OUTPUTS.md](../REPORTS_AND_COMPLIANCE_OUTPUTS.md) ([pt-BR](../REPORTS_AND_COMPLIANCE_OUTPUTS.pt_BR.md))
- [USAGE.md](../USAGE.md) ([pt-BR](../USAGE.pt_BR.md))
