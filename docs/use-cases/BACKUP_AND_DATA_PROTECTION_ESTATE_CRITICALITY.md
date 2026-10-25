# Use-case storyboard — backup / data-protection estate, criticality overlay

**Português (Brasil):** [BACKUP_AND_DATA_PROTECTION_ESTATE_CRITICALITY.pt_BR.md](BACKUP_AND_DATA_PROTECTION_ESTATE_CRITICALITY.pt_BR.md)

Documentation storyboard for organisations that already run an **enterprise backup, recovery, and data-protection platform** and need a **criticality / sensitivity overlay** on top of it. **Not** a backup/DR product, **not** a recoverability guarantee, and **not** a certification of any data-protection vendor.

## Cast (generic roles)

- **Organisation:** Enterprise or mid-market team that operates an **immutable-snapshot / cyber-resilience / backup platform** (DR copies, long-retention archives) across primary and secondary storage.
- **Data subjects:** Employees, customers, and partners whose records live inside the protected estate (databases, file shares, mail, app data) — and, by extension, **every copy** the protection platform fans out.
- **Systems:** Production shares/DBs that are **sources** of the backup estate, **restored/mounted read-only** copies, export catalogues, and the protection platform's own inventory/reports.

## Storyboard (flow)

1. **Protection without criticality** — the platform answers “is everything recoverable?”, but its own **maturity checklist** asks the harder question: “do you have visibility into **which** data is most critical or most sensitive?” That row stays blank.
2. **The blind copy** — protection fans data out into snapshots, DR sites, and long-retention tiers; sensitive and critical records are now **multiplied** across the estate with **no criticality label**.
3. **Boar sniffs (scoped, read-only)** — point Data Boar at **restored/mounted copies** or source shares/DBs on **read-only** access; PII density, sensitive categories, minors, and national-ID-like runs surface in the report heatmap.
4. **Criticality overlay** — findings become the **criticality/sensitivity layer** the protection platform lacks: which shares, tables, and paths concentrate regulated data, and where retention and immutability matter most.
5. **Human moment** — owners decide retention tiers, legal hold, and access scope; **counsel** interprets. The product does **not** decide criticality classes, perform backup/restore, or assert recoverability.

## How Data Boar helps without deciding

- **Answers the checklist gap** the protection platform itself raises (“which data is most critical?”) with **technical evidence**, not a recoverability claim.
- **Prioritises** where sensitive data concentrates so retention, immutability, and DR spend can **follow criticality** instead of treating every copy alike.
- **Does not** back up, restore, replicate, or certify recoverability; it **maps**, it does not protect.

## Partner opportunity

Partners who already sell or operate **enterprise backup / data-protection platforms** attach Data Boar as the **criticality and sensitivity discovery layer** that closes the “do you know what's most critical?” gap on the **vendor's own maturity assessment**. Sold as a **fixed-scope discovery workshop** against the existing install base, then handed to IT/DPO for retention and access decisions. The argument writes itself: the platform **asks** the question; Data Boar is the **answer**.

## Product alignment (maintainers)

Prioritise surfaces that ingest **restored/mounted copies and export catalogues** as scan roots (filesystem + compressed + SQL sampling on read-only mounts) and **criticality/sensitivity reporting** (heatmap, gravity tiers, jurisdiction hints). Keep positioning as an **evidence overlay**, not protection. **Do not** link execution sequencing from this buyer-facing page into `docs/plans/`; use the **Internal and reference** section of [docs/README.md](../README.md) as the maintainer entry point.

**Signal strengths for this vertical:** `file_scan`, compressed-archive handling, optional SQL connectors, heatmap / compliance outputs, [REPORTS_AND_COMPLIANCE_OUTPUTS.md](../REPORTS_AND_COMPLIANCE_OUTPUTS.md), [ADDING_CONNECTORS.md](../ADDING_CONNECTORS.md).

## Related docs

- [use-cases/README.md](README.md) ([pt-BR](README.pt_BR.md))
- [SERVICE_TIERS_SCOPE_TEMPLATE.md](../ops/SERVICE_TIERS_SCOPE_TEMPLATE.md) ([pt-BR](../ops/SERVICE_TIERS_SCOPE_TEMPLATE.pt_BR.md))
- [DECISION_MAKER_VALUE_BRIEF.md](../DECISION_MAKER_VALUE_BRIEF.md) ([pt-BR](../DECISION_MAKER_VALUE_BRIEF.pt_BR.md))
- [USAGE.md](../USAGE.md) ([pt-BR](../USAGE.pt_BR.md))
