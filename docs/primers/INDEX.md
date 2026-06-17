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

## Navigation

- **Map of maps:** [docs/hubs/INDEX.md](../hubs/INDEX.md)
- **Glossary:** [GLOSSARY.md](../GLOSSARY.md)
- **Compliance/framework primers:** central hub at `docs/plans/PRIMERS_HUB.md`

## Update ritual

1. Add the primer file under `docs/primers/` (EN + pt-BR mirror).
1. Add a row to this index **and** its `.pt_BR` mirror.
1. Register the local index in `docs/hubs/INDEX.md` (already done) — keep the row's path valid.
1. Run `./scripts/check-hubs.sh` (or `.\scripts\check-hubs.ps1`) and `./scripts/check-all.sh`.
