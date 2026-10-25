# Use-case storyboard — RPO, people ops, and payroll bureau (B2B)

**Português (Brasil):** [RPO_PEOPLE_OPS_AND_PAYROLL_BUREAU.pt_BR.md](RPO_PEOPLE_OPS_AND_PAYROLL_BUREAU.pt_BR.md)

Storyboard for **high-volume HR files** across **many employer clients**. **Not** labour-law advice and **not** payroll calculation certification.

## Cast (generic roles)

- **Organisation:** RPO, outsourced HR, or payroll bureau serving **SMB to mid-market** employers.
- **Data subjects:** Applicants, employees, ex-employees, dependents where present in benefits files.
- **Systems:** ATS exports, onboarding PDF packs, **CSV/SQL** payroll handoffs, shared “client HR” trees, assessment spreadsheets.

## Storyboard (flow)

1. **Recruitment burst** — résumés and interview notes land beside **final hire** spreadsheets; naming mixes client codes and legal entity names.
2. **Payroll handoff** — monthly files contain **national IDs**, bank tokens, and free-text “notes” fields.
3. **Cross-client bleed** — same consultant workspace spans **multiple** employers; weak folder discipline.
4. **Boar sniffs (scoped targets)** — filesystem + optional SQL; **minor-adjacent** fields may appear in forms (route to human review per [MINOR_DETECTION.md](../MINOR_DETECTION.md)).
5. **Human moment** — **Retention** for CVs; **counsel** for background-check regulation. Product does **not** decide hiring.

## How Data Boar helps without deciding

- **Produces** a **first map** of PII density before a formal ROPA or DPIA engagement.
- **Flags** wide scans that accidentally span **too many** client subtrees.
- **Does not** replace ATS, HRIS, or certified payroll engines.

## Partner opportunity

Partners productise a **fixed “HR data surface” scan** as the entry SKU, then upsell policy work and tooling change separately.

## Product alignment (maintainers)

Demand here often overlaps **accounting** storyboards (tax IDs) plus **strong minor hints**. Prioritise: stable **Brazilian CPF** heuristics where configured, **sample limits**, and **clear export RBAC**. Maintainer sequencing: [docs/README.md](../README.md) **Internal and reference**.

**Signal strengths:** payroll-shaped columns, compressed archives, [MINOR_DETECTION.md](../MINOR_DETECTION.md), [COMPLIANCE_METHODOLOGY.md](../COMPLIANCE_METHODOLOGY.md).

## Related docs

- [use-cases/README.md](README.md) ([pt-BR](README.pt_BR.md))
- [ACCOUNTING_FIRM_PAYROLL_TAX_AND_LEDGER.md](ACCOUNTING_FIRM_PAYROLL_TAX_AND_LEDGER.md) ([pt-BR](ACCOUNTING_FIRM_PAYROLL_TAX_AND_LEDGER.pt_BR.md))
- [REPORTS_AND_COMPLIANCE_OUTPUTS.md](../REPORTS_AND_COMPLIANCE_OUTPUTS.md) ([pt-BR](../REPORTS_AND_COMPLIANCE_OUTPUTS.pt_BR.md))
- [USAGE.md](../USAGE.md) ([pt-BR](../USAGE.pt_BR.md))
