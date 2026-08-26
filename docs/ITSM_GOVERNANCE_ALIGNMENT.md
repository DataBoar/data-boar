# IT and service-management governance alignment

**Português (Brasil):** [ITSM_GOVERNANCE_ALIGNMENT.pt_BR.md](ITSM_GOVERNANCE_ALIGNMENT.pt_BR.md)

**Audience:** DPO, CISO, IT director, external auditor, GRC consultant.

**Technical companion:** [COMPLIANCE_FRAMEWORKS.md](COMPLIANCE_FRAMEWORKS.md) ([pt-BR](COMPLIANCE_FRAMEWORKS.pt_BR.md))

**GRC report schema:** [GRC_EXECUTIVE_REPORT_SCHEMA.md](GRC_EXECUTIVE_REPORT_SCHEMA.md) ([pt-BR](GRC_EXECUTIVE_REPORT_SCHEMA.pt_BR.md))

**Note:** This document is conceptual positioning. It is **not** a certified audit and **not** legal advice.

---

## 1. Data Boar and sustainable value creation in ITSM

### 1.1 What “value” means in service management

ITIL 4 frames value as **co-creation** between provider and customer:

> Value = Utility (fit for purpose) + Warranty (fit for use)

In the Data Boar context:

- **Utility:** locates possible PII / sensitive data where the organisation did not already see it.
- **Warranty:** repeatable execution, immutable Audit Trail, session-traceable results.
- **Co-creation:** a technical finding has value only when translated into business language and control action.

### 1.2 Sustainable value — the cycle

```text
Plan → Execute → Measure → Improve → (loop)
```

A one-off annual scan creates **ephemeral** value. A sustainable cycle:

1. **Plan:** define target scope, compliance profile, response SLA.
1. **Execute:** Data Sniffing + Deep Boring (one scan session).
1. **Measure:** GRC report — findings × controls × frameworks.
1. **Improve:** compare sessions (`--diff`), close gaps, re-scan.
1. **Return to 1** with widened scope.

---

## 2. Alignment by framework

### 2.1 ABNT NBR ISO/IEC 38500 — IT governance

The standard sets **six principles** for the governing body. Data Boar can contribute **evidence** on the following (product does **not** certify board conformance):

| Principle           | How Data Boar can contribute                                           | Evidence artefact                                   |
| ---------           | ----------------------------                                           | -----------------                                   |
| **Responsibility**  | Surfaces targets without a documented data owner (CMDB gap)            | Findings with `target_name` and no documented owner |
| **Strategy**        | PII-exposure baseline for security investment decisions                | GRC report with heatmap and trend                   |
| **Performance**     | Measures posture change between sessions                               | `--diff session_a session_b`                        |
| **Conformance**     | Evidence of findings tagged against LGPD Arts. 46–47 (when configured) | `norm_tag` per finding + Governance Lens            |
| **Human behaviour** | Surfaces personal data in dev/QA (policy gap)                          | Findings on `nonprod` targets                       |

### 2.2 ABNT NBR ISO/IEC 27014 — information-security governance

Five governance processes and where Data Boar can act:

| Process         | Data Boar contribution                                                |
| -------         | ----------------------                                                |
| **Evaluate**    | Automated PII-exposure inventory — baseline for risk assessment       |
| **Direct**      | GRC report with control gaps → input for test-data and masking policy |
| **Monitor**     | Scheduled scans + session comparison                                  |
| **Communicate** | Governance Lens: technical findings in DPO / board language           |
| **Assure**      | Immutable Audit Trail exportable as evidence for an external auditor  |

### 2.3 COBIT 2019 — relevant control objectives

#### APO13 — Manage security

| COBIT practice                       | Contribution                                                  |
| --------------                       | ------------                                                  |
| APO13.01 Establish an ISMS           | Findings baseline as a formal starting point for an ISMS      |
| APO13.02 Risk treatment plan         | Remediation roadmap in the GRC report with owner and due date |
| APO13.03 Monitor and review the ISMS | Recurring scan + session diff                                 |

#### DSS05 — Manage security services

| COBIT practice                             | Contribution                                            |
| --------------                             | ------------                                            |
| DSS05.02 Network and connectivity security | Findings on APIs without evidenced auth (when in scope) |
| DSS05.04 Identity and access               | PII in non-prod without prod-equivalent controls        |
| DSS05.07 Monitor security events           | Scan integrated into a CI/CD pipeline                   |

#### MEA03 — Monitor, evaluate and assess compliance

| COBIT practice                            | Contribution                                                              |
| --------------                            | ------------                                                              |
| MEA03.01 Identify compliance requirements | `norm_tag` per finding (LGPD, GDPR, CCPA, BACEN, PCI-DSS when configured) |
| MEA03.04 Obtain assurance of compliance   | Audit Trail + GRC report as a formal evidence artefact                    |

### 2.4 ITIL 4 — information security management practice

