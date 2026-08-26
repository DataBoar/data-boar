# Decision-maker value brief

**Português (Brasil):** [DECISION_MAKER_VALUE_BRIEF.pt_BR.md](DECISION_MAKER_VALUE_BRIEF.pt_BR.md)

This brief helps leadership, legal, compliance, and security teams evaluate Data Boar without overclaims.

## Positioning in one sentence

Data Boar is a configurable technical discovery and evidence-support platform that helps organizations locate and classify possible personal and sensitive data exposure across heterogeneous sources.

## What it is and what it is not

- **It is**
- A discovery and mapping engine for data inventory and remediation prioritization.
- A metadata-first reporting workflow (findings, norm tags, trend context) for governance.
- A bridge between IT operations and compliance/legal review processes.
- An input to **ITIL 4 value co-creation** (utility + warranty): scans are repeatable evidence, not a finished compliance outcome. See [ITSM_GOVERNANCE_ALIGNMENT.md](ITSM_GOVERNANCE_ALIGNMENT.md).
- **It is not**
- A legal decision engine or legal advice.
- A certification authority for ISO, SOC, or regulatory compliance.
- A replacement for DPO, counsel, or formal audit firms.

## Shared responsibility model

- **Data Boar**
- Runs configured scans against approved targets.
- Produces technical findings and operational evidence artifacts.
- Supports norm-aligned language via configuration profiles.
- **Customer organization**
- Defines lawful scope, legal basis, and risk acceptance.
- Approves credentials, retention, and access governance.
- Interprets findings for legal/regulatory decisions.

## Value by segment

### SMB (lean IT)

- Fast visibility into high-risk data exposure with controlled operational overhead.
- Practical outputs for immediate remediation prioritization.
- Suitable when teams need progress without full enterprise platforms.

### Mid-market (growing governance pressure)

- Repeatable scans and trend evidence for compliance and security coordination.
- Structured bridge between IT teams and legal/compliance stakeholders.
- Config-driven adaptation for multi-jurisdiction and policy growth.

### Enterprise / public sector

- Technical evidence support for broader governance and assurance programs.
- Integration path with stricter operational controls and segmented environments.
- Professional-services-friendly model for phased maturity programs.
- **Remediation loop (Enterprise, coming):** findings carry precise coordinates — field location, data type, identifier — so third-party remediation plugins can apply tokenization, masking, or field encryption in-place, then Data Boar re-scans to confirm. The full loop: scan once, remediate precisely, prove it.

## Children's and minors' data — deliberate product depth

Minor-related exposure is a **first-class detection lane**, not a marketing afterthought: configurable age thresholds, optional deeper database resampling when a column looks like DOB or age, **cross-reference** with identifier- or health-like findings in the same table or filesystem path, and norm-tagged Excel recommendations aligned with **LGPD Art. 14** and **GDPR Art. 8**. US-oriented **compliance-sample YAML** (e.g. COPPA-flavoured vocabulary) supports **inventory language** for counsel review—it does **not** perform parental consent checks or legal age verification.

- Operator guide: [MINOR_DETECTION.md](MINOR_DETECTION.md) ([pt-BR](MINOR_DETECTION.pt_BR.md))
- Concern-first map (minors block is the first table): [MAP.md](MAP.md) ([pt-BR](MAP.pt_BR.md))

## Minimum procurement questions

Before purchase, confirm:

1. Which data domains and systems are in the first scan scope?
1. Which audience consumes the first evidence package (IT, DPO, legal, board)?
1. What timeline is expected for first actionable findings?
1. Which controls remain outside tool scope and need parallel ownership?
1. What success metric defines value in 30/60/90 days?

## Evidence package expectations

Typical outcomes include:

- Source and pattern findings with sensitivity context.
- Norm-tagged recommendation language suitable for triage.
- Session-over-session trend visibility.
- Operational trace artifacts for repeatability.

These outcomes support governance and audit preparation; they do not, by themselves, prove legal compliance.

## Related documentation

- [MINOR_DETECTION.md](MINOR_DETECTION.md) ([pt-BR](MINOR_DETECTION.pt_BR.md)) — thresholds, cross-reference, samples
- [COMPLIANCE_AND_LEGAL.md](COMPLIANCE_AND_LEGAL.md) ([pt-BR](COMPLIANCE_AND_LEGAL.pt_BR.md))
- [COMPLIANCE_FRAMEWORKS.md](COMPLIANCE_FRAMEWORKS.md) ([pt-BR](COMPLIANCE_FRAMEWORKS.pt_BR.md))
- [COMPLIANCE_TECHNICAL_REFERENCE.md](COMPLIANCE_TECHNICAL_REFERENCE.md) ([pt-BR](COMPLIANCE_TECHNICAL_REFERENCE.pt_BR.md))
- [SECURITY.md](SECURITY.md) ([pt-BR](SECURITY.pt_BR.md))
- [README.md](README.md) ([pt-BR](README.pt_BR.md))
- [use-cases/USE_CASE_SCAN_AND_REMEDIATE.md](use-cases/USE_CASE_SCAN_AND_REMEDIATE.md) ([pt-BR](use-cases/USE_CASE_SCAN_AND_REMEDIATE.pt_BR.md)) — Enterprise remediation pipeline with audit trail (coming; illustrative use-case)
- [use-cases/USE_CASE_TOKENIZED_FINDINGS.md](use-cases/USE_CASE_TOKENIZED_FINDINGS.md) ([pt-BR](use-cases/USE_CASE_TOKENIZED_FINDINGS.pt_BR.md)) — share findings reports without exposing live PII (coming; illustrative use-case)
