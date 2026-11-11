# Primer: Data Boar in the data-governance ecosystem (DMBOK, ISO/IEC 38505, governance vs management)

<!-- plans-hub-summary: Data Boar positioning for data-governance practitioners (GGD, DPOs, TCC reviewers); governance vs management, DMBOK areas, normative anchors, Data Governance Act, open data -->

**Status:** Active
**Date:** 2026-11-10
**Authors:** Fabio Leitao
**Priority:** H2
**Depends on:** ADR-0004, ADR-0035, ADR-0050, ADR-0058, ADR-0070
**GitHub:** [#752](https://github.com/DataBoar/data-boar/issues/752)

**Português (Brasil):** [DATA_GOVERNANCE_PRIMER.pt_BR.md](DATA_GOVERNANCE_PRIMER.pt_BR.md)

**Audience:** Data-governance professionals (GGD), DPOs with DMBOK background, academic reviewers (TCC at PUC-Rio), and data-governance consultants. These readers arrive from the data-governance discipline — not from cybersecurity — and know DMBOK, ISO/IEC 38505, and the distinction between governance and management.

**Tone:** Professional, evidence-oriented. No mascot. No verbatim DAMA wheel, no ISO clause dump. Official starting points: [DAMA Body of Knowledge](https://www.dama.org/cpages/body-of-knowledge), [ISO/IEC 38505](https://www.iso.org/standard/56639.html), [Data Governance Act EU 2022/868](https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32022R0868).

---

## 1. Data management vs data governance — distinction

Based on DAMA International (DMBOK, 2nd ed., 2017) and ISO/IEC 38505:

- **Data management**: operational control of day-to-day data activities (backup, availability, quality execution, pipelines). Responsible: data managers and technical teams.
- **Data governance**: periodic monitoring to ensure data activities are aligned with organisational strategy, operating at acceptable risk, and contributing to objectives. Responsible: senior leadership, DPO, board. Defined by DAMA as "the exercise of authority, control (planning, monitoring, oversight) over the management of data assets."

Data Boar serves both levels:

- **Management**: the scan itself — collection, sampling, findings at operational level.
- **Governance**: executive report + compliance grade report + APG delivered to senior leadership as governance indicators.

| Dimension | Governance | Management |
| --------- | ---------- | ---------- |
| Level | Strategic / periodic | Operational / continuous |
| Core question | Is the area aligned with strategy? | Are activities being executed? |
| Frequency | Periodic reviews · key indicators | Day-to-day |
| Accountable | Senior leadership · board | Managers & technical teams |
| Data Boar role | Evidence for EDM cycle | Operational data visibility |

**SVG** (hierarchy — A governs B): [data_boar_governance_vs_management.svg](../assets/diagrams/data_boar_governance_vs_management.svg) (companion, optional).

---

## 2. Data Boar across the 11 DMBOK knowledge areas

From [databoar-dmbok-diagrams.md](../assets/diagrams/databoar-dmbok-diagrams.md) section 1. Three zones:

| Zone | Knowledge area | Data Boar role |
| ---- | -------------- | -------------- |
| **Core** | Data governance | `scan_manifest`, GRC-oriented report, auditable session metadata |
| **Core** | Data security | PII/sensitive discovery; exposure by source and pattern type |
| **Core** | Metadata management | `norm_tag`, plugin schema, sensitivity profile on findings |
| Contributes | Data architecture | Inventory of configured origins as input to architecture work |
| Contributes | Storage and operations | Scans of databases, files, and stream-adjacent targets you configure |
| Contributes | Integration & interoperability | Connectors and plugins per source |
| Contributes | Data quality | Sensitivity profile as **one** quality/risk dimension — not a DQ scorecard |
| Context | Data modelling & design | — |
| Context | Documents & content | — (except when you point a filesystem/API target at those stores) |
| Context | Reference & master data | — |
| Context | Data warehousing & BI | Optional BI connectors when configured; not a warehouse platform |

*Labels above are this repo's grouping (core / contributes / context). They are **not** a reproduction of DAMA's published area names or diagrams.*

---

## 3. Normative anchors

- **ISO/IEC 38505** (governance of data): extends ISO/IEC 38500 principles to the data domain. Catalogue: [ISO/IEC 38505](https://www.iso.org/standard/56639.html).
- **ISO/IEC 27701:2019** (privacy information management — PIMS): extends ISO/IEC 27001 for PII governance. Catalogue: [ISO/IEC 27701:2019](https://www.iso.org/standard/71670.html).
- **ISO/IEC 25012** (data quality model): quality as a governance dimension. Catalogue: [ISO/IEC 25012](https://www.iso.org/standard/35736.html).
- **DAMA DMBOK 2nd ed. (2017)**: the canonical framework. [DAMA Body of Knowledge](https://www.dama.org/cpages/body-of-knowledge).
- **LGPD** (Lei 13.709/2018), **GDPR** (EU 2016/679): regulatory context.

---

## 4. Data Governance Act (EU, Regulation 2022/868)

Regulation (EU) 2022/868. Governs **data intermediation services**, **data altruism**, and **re-use of public-sector data**. Complements GDPR at the ecosystem level. Relevant for organisations operating across EU and Brazil simultaneously.

Data Boar's discovery capability supports the **auditability** requirements of this regulation.

Reference: [Regulation (EU) 2022/868](https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32022R0868).

---

## 5. Open data — brief framing

Open data as a governance concept: data made available without restrictions. Relevant for Data Boar's open-core model (open scanner, proprietary reporting layer). Normative anchor: [W3C Data on the Web Best Practices](https://www.w3.org/TR/dwbp/).

---

## 6. Data Boar positioning statement for this audience

> "Data Boar is the discovery and evidence layer that makes data governance verifiable. It does not replace a GGD function — it provides the inventory, exposure baseline, and audit trail that a GGD function requires to exercise oversight with evidence."

---

## Cross-references

- [databoar-dmbok-diagrams.md](../assets/diagrams/databoar-dmbok-diagrams.md) — DMBOK zones and governance vs management diagram
- [databoar-governance-diagrams.md](../assets/diagrams/databoar-governance-diagrams.md) — IT governance stack and EDM cycle mapping
- [COMPLIANCE_AND_LEGAL.md](../COMPLIANCE_AND_LEGAL.md) — regulatory alignment, ISO/IEC 27701, 25012, Data Governance Act
- [DECISION_MAKER_VALUE_BRIEF.md](../DECISION_MAKER_VALUE_BRIEF.md) — executive positioning
- [ADR-0025](../adr/ADR-0025-compliance-positioning-evidence-inventory-not-legal-conclusion-engine.md) — "evidence and inventory, not legal conclusion" posture

---

*Original wording — does not reproduce DAMA or ISO text. All normative references with year and URL.*