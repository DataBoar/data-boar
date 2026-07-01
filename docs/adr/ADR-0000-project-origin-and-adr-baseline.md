# ADR 0000 — Project origin and ADR baseline

- **Status:** Accepted
- **Date (UTC):** 2026-03-26
- **Authors:** Fabio Leitao
- **Deciders:** Fabio Leitao

## Status history

- **2026-03-26:** Accepted — genesis anchor for pre-ADR history and index ordering.
- **2026-07-01:** Amended — ecosystem **UMADR** house rule (canonical regency for Data Boar and satellite repos); no change to the original genesis decisions below. Full metadata constitution: [ADR 0045](ADR-0045-adr-metadata-and-format-standardization.md). Tracking: GitHub #994.

## Context

The repository **`data-boar`** hosts **Data Boar** — a compliance-oriented engine to **discover and map personal and sensitive data** across files, databases, APIs, and related “data soup” sources, with reporting and dashboard surfaces for operators and compliance roles. The product positioning and feature narrative live in the canonical **[README.md](../../README.md)**; technical operation is in **[docs/TECH_GUIDE.md](../TECH_GUIDE.md)** and **[docs/USAGE.md](../USAGE.md)**.

For years before **Architecture Decision Records** existed in this tree, design choices were embedded in **code**, **plans** under **`docs/plans/`**, **release notes** under **`docs/releases/`**, and **SECURITY** / **CONTRIBUTING** text — without a numbered “why” series. That history remains valid; this ADR does **not** replace those sources.

The **Data Boar ecosystem** includes additional repositories (orchestration, scaffolds, detectors, reserves). Those repos need a **single auditable mother governance** for how ADRs are numbered, named, and lifecycle-managed — without copying operator-only process detail into every satellite tree.

## Decision

### Genesis and index (original)

1. Reserve **ADR 0000** as a **short historical anchor**: what the app is for, where the canonical pitch and tech docs live, and that substantive decisions before **March 2026** were not recorded as ADRs.
1. Keep **ADR 0001+** for **explicit** decisions made after ADRs were adopted in-repo (tooling, security doc policy, SBOM roadmap, etc.).
1. Do **not** renumber existing ADRs when adding 0000; new readers see **0000** first in the index, then chronological **0001**, **0002**, …

### UMADR ecosystem house rule (canonical regency)

This repository is the **canonical UMADR regency** for the ecosystem. Satellite repositories **reference** this file (or its stable public URL); they **do not** paste the full governance manifesto into genesis ADRs (**OPSEC** — see below).

| Rule | Requirement |
| ---- | ----------- |
| **Numbering** | Four-digit zero-padded IDs: `ADR-0001`, not `ADR-001`. Renumber only when normalizing legacy three-digit filenames; do **not** force-renumber an established corpus except for format compliance. |
| **Filename** | `ADR-NNNN-kebab-synopsis.md` — synopsis in the slug; stable after merge. |
| **Locale** | ADR body text is **English-only** (`en_US`). Paired pt-BR mirrors apply to operator README/index prose, not to numbered ADR files (see [ADR 0045](ADR-0045-adr-metadata-and-format-standardization.md)). |
| **Sections** | Prefer **Context**, **Decision**, **Consequences**, **References**; use `## Status history` for lifecycle (UMADR). |
| **Status taxonomy** | **Proposed**, **Accepted**, **Duplicate of ADR-NNNN**, **Obsolete**, **Quarantined**, plus compound forms (**Superseded by ADR-NNNN**, **Deprecated**, **Reserved**) as defined in [ADR 0045](ADR-0045-adr-metadata-and-format-standardization.md). **U = Human-in-the-Loop:** agents set **Proposed** on materialization; **Accepted** requires explicit operator ratification per [ADR 0056](ADR-0056-cryptographic-adr-inventory-inv-adr-ssh-attestation.md). |
| **Rebrand** | Each repository rename/rebrand is recorded in **its own ADR** (pattern: [ADR 0014](ADR-0014-rename-repo-and-package-python3-lgpd-crawler-to-data-boar.md)). Use a **low number** (0001–0005) when the corpus is small; otherwise the **next free** number — without renumbering unrelated ADRs. |
| **Canonical + reference-stub** | **data-boar** holds the full house rule (this ADR + [ADR 0045](ADR-0045-adr-metadata-and-format-standardization.md)). Satellites add a **short reference-stub ADR** that links here — no duplicate constitution text. |
| **Genesis ADR-0000 (satellites)** | **Origin / birth / rebrand only** — charter pointers, not agent modus operandi, security gate recipes, or private operator ritual. |
| **Greenfield birth-triplet** | New repos SHOULD seed, in the first governance commit: **0000** genesis (Accepted), **0001** mission charter (Accepted), **0002** UMADR reference-stub → this ADR (Accepted or Referenced). Optional **0003** language/R&D posture (Proposed) only when relevant. |
| **Engineering rigor canon** | Shared HITL rigor (RCA, gates, tests, PowerShell invariants) is **[ADR 0079](ADR-0079-ecosystem-engineering-rigor-canon.md)** — satellites reference; do not duplicate. |

**Stable public URL for reference-stubs:**

`https://github.com/FabioLeitao/data-boar/blob/main/docs/adr/ADR-0000-project-origin-and-adr-baseline.md`

Normalization playbook (operator vault, not tracked): issue **#994**; per-repo audit table maintained outside the public tree.

## Consequences

- **Positive:** One place to point newcomers (“why is there no ADR for X from 2022?”) without rewriting old history.
- **Positive:** Ecosystem repos share numbering, status, and stub pattern without forking UMADR text.
- **Positive:** Public canonical regency is auditable on GitHub; satellites stay thin.
- **Negative:** Slight overlap with README — keep genesis sections **brief** and link out.
- **Negative:** Satellite normalization is manual per repo (one PR each); [ADR 0045](ADR-0045-adr-metadata-and-format-standardization.md) remains the in-repo constitution for metadata detail.

## References

- [README.md](../../README.md) · [README.pt_BR.md](../../README.pt_BR.md)
- [docs/TECH_GUIDE.md](../TECH_GUIDE.md) · [docs/NARRATIVE_AND_ARCHITECTURE_HISTORY.md](../NARRATIVE_AND_ARCHITECTURE_HISTORY.md)
- [docs/ACADEMIC_USE_AND_THESIS.md](../ACADEMIC_USE_AND_THESIS.md)
- [docs/adr/README.md](README.md) — index and numbering rules
- [ADR 0045 — ADR metadata and format standardization (UMADR)](ADR-0045-adr-metadata-and-format-standardization.md)
- [ADR 0014 — Rename repository and package (rebrand pattern)](ADR-0014-rename-repo-and-package-python3-lgpd-crawler-to-data-boar.md)
- [ADR 0056 — Cryptographic ADR inventory](ADR-0056-cryptographic-adr-inventory-inv-adr-ssh-attestation.md)
- [ADR 0079 — Ecosystem engineering rigor canon (satellites)](ADR-0079-ecosystem-engineering-rigor-canon.md)
- GitHub issue [#994](https://github.com/FabioLeitao/data-boar/issues/994) — ecosystem UMADR normalization
