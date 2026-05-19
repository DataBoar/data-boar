# IT governance and service management alignment

**Português (Brasil):** [ITSM_GOVERNANCE_ALIGNMENT.pt_BR.md](ITSM_GOVERNANCE_ALIGNMENT.pt_BR.md)

**Audience:** DPO, CISO, IT director, external auditor, GRC consultant.

**Primer (concepts):** [GOVERNANCE_SERVICE_MANAGEMENT_PRIMER.md](GOVERNANCE_SERVICE_MANAGEMENT_PRIMER.md) · **Regulatory labels:** [COMPLIANCE_FRAMEWORKS.md](COMPLIANCE_FRAMEWORKS.md) · **GRC JSON contract:** [GRC_EXECUTIVE_REPORT_SCHEMA.md](GRC_EXECUTIVE_REPORT_SCHEMA.md)

**Positioning:** Conceptual reference only — **not** certified audit, **not** legal advice.

---

## 1. Sustainable value in ITSM terms

[ITIL 4](https://www.axelos.com/certifications/itil-service-management) describes value as **co-creation** between provider and consumer:

> **Value** = **Utility** (fit for purpose) + **Warranty** (fit for use)

| Dimension | Data Boar contribution |
| --------- | ---------------------- |
| **Utility** | Surfaces **where** personal/sensitive data appear across configured **targets** |
| **Warranty** | Repeatable runs, bounded sampling, per-session **Audit Trail** |
| **Co-creation** | Findings gain executive meaning when mapped to **controls** and **norm_tag** frameworks — optional **Governance Lens** (Pro/Enterprise) |

**Continual improvement loop:** Plan scope → Execute scan (**Data Sniffing** / **Deep Boring** — [GLOSSARY.md](GLOSSARY.md)) → Measure (Excel, heatmap, GRC JSON) → Improve (`--diff`, remediation, re-scan). See [GOVERNANCE_SERVICE_MANAGEMENT_PRIMER.md](GOVERNANCE_SERVICE_MANAGEMENT_PRIMER.md).

---

## 2. Framework alignment (summary tables)

### 2.1 ISO/IEC 38500 — IT governance principles

| Principle | Evidence the product helps produce |
| --------- | ---------------------------------- |
| **Responsibility** | Findings tied to **`target_name`** — highlights systems without documented data owner |
| **Strategy** | Baseline heatmaps / trends for security investment |
| **Performance** | Session **`--diff`** between runs |
| **Conformity** | **`norm_tag`** rows (LGPD, GDPR, sector samples) |
| **Human behaviour** | Findings in **non-production** targets when policy expects parity |

### 2.2 ISO/IEC 27014 — Information security governance

| Process | Contribution |
| ------- | ------------ |
| **Assess** | Automated PII/sensitive-data exposure inventory |
| **Direct** | GRC-oriented exports inform masking/test-data policy |
| **Monitor** | Recurring scans + session comparison |
| **Communicate** | Governance Lens narrative (tier-gated roadmap) |
| **Assure** | Exportable **Audit Trail** for external audit |

### 2.3 COBIT 2019 — Selected objectives

| Objective | Contribution |
| --------- | ------------ |
| **APO13** (Manage security) | Baseline findings for ISMS scope; remediation rows in GRC exports |
| **DSS05** (Manage security services) | Evidence of weak auth contexts, non-prod PII exposure |
| **MEA03** (Monitor compliance) | **`norm_tag`** + stable [GRC_EXECUTIVE_REPORT_SCHEMA.md](GRC_EXECUTIVE_REPORT_SCHEMA.md) |

### 2.4 ITIL 4 — Information security management practice

| Activity | Contribution |
| -------- | ------------ |
| Classify information assets | Inventory of targets with sensitivity breakdown |
| Assess/treat risk | Risk matrix fields in GRC JSON (P0/P1/P2 style) |
| Continual improvement | `--diff` between sessions |

**Service Value Chain (SVC) touchpoints:** **Engage** (`--validate-config`); **Design & Transition** (control targets per finding type — Lens roadmap); **Deliver & Support** (operational scan service); **Improve** (trend/diff).

### 2.5 ISO/IEC 20000-1 — Service management

| Topic | Contribution |
| ----- | ------------ |
| **Knowledge** | Findings export to corporate DB (*findings sink* — Pro tier) |
| **Configuration** | Targets as configuration items lacking security attributes |
| **Change** | Pre/post change session diff |

### 2.6 BACEN Resolution 4.893/2021 (Brazilian fintech — Enterprise framing)

Pair technical discovery with [compliance samples](compliance-samples/) and counsel on **cybersecurity policy** and **incident communication** obligations. Product does **not** certify BACEN compliance.

---

## 3. Audience positioning (elevator lines)

| Reader | Message |
| ------ | ------- |
| **Board / executive (ISO 38500)** | Periodic technical evidence for governance principles — does **not** replace formal IT governance programme |
| **DPO / CISO (ISO 27014 + LGPD)** | GRC-oriented session outputs mapped to assess/communicate processes |
| **External auditor (COBIT MEA03)** | Immutable Audit Trail + stable GRC schema traceability |
| **ITSM manager (ITIL 4 / ISO 20000)** | Recurring scan closes measure→improve loop |

---

## 4. Outputs mapped to audience

| Output | Format | Primary audience | Framework hook |
| ------ | ------ | ---------------- | -------------- |
| Standard Excel + heatmap | XLSX | Security analyst, ITSM | ISO 20000, ITIL 4 |
| GRC executive export | JSON (+ future DOCX/PDF via Lens) | DPO, CISO, auditor | ISO 27014, COBIT |
| Audit Trail | SQLite + optional export | Auditor, legal | ISO 38500, COBIT MEA03 |
| DSAR export | JSON | DPO | LGPD Art. 18, GDPR Art. 15 |
| Findings sink | DB connector (Pro) | CMDB/data team | ISO 20000 configuration |

Details: [REPORTS_AND_COMPLIANCE_OUTPUTS.md](REPORTS_AND_COMPLIANCE_OUTPUTS.md).

---

## 5. Related documentation

- [GOVERNANCE_SERVICE_MANAGEMENT_PRIMER.md](GOVERNANCE_SERVICE_MANAGEMENT_PRIMER.md)
- [COMPLIANCE_AND_LEGAL.md](COMPLIANCE_AND_LEGAL.md)
- [DECISION_MAKER_VALUE_BRIEF.md](DECISION_MAKER_VALUE_BRIEF.md)
- [USAGE.md](USAGE.md) — CLI (`--diff`, `--validate-config`, `--export-dsar`)
- [GLOSSARY.md](GLOSSARY.md) — COBIT, ITIL 4, Governance Lens, ISO 38500 / 27014
