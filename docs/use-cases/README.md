# Use-case storyboards (workshop flows)

**Português (Brasil):** [README.pt_BR.md](README.pt_BR.md)

Short **narrative storyboards** for POCs, sales-engineering workshops, and DPO/IT alignment. They are **illustrative** only: **not** legal advice and **not** a promise that any deployment matches the scenario or satisfies sector law (health, legal privilege, tax secrecy, etc.).

Each storyboard includes **Partner opportunity** (how to qualify a lead) and **Product alignment (maintainers)** (which shipped surfaces to stress first—without linking into `docs/plans/` from buyer-facing docs; see [docs/README.md](../README.md) *Internal and reference*).

**Product use cases** (scan → remediate → prove, tokenized exports, biometrics): [USE_CASES_HUB.md](USE_CASES_HUB.md) ([pt-BR](USE_CASES_HUB.pt_BR.md)).

## Index

| Storyboard | Focus | Typical Data Boar targets |
| ---------- | ----- | ------------------------- |
| [PORT_LOGISTICS_MULTINATIONAL_CREW.md](PORT_LOGISTICS_MULTINATIONAL_CREW.md) | Multinational crew, port-adjacent metadata tension | Databases, file shares, ticketing exports |
| [LAW_FIRM_CLIENT_MATTER_AND_TRUST_DATA.md](LAW_FIRM_CLIENT_MATTER_AND_TRUST_DATA.md) | Client matters, privilege hygiene, conflict checks | Document shares, mail archives, DMS exports, matter databases |
| [ACCOUNTING_FIRM_PAYROLL_TAX_AND_LEDGER.md](ACCOUNTING_FIRM_PAYROLL_TAX_AND_LEDGER.md) | Payroll, tax identifiers, general ledger | ERP/CSV exports, SQL payroll, shared drives |
| [PHARMA_SPECIALTY_SALES_HOSPITALS_AND_PATIENT_PROGRAMS.md](PHARMA_SPECIALTY_SALES_HOSPITALS_AND_PATIENT_PROGRAMS.md) | Specialty distribution to hospitals/pharmacies; optional patient-support paths | CRM, order history, program spreadsheets, REST exports |
| [MSP_IT_CONSULTANCY_MULTI_TENANT_SMB.md](MSP_IT_CONSULTANCY_MULTI_TENANT_SMB.md) | MSP / IT consultancy, many SMB tenants, repeat scans | Per-client shares, RMM exports, M365/Google dumps, SQL read-only copies |
| [INSURANCE_BROKER_AND_BENEFITS_ADMIN.md](INSURANCE_BROKER_AND_BENEFITS_ADMIN.md) | Claims, policies, beneficiaries; health-adjacent text | CRM, claims folders, spreadsheets, REST extracts |
| [RPO_PEOPLE_OPS_AND_PAYROLL_BUREAU.md](RPO_PEOPLE_OPS_AND_PAYROLL_BUREAU.md) | RPO / outsourced HR / payroll bureau across employers | ATS exports, onboarding packs, payroll CSV/SQL, HR shares |
| [REAL_ESTATE_AND_CONDOMINIUM_MANAGEMENT.md](REAL_ESTATE_AND_CONDOMINIUM_MANAGEMENT.md) | Rental / condo / property SMB, high document churn | Unit folders, contracts, consumption logs, simple CRM exports |
| [NGO_MIGRANT_WELCOME_AND_HUMANITARIAN_FILES.md](NGO_MIGRANT_WELCOME_AND_HUMANITARIAN_FILES.md) | Humanitarian intake; ethics-first minimisation | Intake spreadsheets, scans (where allowed), messaging exports |
| [EDTECH_LMS_EXPORTS_AND_MINORS.md](EDTECH_LMS_EXPORTS_AND_MINORS.md) | LMS rosters, guardians, minors; due diligence hygiene | LMS CSV/JSON, tickets, optional roster SQL |

## Adding future storyboards

1. Add a new **English** file under `docs/use-cases/` using the same structure as existing storyboards: **Cast** (generic roles), **Storyboard (flow)**, **How Data Boar helps without deciding**, **Partner opportunity**, **Product alignment (maintainers)**, **Related docs**.
1. Add the **pt-BR** mirror (`*.pt_BR.md`) with the same sections (use **Oportunidade para parceiros** and **Alinhamento de produto (maintainers)** for the partner/product headings).
1. Register the pair in the table above (and keep [docs/README.md](../README.md) pointing at this hub).
1. When a vertical drives **repeatable revenue signals**, maintainers record sequencing in the planning entry point linked from [docs/README.md](../README.md) (*Internal and reference*)—not via new `docs/plans/` links from this hub (CI guard).

## Cross-cutting references

- [DECISION_MAKER_VALUE_BRIEF.md](../DECISION_MAKER_VALUE_BRIEF.md) ([pt-BR](../DECISION_MAKER_VALUE_BRIEF.pt_BR.md))
- [SERVICE_TIERS_SCOPE_TEMPLATE.md](../ops/SERVICE_TIERS_SCOPE_TEMPLATE.md) ([pt-BR](../ops/SERVICE_TIERS_SCOPE_TEMPLATE.pt_BR.md))
- [COMPLIANCE_AND_LEGAL.md](../COMPLIANCE_AND_LEGAL.md) ([pt-BR](../COMPLIANCE_AND_LEGAL.pt_BR.md))
