# Use-case storyboard — accounting firm, payroll, tax IDs, and ledger (mid-market)

**Português (Brasil):** [ACCOUNTING_FIRM_PAYROLL_TAX_AND_LEDGER.pt_BR.md](ACCOUNTING_FIRM_PAYROLL_TAX_AND_LEDGER.pt_BR.md)

This is a **documentation storyboard** for workshops and POC narratives for **SMB to mid-market** accounting and audit-adjacent practices. It is **not** tax or labour-law advice.

## Cast (generic roles)

- **Organisation:** A firm serving **dozens to hundreds** of employer clients; payroll and tax filings are recurring.
- **Data subjects:** Employees of client companies (names, bank details where present in exports), client owners and signatories.
- **Systems:** Payroll CSV/SQL dumps, **nota fiscal** / invoice exports (where jurisdiction applies), GL spreadsheets, **eSocial**-class event files (Brazil-shaped examples), shared “client folder” trees.

## Storyboard (flow)

1. **Payroll cycle** — monthly files land in predictable paths; **CPF/CNPJ-shaped** columns may coexist with free-text “observation” fields.
2. **Tax season peaks** — more ad-hoc uploads, **compressed** archives, duplicate copies under “final” and “final2” names.
3. **Cross-client bleed risk** — the same bookkeeper’s laptop or share may contain **multiple** client trees; path names are a weak separator.
4. **Boar sniffs (scoped targets)** — filesystem + optional SQL connectors surface **national-ID-like** runs, bank-ish tokens, and **ambiguous** numeric columns.
5. **Report to DPO or partner** — findings prioritise **where** dense personal + financial metadata lives; **recommendation overrides** from [compliance-samples](../compliance-samples/) can localise wording (LGPD, GDPR-shaped samples).
6. **Human moment** — **Retention** and **least privilege** on shares; **counsel** where labour or tax secrecy applies. The product does **not** compute tax liability or payroll correctness.

## How Data Boar helps without deciding

- **Accelerates** “first map” of **PII + financial-adjacent** columns before a deeper audit engagement.
- **Highlights** **cross-directory** exposure if the same scan spans too wide a root.
- **Does not** replace statutory accounting systems, government portals, or certified payroll tools.

## Partner opportunity

Regional accounting networks and **LGPD/GDPR** boutiques productise a **payroll-and-ledger surface scan** as the first week of a larger engagement.

## Product alignment (maintainers)

Strong signal for **national-ID-shaped** columns, **compressed** peaks, and **cross-directory** warnings. Maintainer sequencing: [docs/README.md](../README.md) *Internal and reference*.

## Related docs

- [use-cases/README.md](README.md) ([pt-BR](README.pt_BR.md))
- [COMPLIANCE_FRAMEWORKS.md](../COMPLIANCE_FRAMEWORKS.md) ([pt-BR](../COMPLIANCE_FRAMEWORKS.pt_BR.md))
- [REPORTS_AND_COMPLIANCE_OUTPUTS.md](../REPORTS_AND_COMPLIANCE_OUTPUTS.md) ([pt-BR](../REPORTS_AND_COMPLIANCE_OUTPUTS.pt_BR.md))
- [USAGE.md](../USAGE.md) ([pt-BR](../USAGE.pt_BR.md)) — `file_scan`, compressed archives, `sample_limit`
