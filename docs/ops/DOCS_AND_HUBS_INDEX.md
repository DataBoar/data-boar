# Docs and hubs master index

**Português (Brasil):** [DOCS_AND_HUBS_INDEX.pt_BR.md](DOCS_AND_HUBS_INDEX.pt_BR.md)

<!-- plans-hub-summary: Master index of all navigation hubs in the project -->

> **For agents:** when you need "where is the hub for X?", start here or at [`docs/hubs/INDEX.md`](../hubs/INDEX.md). Hubs **link only** — they do not move canonical files ([ADR-0057](../adr/ADR-0057-lightweight-hub-index-co-located-links.md)).

## Planning and prioritization

| Hub | Purpose | When to consult |
| --- | ------- | ---------------- |
| [`docs/plans/PLANS_HUB.md`](../plans/PLANS_HUB.md) | Table of every `PLAN_*.md` | Finding or adding a plan file |
| [`docs/plans/PLANS_TODO.md`](../plans/PLANS_TODO.md) | Execution dashboard and sequencing | Picking the next slice |
| [`docs/ops/PLANS_DOCUMENTATION_HIERARCHY.md`](PLANS_DOCUMENTATION_HIERARCHY.md) | `PLAN_*` vs `PLANS_TODO` vs `PLANS_HUB` | PMO / three-layer model |
| [`docs/plans/PLAN_TAXONOMY_AXES.md`](../plans/PLAN_TAXONOMY_AXES.md) | H / U / G / P bands | Priority vocabulary |
| [`docs/plans/PRIMERS_HUB.md`](../plans/PRIMERS_HUB.md) | Framework education primers | Compliance framework context |

## Architecture decisions

| Hub | Purpose | When to consult |
| --- | ------- | ---------------- |
| [`docs/adr/README.md`](../adr/README.md) | ADR index 0000 through latest | Recording or reading a decision |
| [`docs/adr/INVENTORY.txt`](../adr/INVENTORY.txt) | Per-ADR SHA-256 manifest | Integrity / audit evidence |

## Agents, policies, and scripts

| Hub | Purpose | When to consult |
| --- | ------- | ---------------- |
| [`docs/hubs/RULES_AND_SKILLS_HUB.md`](../hubs/RULES_AND_SKILLS_HUB.md) | All Cursor `.mdc` rules + skills | Which rule/skill applies |
| [`docs/ops/CURSOR_AGENT_POLICY_HUB.md`](CURSOR_AGENT_POLICY_HUB.md) | Theme to policy map (clickable) | Fresh agent policy routing |
| [`docs/ops/OPERATOR_AGENT_COLD_START_LADDER.md`](OPERATOR_AGENT_COLD_START_LADDER.md) | Ordered cold-start path | Empty-context session |
| [`docs/ops/TOKEN_AWARE_SCRIPTS_HUB.md`](TOKEN_AWARE_SCRIPTS_HUB.md) | `scripts/*.ps1` / `.sh` | Before ad-hoc shell |
| [`AGENTS.md`](../../AGENTS.md) | Non-negotiable agent contract | Every session baseline |

## Cross-cutting navigation

| Hub | Purpose | When to consult |
| --- | ------- | ---------------- |
| [`docs/hubs/INDEX.md`](../hubs/INDEX.md) | Hub-of-hubs by work area | Two-hop navigation |
| [`docs/README.md`](../README.md) | Product doc tables EN/pt-BR | External / integrator docs |
| [`docs/MAP.md`](../MAP.md) | Topic-first concern map | "Where is X explained?" |

## Integrity and release

| Hub | Purpose | When to consult |
| --- | ------- | ---------------- |
| [`docs/ops/INTEGRITY_HUB.md`](INTEGRITY_HUB.md) | Tamper detection, release evidence | Security / release audit |
| [`docs/ops/RELEASE_INTEGRITY.md`](RELEASE_INTEGRITY.md) | Ops release integrity spec | SRE / GRC checklist |

## Maintenance

- New hub: add a row here and in [`docs/hubs/INDEX.md`](../hubs/INDEX.md) in the **same PR**.
- Rules/skills hub: `uv run python scripts/build_rules_skills_hub.py --write`.
- Plans hub: `uv run python scripts/plans_hub_sync.py --write`.
