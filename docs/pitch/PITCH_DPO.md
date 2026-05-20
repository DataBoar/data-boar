# DPO pitch — privacy and compliance leadership

**Português (Brasil):** [PITCH_DPO.pt_BR.md](PITCH_DPO.pt_BR.md) · **Index:** [INDEX.md](INDEX.md)

**Audience:** Data Protection Officers, privacy counsel, compliance leads (LGPD, GDPR, PIPEDA, multinational programmes).

---

## Role of the tool in your programme

Data Boar **supports** privacy governance—it does not decide lawfulness, retention limits, or breach notification outcomes. It accelerates **inventory and evidence** so your office can focus on interpretation, risk acceptance, and regulator-ready narrative.

Non-technical legal summary: [COMPLIANCE_AND_LEGAL.md](../COMPLIANCE_AND_LEGAL.md).

## Framework alignment (configuration, not magic)

Built-in and sample **norm tags** cover LGPD, GDPR, CCPA, HIPAA, GLBA, and extensible profiles (UK GDPR, PIPEDA, POPIA, APPI, PCI-DSS, 152-FZ, and more) via [compliance-samples/](../compliance-samples/).

| Need | Where to look |
| ---- | ------------- |
| Merge a regional YAML profile | [COMPLIANCE_FRAMEWORKS.md](../COMPLIANCE_FRAMEWORKS.md) |
| Recommendation wording per norm | `report.recommendation_overrides` in [USAGE.md](../USAGE.md) |
| Multinational tension hints (heuristic) | [JURISDICTION_COLLISION_HANDLING.md](../JURISDICTION_COLLISION_HANDLING.md) |

## DSAR and subject-rights workflows

The product helps you **locate** personal data categories and **document** scan scope—it does **not** automate legal responses, identity verification, or statutory deadlines.

Practical pattern:

1. Define targets tied to the data subject's systems of interest.
2. Run bounded discovery with audit-friendly session logs.
3. Export findings and heatmaps for legal review—not raw bulk exfiltration by default.

Storyboard: [use-cases/USE_CASE_SCAN_AND_REMEDIATE.md](../use-cases/USE_CASE_SCAN_AND_REMEDIATE.md).

## Minors and sensitive categories

When enabled, the engine flags **possible** child-related columns and cross-references with identifier- or health-like findings—aligned with inventory language for **LGPD Art. 14** and **GDPR Art. 8** review, not parental consent automation.

Operator guide: [MINOR_DETECTION.md](../MINOR_DETECTION.md).

## Evidence you can defend in a workshop

- Norm-tagged recommendations suitable for triage (not legal opinions).
- Session-over-session **trend** context.
- Optional executive Markdown and `scan_manifest_*.yaml` beside the XLSX—see [REPORTS_AND_COMPLIANCE_OUTPUTS.md](../REPORTS_AND_COMPLIANCE_OUTPUTS.md).

## What to tell your CISO and board

- **Shared responsibility:** your office owns legal basis and interpretation; the platform owns configured technical reads and structured outputs.
- **No overclaim:** passing a scan does not prove compliance; it produces **prioritized technical signals**.

## Next step

- **Executive summary:** [PITCH_STAKEHOLDER.md](PITCH_STAKEHOLDER.md)
- **Security controls:** [PITCH_CISO.md](PITCH_CISO.md)
- **Tokenized findings narrative:** [use-cases/USE_CASE_TOKENIZED_FINDINGS.md](../use-cases/USE_CASE_TOKENIZED_FINDINGS.md)