| ITIL 4 activity                          | Data Boar contribution                                                                           |
| ---------------                          | ----------------------                                                                           |
| Identify and classify information assets | Target inventory with findings by PII type                                                       |
| Classify and treat risks                 | Risk matrix in the GRC report (P0/P1/P2 + framework reference)                                   |
| Control access to information            | Gap: targets without documented access control                                                   |
| Respond to incidents                     | Findings with LGPD Art. 48 `norm_tag` (when configured) as an early warning of notification duty |
| Continual improvement                    | Session `--diff` shows posture change                                                            |

#### Mapping to the Service Value Chain (SVC)

| SVC activity        | Data Boar role                                                         |
| ------------        | --------------                                                         |
| Engage              | `--validate-config` — operator validates configuration before the scan |
| Design & Transition | Governance Lens defines target controls per finding type               |
| Deliver & Support   | Recurring scan as a managed PII-monitoring service                     |
| Improve             | Session diff + trending in the report                                  |

### 2.5 ABNT NBR ISO/IEC 20000-1 — IT service management

| ISO 20000 area           | Contribution                                                            |
| --------------           | ------------                                                            |
| Knowledge management     | Findings exported to a corporate CMDB/DB (findings sink, when licensed) |
| Configuration management | Identifies CIs (targets) without security attributes in the CMDB        |
| Change management        | Session diff before/after production changes                            |

### 2.6 BACEN Resolution 4.893/2021 (Pro / Enterprise — Brazilian fintech context)

Reference: [SENSITIVITY_DETECTION.md](SENSITIVITY_DETECTION.md) and Governance Lens **Enterprise** maps (curated; not Open Core).

| BACEN article (as commonly cited in workshops) | Contribution                                   |
| ---------------------------------------------  | ------------                                   |
| Art. 4 — cybersecurity policy                  | Findings baseline as input to policy           |
| Art. 6 — incident action and response plan     | PII in non-prod API/DB as a plan trigger       |
| Art. 11 — incident communication to BACEN      | Audit Trail as detection-and-response evidence |

---

## 3. Positioning by audience

### Board / directors (ISO 38500)

> Data Boar supplies **periodic technical evidence** toward IT-governance principles — especially Responsibility, Conformance, and Performance — without replacing a formal governance programme.

### DPO / CISO (ISO 27014 + LGPD)

> Each scan session can produce a GRC report with control gaps mapped to ISO 27014, COBIT DSS05, and relevant LGPD articles (when tagged) — input to **Evaluate** and **Communicate** in information-security governance.

### External auditor (COBIT MEA03)

> An immutable Audit Trail and a stable GRC schema ([GRC_EXECUTIVE_REPORT_SCHEMA.md](GRC_EXECUTIVE_REPORT_SCHEMA.md)) let an auditor trace findings to COBIT practices and regulatory tags — without relying on ad-hoc log interpretation.

### IT / ITSM manager (ITIL 4 + ISO 20000)

> Recurring scans close an ITIL 4 improvement loop: Deliver → Measure (GRC report) → Improve (close gaps) → Deliver again with a better posture.

---

## 4. Outputs mapped by audience

| Output                       | Format               | Primary audience             | Framework reference                |
| ------                       | ------               | ----------------             | -------------------                |
| GRC report (Governance Lens) | DOCX / ODT / PDF     | DPO, CISO, auditor           | ISO 27014, COBIT APO13/DSS05       |
| Excel with heatmap           | XLSX / ODS           | IT manager, security analyst | ISO 20000, ITIL 4                  |
| Exportable Audit Trail       | JSON / YAML          | External auditor, legal      | ISO 38500, COBIT MEA03             |
| Findings sink (corporate DB) | PostgreSQL / MongoDB | Data team, CMDB              | ISO 20000 configuration management |
| DSAR export                  | Structured JSON      | DPO, legal                   | LGPD Art. 18, GDPR Art. 15         |

---

## 5. Related resources

- [COMPLIANCE_FRAMEWORKS.md](COMPLIANCE_FRAMEWORKS.md) — regulatory frameworks (LGPD, GDPR, CCPA)
- [COMPLIANCE_AND_LEGAL.md](COMPLIANCE_AND_LEGAL.md) — legal posture (not advice)
- [GRC_EXECUTIVE_REPORT_SCHEMA.md](GRC_EXECUTIVE_REPORT_SCHEMA.md) — GRC JSON contract
- [DECISION_MAKER_VALUE_BRIEF.md](DECISION_MAKER_VALUE_BRIEF.md) — leadership brief
- [REPORTS_AND_COMPLIANCE_OUTPUTS.md](REPORTS_AND_COMPLIANCE_OUTPUTS.md) — pipeline outputs
- [SENSITIVITY_DETECTION.md](SENSITIVITY_DETECTION.md) — detection patterns and `norm_tag`
- [GLOSSARY.md](GLOSSARY.md) — ITSM / ISMS terms (EDM, SVS, SLA, Governance Lens)
- Governance Lens **implementation** sequencing lives in the maintainer PMO index ([README.md](README.md) *Internal and reference*) — not linked here ([ADR 0004](adr/ADR-0004-external-docs-no-markdown-links-to-plans.md)).
