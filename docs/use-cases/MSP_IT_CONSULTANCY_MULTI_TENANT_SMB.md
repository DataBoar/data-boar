# Use-case storyboard — MSP / IT consultancy, multi-client SMB stacks

**Português (Brasil):** [MSP_IT_CONSULTANCY_MULTI_TENANT_SMB.pt_BR.md](MSP_IT_CONSULTANCY_MULTI_TENANT_SMB.pt_BR.md)

Documentation storyboard for **repeatable** discovery across **many small tenants** (file shares, backup trees, exports). **Not** a managed-security operations contract or vendor certification.

**Different angle:** provider-operated **managed / SaaS** tenancy (subdomain → dedicated instance) is documented in [USE_CASE_MANAGED_SAAS_MULTI_TENANT.md](USE_CASE_MANAGED_SAAS_MULTI_TENANT.md) ([pt-BR](USE_CASE_MANAGED_SAAS_MULTI_TENANT.pt_BR.md)) — that is **not** “MSP scans its SMB clients.”

## Cast (generic roles)

- **Organisation:** Regional MSP or IT consultancy with **standard playbooks** per client (AD/M365, Google Workspace, line-of-business SQL, NAS replication).
- **Data subjects:** Client employees and customers of those clients (names, identifiers, ticket bodies, exports).
- **Systems:** Per-client folder roots, RMM export CSVs, **M365/Google** dumps where policy allows, SQL backups, VPN config trees (often **credential-adjacent**).

## Storyboard (flow)

1. **Onboarding** — consultant copies a “data inventory” bundle into a scoped scan root; naming is inconsistent (`ClienteA`, `client_a_final`).
2. **Cross-tenant risk** — same laptop or sync tool touched **multiple** clients; zip archives nest older copies.
3. **Boar sniffs (scoped targets)** — filesystem + optional SQL sampling on **read-only** copies; dense PII columns and national-ID-like runs surface in the report heatmap.
4. **Partner workshop** — findings prioritise **where** to tighten retention and share permissions; **recommendation overrides** localise DPO language where configured.
5. **Human moment** — **least privilege** on RMM and backup accounts; **counsel** for contractual DPA scope. The product does **not** assert “secure MSP” or replace SIEM.

## How Data Boar helps without deciding

- **Reuses** the same scan recipe across clients (utility-belt **repeatability** for the consultancy).
- **Highlights** accidental **wide roots** (cross-client bleed) before deeper pen-test or formal audit spend.
- **Does not** replace endpoint protection, patch management, or contractual SLAs.

## Partner opportunity

Partners sell a **fast first map** (“where is our data soup dense?”) as a **fixed-scope workshop** or retainer add-on, then hand off remediation to the client’s IT or to higher-touch compliance firms.

## Product alignment (maintainers)

When MSP demand spikes, prioritise capabilities that **multiply across tenants**: documented **scope import** paths, **compressed** archive handling, **SQL sampling** caps, and **clear RBAC** on dashboard exports. **Do not** link execution sequencing from buyer-facing pages into `docs/plans/`; use the **Internal and reference** section of [docs/README.md](../README.md) as the maintainer entry point.

**Signal strengths for this vertical:** `file_scan`, optional SQL connectors, heatmap / compliance outputs, [REPORTS_AND_COMPLIANCE_OUTPUTS.md](../REPORTS_AND_COMPLIANCE_OUTPUTS.md), [ADDING_CONNECTORS.md](../ADDING_CONNECTORS.md).

## Related docs

- [use-cases/README.md](README.md) ([pt-BR](README.pt_BR.md))
- [USE_CASE_MANAGED_SAAS_MULTI_TENANT.md](USE_CASE_MANAGED_SAAS_MULTI_TENANT.md) ([pt-BR](USE_CASE_MANAGED_SAAS_MULTI_TENANT.pt_BR.md))
- [SERVICE_TIERS_SCOPE_TEMPLATE.md](../ops/SERVICE_TIERS_SCOPE_TEMPLATE.md) ([pt-BR](../ops/SERVICE_TIERS_SCOPE_TEMPLATE.pt_BR.md))
- [DECISION_MAKER_VALUE_BRIEF.md](../DECISION_MAKER_VALUE_BRIEF.md) ([pt-BR](../DECISION_MAKER_VALUE_BRIEF.pt_BR.md))
- [USAGE.md](../USAGE.md) ([pt-BR](../USAGE.pt_BR.md))
