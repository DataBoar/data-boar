# Navigation hubs — Data Boar

**Português (Brasil):** [INDEX.pt_BR.md](INDEX.pt_BR.md)

> **For agents (Cursor and others):** read this page first when you need the **map of maps**. Master one-liner index: [`docs/ops/DOCS_AND_HUBS_INDEX.md`](../ops/DOCS_AND_HUBS_INDEX.md). Each row below points to a hub in its canonical folder — we **do not** move files here ([ADR-0057](../adr/ADR-0057-lightweight-hub-index-co-located-links.md)).

## How to use

1. Identify your work area (plans, scripts, compliance, pitch).
1. Open the hub below.
1. Follow links inside that hub to the real files.

## Index

### Planning and prioritization

| Hub | Canonical path | Covers |
| --- | -------------- | ------ |
| Plans hub | `docs/plans/PLANS_HUB.md` | Every `PLAN_*.md` + hub summary |
| Plans hierarchy | `docs/ops/PLANS_DOCUMENTATION_HIERARCHY.md` | `PLAN_*` vs `PLANS_TODO` vs `PLANS_HUB` |
| Taxonomy axes | `docs/plans/PLAN_TAXONOMY_AXES.md` | H / U / G / P bands |
| Primers hub | `docs/plans/PRIMERS_HUB.md` | Framework education primers (compliance tier) |
| Primers (technical) | `docs/primers/INDEX.md` | Onboarding/KT primers (AI evolution, decision records) |
| Plans to-do | `docs/plans/PLANS_TODO.md` | Execution dashboard |

### Architecture decisions

| Hub | Canonical path | Covers |
| --- | -------------- | ------ |
| ADR index | `docs/adr/README.md` | ADR-0001 through latest |

### Scripts and automation

| Hub | Canonical path | Covers |
| --- | -------------- | ------ |
| Scripts hub | `docs/ops/TOKEN_AWARE_SCRIPTS_HUB.md` | `scripts/*.ps1` / `.sh` |
| Cross-platform pairs | `docs/ops/SCRIPTS_CROSS_PLATFORM_PAIRING.md` | Windows/Linux script twins |

### Agents and policies

| Hub | Canonical path | Covers |
| --- | -------------- | ------ |
| Cursor policy hub | `docs/ops/CURSOR_AGENT_POLICY_HUB.md` | Rules + skills map |
| Rules and skills hub | `docs/hubs/RULES_AND_SKILLS_HUB.md` | All `.mdc` rules + skills (generated) |
| Cold-start ladder | `docs/ops/OPERATOR_AGENT_COLD_START_LADDER.md` | Fresh-session router |
| Agent contract | `AGENTS.md` | Non-negotiables + quick index |

### Product docs (external-facing)

| Hub | Canonical path | Covers |
| --- | -------------- | ------ |
| Docs README | `docs/README.md` | EN/pt-BR doc tables |
| Audience guide | `docs/AUDIENCE_GUIDE.md` | Who reads what |
| Concern map | `docs/MAP.md` | Topic-first navigation |
| Use cases | `docs/use-cases/USE_CASES_HUB.md` | Storyboards + product scenarios |
| Pitch decks | `docs/pitch/INDEX.md` | Stakeholder / DPO / CISO |

### Security, governance, and posture

| Hub | Canonical path | Covers |
| --- | -------------- | ------ |
| **Posture hub** | `docs/SECURITY_GOVERNANCE_POSTURE_HUB.md` | Security, governance, safety, quality, provenance — co-located index |
| Governance diagrams | `docs/ops/governance/DATABOAR_GOVERNANCE_DIAGRAMS.md` | ISO/COBIT/ITIL positioning diagrams for pitches |

### Integrity and release evidence

| Hub | Canonical path | Covers |
| --- | -------------- | ------ |
| **Integrity hub** | `docs/ops/INTEGRITY_HUB.md` | Tamper detection, runtime trust, release vs licensing docs, ADR inventory |
| Release integrity (ops spec) | `docs/ops/RELEASE_INTEGRITY.md` | Rust build evidence, SRE checklist, GRC weights |
| Release integrity (product) | `docs/RELEASE_INTEGRITY.md` | Licensing digest, optional signed manifest, SBOM |
| Integrity check (alpha) | `docs/ops/INTEGRITY_CHECK_ALPHA_LOGIC.md` | Runtime trust design spec |

### Inspirations and doctrine

| Hub | Canonical path | Covers |
| --- | -------------- | ------ |
| Inspirations hub | `docs/ops/inspirations/INSPIRATIONS_HUB.md` | Engineering manifestos |

## Update ritual

When you add or rename a hub:

1. Add or fix a row in this file (EN + pt-BR mirror).
1. Run `.\scripts\check-hubs.ps1` (or `./scripts/check-hubs.sh`) — wired in `check-all`.
1. Grep for stale paths before commit.

Broken links in backtick paths **fail** `check-all` via `scripts/check_hubs.py`.
