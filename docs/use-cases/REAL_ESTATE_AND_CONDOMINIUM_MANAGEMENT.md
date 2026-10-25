# Use-case storyboard — real estate agency and condominium / property management (SMB)

**Português (Brasil):** [REAL_ESTATE_AND_CONDOMINIUM_MANAGEMENT.pt_BR.md](REAL_ESTATE_AND_CONDOMINIUM_MANAGEMENT.pt_BR.md)

Storyboard for **high-volume SMB** property data: tenants, owners, contracts, and utilities. **Not** land-registry legal advice.

## Cast (generic roles)

- **Organisation:** Rental agency, **condo** administrator, or property manager with **many small units** and recurring document flows.
- **Data subjects:** Tenants, owners, guarantors, emergency contacts, vendors.
- **Systems:** “Unit folder” trees, contract PDFs, spreadsheet **consumption** logs, WhatsApp-export dumps (where policy allows), simple CRM exports.

## Storyboard (flow)

1. **Lease cycle** — ID scans and proof-of-income attachments accumulate per unit; filenames are **opaque**.
2. **Turnover** — former tenant folders are **not** archived consistently; duplicates linger.
3. **Boar sniffs (scoped targets)** — national-ID-like runs, phone patterns, address-like strings in mixed CSVs.
4. **Owner committee** — report supports **retention** discussion (how long to keep ID copies) without legal conclusion.
5. **Human moment** — **Physical access** logs and keys are out of scope for the scanner; counsel for **landlord–tenant** law.

## How Data Boar helps without deciding

- **Surfaces** **dense** PII in forgotten subtrees (common in SMB shares).
- **Supports** **least-privilege** restructuring on file servers.
- **Does not** score tenants or replace property-management software.

## Partner opportunity

Regional consultancies and **managed IT for SMB** use the storyboard to sell **non-glamorous** but frequent compliance hygiene where enterprise GRC suites are too heavy.

## Product alignment (maintainers)

This vertical stress-tests **plain filesystem** scale, **PDF** attachments, and **messy CSV** encodings—not exotic connectors. Improvements to **throughput**, **memory caps**, and **operator clarity** in [USAGE.md](../USAGE.md) help here first. Maintainer sequencing: [docs/README.md](../README.md) **Internal and reference**.

**Signal strengths:** `file_scan`, `sample_limit`, heatmap outputs, [TOPOLOGY.md](../TOPOLOGY.md) for deployment shape.

## Related docs

- [use-cases/README.md](README.md) ([pt-BR](README.pt_BR.md))
- [COMPLIANCE_FRAMEWORKS.md](../COMPLIANCE_FRAMEWORKS.md) ([pt-BR](../COMPLIANCE_FRAMEWORKS.pt_BR.md))
- [USAGE.md](../USAGE.md) ([pt-BR](../USAGE.pt_BR.md))
- [TOPOLOGY.md](../TOPOLOGY.md) ([pt-BR](../TOPOLOGY.pt_BR.md))
