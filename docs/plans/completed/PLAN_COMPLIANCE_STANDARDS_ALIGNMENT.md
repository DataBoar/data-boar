# Plan: Compliance standards alignment (ISO/IEC 27701, FELCA, auditable norms)

**Status:** Done (documentation; archived under `docs/plans/completed/`)
**Synced with:** [PLANS_TODO.md](../PLANS_TODO.md) (central to-do list)

## Purpose

Document how the product **supports** (does not certify) alignment with **auditable and management standards** such as **ISO/IEC 27701** (PIMS), **SOC 2**, and **FELCA** (Lei 15.211/2025 – Estatuto Digital da Criança e do Adolescente), and ensure the roadmap for decision-makers mentions these where relevant. No new runtime behaviour or code is required for the initial scope; this plan is **documentation- and roadmap-only**, sequenced for minimal token use.

---

## How we support these standards

### ISO/IEC 27701 (Privacy Information Management Systems (PIMS))

- **What it is:** International standard (2019; 2025 standalone edition) for establishing and operating a Privacy Information Management System. It requires PII controllers and processors to demonstrate accountability, manage privacy risks, and provide evidence (e.g. documented processing, DPIAs, cross-border transfer documentation).
- **Our role:** We do **not** certify organisations. We provide **discovery and mapping** of personal/sensitive data across sources (files, SQL, NoSQL, APIs, shares, etc.) and **metadata-only** reporting (where found, pattern type, sensitivity, norm tags). That supports **evidence-based accountability**: knowing where PII is and the scope of processing is a prerequisite for applying ISO/IEC 27701 controls and for audits. Our config-driven norm tags and recommendation overrides align with the regulations organisations declare under ISO/IEC 27701 (e.g. LGPD, GDPR, CCPA).

### SOC 2 (Service Organization Control 2)

- **What it is:** A widely used framework (AICPA) for reporting on controls relevant to security, availability, processing integrity, confidentiality, and privacy. SOC 2 Type I/II is a common pressure point for corporates (customers, procurement, and auditors expect evidence of control design and operation).
- **Our role:** We do **not** perform SOC 2 audits or issue reports on behalf of the organisation. We provide **discovery and mapping** of where personal or sensitive data resides and **metadata-only** reporting. That supports control design and audit preparation (e.g. evidence of data inventory and scope of processing). Norm tags and recommendation overrides can be aligned to the trust principles and criteria you use.

### FELCA (Lei 15.211/2025 – Estatuto Digital da Criança e do Adolescente)

- **What it is:** Brazilian law in force from 17 March 2026. It applies to digital platforms directed at or likely to be accessed by children and adolescents. It mandates age verification, prohibits certain practices (e.g. profiling/targeting minors), requires parental controls and privacy-by-default for minors, and transparency reporting to ANPD.
- **Our role:** We do **not** implement age verification or platform controls. We **discover and flag** where data that may relate to minors is stored or processed (e.g. date-of-birth columns, age fields, “possible minor” inference from DOB). Our **minor data detection** (LGPD Art. 14, GDPR Art. 8–related) and report outputs help organisations (a) map processing of minors’ data and (b) support transparency and accountability toward ANPD and internal audits. This is a **supporting capability** for FELCA-related compliance efforts.

### Other auditable or regional norms

- **Existing:** We already support many regional laws via [compliance-samples](../../compliance-samples/) and [COMPLIANCE_FRAMEWORKS.md](../../COMPLIANCE_FRAMEWORKS.md) (e.g. LGPD, GDPR, CCPA, UK GDPR, PIPEDA, POPIA, APPI, PCI-DSS, and others). Organisations can map our findings to SOC 2, ISO/IEC 27001/27002, or other control frameworks by using norm tags and recommendation overrides.
- **Future:** As new norms emerge (e.g. other regional child-protection or platform rules), we extend via config and samples; the plan does not mandate code changes for each new law.

### Other compliance to watch

- **Regional child-protection or platform laws** (beyond FELCA) may impose similar or stricter obligations (e.g. age verification, parental controls, transparency). Our minor-data detection and config-driven norm tags help you map scope; we extend samples and docs as norms become relevant.
- **Sector-specific rules** (e.g. health, finance, education) and **data-localisation or cross-border** requirements can affect where and how you process data. Use [compliance-samples](../../compliance-samples/) and recommendation overrides to align report text and norm tags; no code change is required to add new frameworks.

---

## Scope of this plan (token-aware)

- **In scope:** Document the above in COMPLIANCE_FRAMEWORKS (EN + pt-BR); add a short, on-brand mention in the **roadmap** sentence of the decision-makers pitch (README and README.pt_BR); add this plan and sequenced to-dos to PLANS_TODO.
- **Out of scope for this plan:** New code, new connectors, new report sheets, or certification claims. Optional future work (e.g. a dedicated “FELCA” or “minor data” filter in reports) can be a separate plan if needed.

---

## Implementation to-dos (sequenced)

| #   | To-do                                                                                                                                                                                                                                                 | Status   |
| --- | --------                                                                                                                                                                                                                                              | -------- |
| 1   | Add subsection “Auditable and management standards (supporting role)” in COMPLIANCE_FRAMEWORKS.md: ISO/IEC 27701 and FELCA paragraphs; link to this plan.                                                                                             | ✅ Done   |
| 2   | Add equivalent subsection in COMPLIANCE_FRAMEWORKS.pt_BR.md (natural pt-BR).                                                                                                                                                                          | ✅ Done   |
| 3   | Update roadmap sentence in README.md (decision-makers / “Why it holds up”): mention alignment with ISO/IEC 27701 (PIMS) and FELCA (minor-data mapping) documented; we continue to extend support for auditable and regional standards.                | ✅ Done   |
| 4   | Update roadmap sentence in README.pt_BR.md equivalently (on-brand, minimal change).                                                                                                                                                                   | ✅ Done   |
| 5   | In PLANS_TODO.md: add “Compliance standards alignment” to plan status and conflict/dependency table; add a short block with these to-dos; place in “What to start next” as smallest-scope (doc-only) so it can be done first under token constraints. | ✅ Done   |

---

## Conflict and placement in roadmap

- **Depends on:** Nothing (doc-only).
- **Conflicts with:** None.
- **Placement:** Documentation and pitch only; no change to scan/report behaviour or to other plans’ ordering. The roadmap sentence is extended once; future feature work (e.g. strong crypto, content-type, data source versions) remains as already sequenced in PLANS_TODO.
