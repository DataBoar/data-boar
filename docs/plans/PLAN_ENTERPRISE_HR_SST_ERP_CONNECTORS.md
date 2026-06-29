# Plan: Enterprise back-office connectors (SST, HR, ERP, CRM, folha, helpdesk, URM)

**Status:** Deferred
**Date:** 2026-03-21
**Authors:** Fabio Leitao
**Priority:** H3

**Synced with:** [PLANS_TODO.md](PLANS_TODO.md)

**Related plans:** [PLAN_SAP_CONNECTOR.md](PLAN_SAP_CONNECTOR.md) (SAP in the data soup), [PLAN_ADDITIONAL_DATA_SOUP_FORMATS.md](completed/PLAN_ADDITIONAL_DATA_SOUP_FORMATS.md) (file formats), [PLAN_SCOPE_IMPORT_FROM_EXPORTS.md](completed/PLAN_SCOPE_IMPORT_FROM_EXPORTS.md) (bootstrap scope from ITSM/monitoring **exports** — not live ERP sampling), [PLAN_DATABRICKS_UNITY_LAKEHOUSE_SCOPE_AND_SCAN.md](PLAN_DATABRICKS_UNITY_LAKEHOUSE_SCOPE_AND_SCAN.md) (lakehouse SQL scan + catalog-driven scope — **substrate**, not live HR/ERP APIs), existing REST/SQL connector patterns in [ADDING_CONNECTORS.md](../ADDING_CONNECTORS.md).

**When implementing any step:** update USAGE / TECH_GUIDE / SECURITY as needed, add tests, then update this file and PLANS_TODO.md.

---

## Clarification: SOC (software) ≠ SOX (Sarbanes-Oxley)

