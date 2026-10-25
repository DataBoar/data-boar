# Use-case storyboard — insurance broker and benefits administrator (mid-market)

**Português (Brasil):** [INSURANCE_BROKER_AND_BENEFITS_ADMIN.pt_BR.md](INSURANCE_BROKER_AND_BENEFITS_ADMIN.pt_BR.md)

Storyboard for **claims**, **policy**, and **beneficiary** data held in mixed formats. **Not** actuarial advice, **not** a regulator-facing filing, and **not** a substitute for sector-specific legal review (health supplement, reinsurance, etc., vary by jurisdiction).

## Cast (generic roles)

- **Organisation:** Broker or **TPA-style** administrator handling **groups** of insured lives; heavy use of spreadsheets and PDF attachments.
- **Data subjects:** Policyholders, dependents, providers (clinics, pharmacies), corporate HR contacts.
- **Systems:** CRM policy objects, **claims** folders, commission spreadsheets, REST exports from legacy core systems (where read-only extracts exist).

## Storyboard (flow)

1. **Open enrollment** — bulk CSVs and email attachments land in shared drives; **duplicate** “corrected” files accumulate.
2. **Claims spike** — free-text fields mix **diagnosis-adjacent** tokens with addresses and national IDs.
3. **Boar sniffs (scoped targets)** — columnar and document paths; optional jurisdiction hints stay **metadata-only** (no medical decision).
4. **DPO alignment** — report shows **density** and **collision** of sensitive categories; counsel decides retention and lawful basis narratives.
5. **Human moment** — **Segregation of duties** between sales and claims staff; product does **not** score claims or premiums.

## How Data Boar helps without deciding

- **Accelerates** inventory before a **DPIA-style** workshop or external audit prep.
- **Surfaces** risky **flattened** exports (wide sheets with dozens of sensitive columns).
- **Does not** replace policy admin systems, underwriting engines, or regulator portals.

## Partner opportunity

Partners attach a **one-week evidence pack** (scoped scan + heatmap) to **RFP responses** or renewal conversations, then scope remediation (vaulting, field-level access) separately.

## Product alignment (maintainers)

If buyers ask repeatedly for **health-adjacent** wording and **beneficiary** patterns, extend **compliance samples** and **sensitivity** hints in a **documented, opt-in** way—avoid implying clinical or insurance regulatory completeness. Prefer [COMPLIANCE_FRAMEWORKS.md](../COMPLIANCE_FRAMEWORKS.md), [SENSITIVITY_DETECTION.md](../SENSITIVITY_DETECTION.md), and [JURISDICTION_COLLISION_HANDLING.md](../JURISDICTION_COLLISION_HANDLING.md). Sequencing for maintainers: [docs/README.md](../README.md) **Internal and reference**.

**Signal strengths:** jurisdiction hints (opt-in), recommendation overrides, GRC-style JSON for executive dashboards ([GRC_EXECUTIVE_REPORT_SCHEMA.md](../GRC_EXECUTIVE_REPORT_SCHEMA.md)).

## Related docs

- [use-cases/README.md](README.md) ([pt-BR](README.pt_BR.md))
- [COMPLIANCE_AND_LEGAL.md](../COMPLIANCE_AND_LEGAL.md) ([pt-BR](../COMPLIANCE_AND_LEGAL.pt_BR.md))
- [REPORTS_AND_COMPLIANCE_OUTPUTS.md](../REPORTS_AND_COMPLIANCE_OUTPUTS.md) ([pt-BR](../REPORTS_AND_COMPLIANCE_OUTPUTS.pt_BR.md))
- [USAGE.md](../USAGE.md) ([pt-BR](../USAGE.pt_BR.md))
