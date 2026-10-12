# Primers — technical and onboarding

**Português (Brasil):** [INDEX.pt_BR.md](INDEX.pt_BR.md)

This folder holds **technical and onboarding primers**: thematic, vendor-neutral knowledge
transfer (KT) for integrators, maintainers, and new contributors. They are **not** product
configuration guides (those live in the product docs) and **not** compliance/framework primers
(those stay in the central hub — see below).

**Taxonomy (see [ADR-0070](../adr/ADR-0070-primer-taxonomy-and-home.md), amends [ADR-0058](../adr/ADR-0058-primer-hub-registration-ritual.md)):**

- **Technical / onboarding primers → this folder (`docs/primers/`).** KT, first read, mental model.
- **Compliance / framework primers → `docs/plans/` (deliverable tier),** indexed by the central
  primers hub `docs/plans/PRIMERS_HUB.md` (referenced as a path so external-tier docs keep a clean
  audience boundary — see [ADR-0004](../adr/ADR-0004-external-docs-no-markdown-links-to-plans.md)).

## Index

| Primer | What it anchors |
| ------ | --------------- |
| [AI_EVOLUTION_PRIMER.md](AI_EVOLUTION_PRIMER.md) ([pt-BR](AI_EVOLUTION_PRIMER.pt_BR.md)) | AI history (winters, expert systems, ML/DL, LLMs) — no hype, integrator context |
| [DECISION_RECORDS_PRIMER.md](DECISION_RECORDS_PRIMER.md) ([pt-BR](DECISION_RECORDS_PRIMER.pt_BR.md)) | ADR → MADR → UMADR: why decisions are recorded, and this repo's standard |
| [FORENSICS_AND_EVIDENCE_PRIMER.md](FORENSICS_AND_EVIDENCE_PRIMER.md) ([pt-BR](FORENSICS_AND_EVIDENCE_PRIMER.pt_BR.md)) | Digital forensics and evidence — inventory artefacts vs *laudo*; ISO/NIST pointers |
| [IAC_AND_DEVSECOPS_PRIMER.md](IAC_AND_DEVSECOPS_PRIMER.md) ([pt-BR](IAC_AND_DEVSECOPS_PRIMER.pt_BR.md)) | IaC concepts; `deploy/ansible` + `deploy/opentofu`; DevSecOps checks that exist in-repo |

| [AI_COMPLIANCE_PRIMER.md](AI_COMPLIANCE_PRIMER.md) | EU AI Act, ISO/IEC 42001, NIST AI RMF — data-layer compliance (inventory only; no model evaluation) |

| [DATA_GOVERNANCE_DMBOK_PRIMER.md](DATA_GOVERNANCE_DMBOK_PRIMER.md) ([pt-BR](DATA_GOVERNANCE_DMBOK_PRIMER.pt_BR.md)) | DAMA-DMBOK knowledge areas and ISO/IEC 38505 — discovery evidence, not a GDD platform |

| [FINANCIAL_SECTOR_COMPLIANCE_PRIMER.md](FINANCIAL_SECTOR_COMPLIANCE_PRIMER.md) | PCI DSS v4.0, SOX, BACEN CMN 4.893 — financial-sector compliance (evidence limits) |

| [GLOBAL_PRIVACY_REGULATIONS_PRIMER.md](GLOBAL_PRIVACY_REGULATIONS_PRIMER.md) | PIPEDA, POPIA, APPI, Vietnam PDPD, FELCA — global privacy regulations (honest sample status) |

| [HEALTH_SECTOR_COMPLIANCE_PRIMER.md](HEALTH_SECTOR_COMPLIANCE_PRIMER.md) | HIPAA/PHI, ANS, ANVISA, CFM — health-sector compliance alignment |

| [ITSM_FRAMEWORKS_PRIMER.md](ITSM_FRAMEWORKS_PRIMER.md) ([pt-BR](ITSM_FRAMEWORKS_PRIMER.pt_BR.md)) | ITIL 4 SVS and ISO/IEC 20000 — selected practices vs scan evidence (not a service desk) |

## Navigation

- **Map of maps:** [docs/hubs/INDEX.md](../hubs/INDEX.md)
- **Glossary:** [GLOSSARY.md](../GLOSSARY.md)
- **Compliance/framework primers:** central hub at `docs/plans/PRIMERS_HUB.md`

## Update ritual

1. Add the primer file under `docs/primers/` (EN + pt-BR mirror).
1. Add a row to this index **and** its `.pt_BR` mirror.
1. Register the local index in `docs/hubs/INDEX.md` (already done) — keep the row's path valid.
1. Run `./scripts/check-hubs.sh` (or `.\scripts\check-hubs.ps1`) and `./scripts/check-all.sh`.
