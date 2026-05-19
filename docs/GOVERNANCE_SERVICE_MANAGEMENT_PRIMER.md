# Governance and service management primer

**Português (Brasil):** [GOVERNANCE_SERVICE_MANAGEMENT_PRIMER.pt_BR.md](GOVERNANCE_SERVICE_MANAGEMENT_PRIMER.pt_BR.md)

**Audience:** DPO, CISO, IT director, GRC lead, external auditor — readers who already use [COMPLIANCE_FRAMEWORKS.md](COMPLIANCE_FRAMEWORKS.md) for **privacy law** labels and need a **service-management** lens for the same scan outputs.

**Not legal advice.** This page explains **how organisations talk about IT value and controls**; it does **not** certify ISO, COBIT, ITIL, or BACEN outcomes.

---

## Three layers (do not collapse them)

| Layer | Question it answers | Data Boar role |
| ----- | ------------------- | -------------- |
| **Privacy / sector law** | Which statute or regulator applies to the processing? | **`norm_tag`**, compliance samples, recommendation overrides — [COMPLIANCE_FRAMEWORKS.md](COMPLIANCE_FRAMEWORKS.md) |
| **Information security management** | How is the ISMS/PIMS built and evidenced? | Discovery, **metadata-only findings**, heatmaps — [COMPLIANCE_FRAMEWORKS.md#auditable-and-management-standards-supporting-role](COMPLIANCE_FRAMEWORKS.md#auditable-and-management-standards-supporting-role) |
| **IT governance & service management** | How does IT co-create **durable value** with the business and prove control operation? | Session **Audit Trail**, repeatable scans, optional **Governance Lens** exports (Pro/Enterprise — see [LICENSING_SPEC.md](LICENSING_SPEC.md)); alignment tables in [ITSM_GOVERNANCE_ALIGNMENT.md](ITSM_GOVERNANCE_ALIGNMENT.md) |

Counsel still decides **law**; the board still owns **governance**; IT still owns **service design**. The product supplies **technical evidence** that those functions can consume without re-typing spreadsheet archaeology.

---

## Minimum viable organisational capacity (why “one annual scan” fails)

Mature programmes treat discovery as a **loop**, not a project:

1. **Plan** — scope targets, compliance profile, who owns remediation.
2. **Execute** — bounded **Data Sniffing** (connectors + sampling + detection).
3. **Measure** — Excel/GRC artefacts, heatmaps, optional executive JSON ([GRC_EXECUTIVE_REPORT_SCHEMA.md](GRC_EXECUTIVE_REPORT_SCHEMA.md)).
4. **Improve** — compare sessions (`--diff`), close gaps, widen scope.

**Toil** (manual, repetitive inventory work) is what this loop automates; see **toil** in [GLOSSARY.md](GLOSSARY.md). External cron on another host is valid, but it is **not** the only pattern — scheduled scans are a **product roadmap** item (tier-gated); until then, operators trigger runs via CLI/API or their own orchestrator.

---

## Framework stack (reference map)

| Framework | Typical owner | One-line fit for Data Boar |
| --------- | ------------- | -------------------------- |
| **ISO/IEC 38500** | Board / executive | Evidence for **responsibility**, **performance**, **conformity** principles — not board decisions |
| **ISO/IEC 27014** | CISO / security governance | **Assess → Direct → Monitor → Communicate → Assure** fed by inventory and Audit Trail |
| **COBIT 2019** | GRC / audit | Control objectives (e.g. **APO13**, **DSS05**, **MEA03**) mapped to findings and reports |
| **ITIL 4** | Service management | **Service value** co-creation; security practice + **continual improvement** via session compare |
| **ISO/IEC 20000-1** | ITSM | Configuration/knowledge inputs — targets as configuration items, exports to corporate DB sinks (Pro) |
| **BACEN Res. 4.893/2021** | Brazilian fintech security | Sector **cyber** policy inputs — pair with LGPD samples; Enterprise-tier Governance Lens framing |

Official titles and ABNT NBR adoption in Brazil: [GLOSSARY.md](GLOSSARY.md) §10. Deep mapping tables: [ITSM_GOVERNANCE_ALIGNMENT.md](ITSM_GOVERNANCE_ALIGNMENT.md).

---

## Governance Lens (commercial tier)

**Governance Lens** is the planned **executive GRC narrative** layer on top of standard Excel/metadata outputs — **Pro** and **Enterprise** feature keys in the licensing map (`governance_lens_pro`, `governance_lens_enterprise`). It translates technical findings into **control-gap language** for DPO/CISO/audit readers.

Today the engine already produces inventory-grade evidence; Lens packaging (DOCX/PDF executive brief) ships when the report module is available. Until then, use [GRC_EXECUTIVE_REPORT_SCHEMA.md](GRC_EXECUTIVE_REPORT_SCHEMA.md) and [REPORTS_AND_COMPLIANCE_OUTPUTS.md](REPORTS_AND_COMPLIANCE_OUTPUTS.md).

---

## Related documentation

- [ITSM_GOVERNANCE_ALIGNMENT.md](ITSM_GOVERNANCE_ALIGNMENT.md) — per-framework contribution tables
- [COMPLIANCE_FRAMEWORKS.md](COMPLIANCE_FRAMEWORKS.md) — regulations and samples
- [DECISION_MAKER_VALUE_BRIEF.md](DECISION_MAKER_VALUE_BRIEF.md) — leadership narrative
- [REPORTS_AND_COMPLIANCE_OUTPUTS.md](REPORTS_AND_COMPLIANCE_OUTPUTS.md) — artefact catalogue
- [GLOSSARY.md](GLOSSARY.md) — ITSM/GRC terms (§9–10)
