# Use case — Tokenized findings for safe sharing

**Português (Brasil):** [USE_CASE_TOKENIZED_FINDINGS.pt_BR.md](USE_CASE_TOKENIZED_FINDINGS.pt_BR.md)

**Illustrative only** — not legal advice. Requires an **Enterprise remediation/tokenization plugin** (maintainer plan `docs/plans/PLAN_REMEDIATION_INTERFACE.md`, GitHub **#601**).

---

## Problem

Findings exports (for example **JSONL**) often include **`sample`** fields with **real PII fragments** so analysts can validate detector confidence. That blocks sharing the same report with external auditors, regulators, partners, or offshore SOC teams without a separate redaction pass.

> I cannot show the findings report to the auditor because it still contains live personal data.

---

## Before and after (conceptual)

| Mode | Example `sample` field | Risk |
| ---- | ---------------------- | ---- |
| **Today** | `123.456.789-00` (live national ID pattern) | PII exposed in every copy of the report |
| **With FPE tokenization** | `871.234.156-99` (same format, not the real subject) | Report structure unchanged; downstream tools keep working |

**Format-preserving encryption (FPE)** keeps length and charset class stable so validators, regex checks, and dashboards still behave realistically while the underlying subject is protected.

---

## Audiences and benefits

| Audience | Benefit | Typical framework hook |
| -------- | ------- | ---------------------- |
| **DPO / privacy office** | Share evidence packages with regulators without titular data in attachments | LGPD Art. 46; GDPR Art. 25 |
| **CISO / SOC** | Feed SIEM or ticketing with finding shape, not live PII in log pipelines | SOC 2 CC6.1 (logical access to sensitive data) |
| **External auditor** | Review scope and density of issues with realistic samples | ISO 27001 / SOC 2 evidence requests |
| **Engineering** | Debug location and detector class without seeing real subjects | Internal need-to-know minimization |

---

## How to enable (product)

1. Run discovery and produce findings per [USAGE.md](../USAGE.md).
1. Configure **Enterprise** export path to invoke a **tokenization plugin** on `sample` (and other configured fields) before write or before share.
1. Retain **reversible** tokens only where policy and key custody allow; use **irreversible** tokens for auditor-only packages when required.

Implementation tracking: GitHub **#601** (maintainer plan `docs/plans/PLAN_REMEDIATION_INTERFACE.md`).

---

## Related docs

- [USE_CASES_HUB.md](USE_CASES_HUB.md) ([pt-BR](USE_CASES_HUB.pt_BR.md))
- [USE_CASE_SCAN_AND_REMEDIATE.md](USE_CASE_SCAN_AND_REMEDIATE.md) ([pt-BR](USE_CASE_SCAN_AND_REMEDIATE.pt_BR.md))
- [COMPLIANCE_AND_LEGAL.md](../COMPLIANCE_AND_LEGAL.md) ([pt-BR](../COMPLIANCE_AND_LEGAL.pt_BR.md))