| Term                                            | Meaning                                                                                                                                            | Relevance to Data Boar                                                                                                                                                                                                                                                                                                                                                                                                        |
| ----                                            | -------                                                                                                                                            | ----------------------                                                                                                                                                                                                                                                                                                                                                                                                        |
| **SOC** ([soc.com.br](https://www.soc.com.br/)) | **S**oftware / suite used in Brazil for **Saúde e Segurança do Trabalho** (occupational health, ASO, eSocial, FAP, EPI, etc.).                     | Potential **technical integration target** (API, DB, exports) to discover where employee health and workplace-safety data live and how they are protected.                                                                                                                                                                                                                                                                    |
| **SOX** (Sarbanes-Oxley Act, US)                | US **securities** law: financial reporting integrity, internal controls over financial reporting (ICFR), IT general controls (ITGC), audit trails. | **Not a “database product” to connect to.** Alignment is **process and evidence**: scans can support **ITGC / access reviews** (who has access to which systems, segregation of duties signals) if we later add connectors that expose **metadata** (roles, permissions, change logs). Full SOX compliance is outside a single scanner scope; we can **document** how findings feed DPO + InfoSec + Internal Audit workflows. |

**Conclusion:** Integrating **SOC** addresses **LGPD / health data / labour compliance** mapping. **SOX** is a separate compliance frame; the product can remain **compatible** by emphasizing read-only discovery, audit logs of scanner actions, and reports that **do not** become a new uncontrolled copy of sensitive data—see “Data minimisation” below.

---

## Does this make sense?

**Yes, strategically**—if scoped as **risk and governance discovery**, not as “ingest full medical records into Excel.”

Many Brazilian and global enterprises store **highly sensitive** personal data in:

- **SST / occupational health** (e.g. SOC, peers, clinic systems),
- **HR / payroll / time** (e.g. LG lugar de gente, Coalize, BMA, Nasajon HR modules, TOTVS RH, exports from folha systems),
- **ERP / CRM** (TOTVS, Nasajon, SAP, Salesforce-style CRMs),
- **ITSM / helpdesk** (GLPI, Movidesk, Zendesk, Jira SM, etc.),
- **Endpoint / productivity / URM** tools (e.g. Trauma Zer0 class—**high legal and ethical sensitivity**; often **employee monitoring**).

## Value for the data soup:

- Same **pattern** as today: discover structures → **bounded samples** → regex / ML → findings + recommendations.
- **DPO-oriented:** where sensitive categories likely exist, retention/access risks, and **which legal bases / norms** are implicated if data is leaked (LGPD Arts. 5, 9–11; GDPR health/special categories where applicable; NR-1 / labour health context in Brazil—**as documentation**, not legal advice).

## Risks if mis-scoped:

- Turning the scanner into a **second copy** of health data or intrusive monitoring content.
- **Licencing / ToS** of vendor APIs (some forbid bulk export or require specific SKUs).
- **Works council / privacy** reviews for URM-class tools.

---

## Guiding principles (before any implementation)

1. **Data minimisation by default:** Prefer **metadata scans** (table/field names, entity names, **hashed or redacted** samples, row counts) over full text of clinical notes. Offer explicit **opt-in** for deeper sampling where legally justified and contractually allowed.
1. **Read-only and least privilege:** Same as databases—credentials with minimal read scope; document required roles per vendor.
1. **Separation of concerns:** **Detection** (what might be sensitive) vs **legal qualification** (final Art. 9 LGPD assessment remains with DPO/counsel). Reports should use **conditional wording** (“possible special-category / health-like field”) where appropriate.
1. **Vendor reality:** Each product exposes **different** surfaces—REST/OData, SOAP, proprietary SDK, **read-only SQL replica**, CSV/Excel **exports** dropped on a share (already scannable via filesystem). No one-size-fits-all; plan per **category** then per **priority vendor**.
1. **URM / productivity tools:** Treat as **separate tier**—highest controversy; may be limited to **config + policy checklist** in reports unless the customer explicitly enables and has legal basis.

---

## Categories and representative systems (examples only)

> Lists such as [iDinheiro ERP](https://www.idinheiro.com.br/negocios/sistemas-erps/), [Leadster CRM](https://leadster.com.br/blog/melhores-crm-de-vendas/), [Coalize folha](https://www.coalize.com.br/automatizacao-da-folha-de-pagamento), [BMA](https://bmasistemas.com.br/), [LG lugar de gente](https://www.lg.com.br/), [Jestor helpdesk](https://blog.jestor.com/melhores-ferramentas-de-gestao-de-tickets-internos-e-suporte/), [Trauma Zer0](https://www.traumazero.com/) are **market references**; integration feasibility depends on **each vendor’s API** and customer contract—not on inclusion in this plan.

| Category                          | Example ecosystems                     | Likely integration surfaces                                                | Notes                                                                                    |
| --------                          | -------------------                    | ---------------------------                                                | -----                                                                                    |
| **SST / occupational health**     | SOC, others                            | REST/API (if licensed), partner integration docs, DB replica, export files | Strong LGPD Art. 11; minimise clinical content in samples.                               |
| **ERP (finance + operations)**    | TOTVS, Nasajon, SAP, Omie-class        | SQL (reporting DB), OData, proprietary APIs                                | Often overlaps with existing SQL path; “connector” may be **documented views** + config. |
| **CRM**                           | RD Station CRM, Salesforce-class, etc. | REST + OAuth                                                               | Similar to Dataverse / REST connector pattern.                                           |
| **HR / folha / ponto**            | LG, Coalize, BMA, Calima-class         | API, file exports, sometimes SQL                                           | High concentration of PII + salary + health-adjacent data.                               |
| **Helpdesk / ITSM**               | GLPI, Movidesk, Zendesk, Jira SM       | REST, webhooks                                                             | Tickets may contain PII; sample limits critical.                                         |
| **URM / productivity monitoring** | Trauma Zer0-class                      | Agent APIs, DB, exports                                                    | Legal review first; possibly **checklist-only** phase.                                   |

---

## What we could deliver (phased, not committed until prioritised)

### Phase A – Research and architecture (no product code required)

| #   | To-do                                                                                                                                                                                      | Status    |
| --- | -----                                                                                                                                                                                      | ------    |
| A.1 | **Per category:** List top 2–3 priority vendors for Brazilian enterprise customers; capture **public** integration docs (API type, auth, rate limits).                                     | ⬜ Pending |
| A.2 | **Map each to access pattern:** API vs SQL replica vs “export folder + filesystem scan” (zero code).                                                                                       | ⬜ Pending |
| A.3 | **Define “risk-only” finding shape:** e.g. `data_category_hint`, `regulatory_hints` (doc strings, not legal opinions), `recommended_controls` (encryption, access review, DLP, retention). | ⬜ Pending |
| A.4 | **SOX note:** Document how future **access/metadata** findings could support ITGC narratives; state limits (we are not a SOX audit tool).                                                  | ⬜ Pending |

### Phase B – Generic enablers (reuse across vendors)

| #   | To-do                                                                                                                           | Status    |
| --- | -----                                                                                                                           | ------    |
| B.1 | **OAuth2 / API key patterns:** Harden REST connector or add thin “generic OAuth REST” target if missing pieces.                 | ⬜ Pending |
| B.2 | **Optional “entity catalog” config:** Allow operator to list API entities/endpoints to scan (avoid discovery of entire tenant). | ⬜ Pending |
| B.3 | **Sampling policy per sensitivity tier:** e.g. health-like entities → field names only or max N chars redacted.                 | ⬜ Pending |

### Phase C – Pilot connectors (pick one after A)

| #   | To-do                                                                                                                             | Status    |
| --- | -----                                                                                                                             | ------    |
| C.1 | **Pilot 1 (TBD):** One vendor with **documented** REST + test tenant (could be CRM or ITSM before SOC).                           | ⬜ Pending |
| C.2 | **Pilot 2 – SOC or HR suite:** Subject to API access and customer pilot; fallback = **scan exports** on controlled share.         | ⬜ Pending |
| C.3 | **Reports:** Sheet or tags for “SST/HR/ERP” source family; link to recommendation library (COMPLIANCE_FRAMEWORKS / new appendix). | ⬜ Pending |

### Phase D – URM / monitoring (optional, last)

| #   | To-do                                                                                                                                  | Status    |
| --- | -----                                                                                                                                  | ------    |
| D.1 | **Policy module only:** Report section “URM tools detected / configured” from optional inventory config—not from intrusive collection. | ⬜ Pending |
| D.2 | **Integration:** Only if explicit legal basis + vendor API allows compliance-oriented metadata export.                                 | ⬜ Pending |

---

## Relationship to SAP and other backlog items

- **SAP** remains the first **named** enterprise ERP connector in [PLAN_SAP_CONNECTOR.md](PLAN_SAP_CONNECTOR.md). TOTVS / Nasajon may reuse **SQL/OData** patterns after SAP design is proven.
- This plan is the **umbrella** for Brazilian SST (SOC), adjacent HR/folha, CRM, helpdesk, and URM—so PLANS_TODO stays a single pointer.

---

## Summary

- **SOC (software)** integration is **feasible in principle** via API, database, or exports; it must be **heavily minimised** for health data.
- **SOX** is **not** the same as SOC; alignment is **governance and evidence**, not a connector named “SOX.”
- **ERP, CRM, folha, helpdesk, URM** fit the same **data soup** narrative with **category-specific** access patterns and **legal/ethical** guardrails—especially for URM.
- **Next step:** Phase A research only; **no implementation** until a pilot vendor and access method are chosen and documented here.

---

## Last updated

Plan created **2026-03-01**: consolidates operator request for SOC, ERP/CRM/folha/helpdesk/URM roadmap; explicit SOC vs SOX; phased research-first approach; no implementation commitment.
