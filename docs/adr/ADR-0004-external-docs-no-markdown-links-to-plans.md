# ADR 0004 — Information architecture — external-tier docs must not link into `plans/`

- **Status:** Accepted
- **Date (UTC):** 2026-03-27
- **Authors:** Fabio Leitao
- **Deciders:** Fabio Leitao

## Context

Planning material under **`docs/plans/`** (and optional **`.cursor/plans/`**) is valuable for **transparency** and **contributor alignment**, but it mixes **execution detail**, **sequencing guesses**, and **internal PMO** language. Buyer-facing, legal/compliance overview, and primary **integrator** guides (deploy, API, product behaviour) serve **different audiences** than maintainers reviewing `PLAN_*.md` files.

Letting those surfaces carry **Markdown hyperlinks** straight into `plans/` creates:

- **Cognitive mismatch** — stakeholders follow a link expecting product truth and land in backlog prose.
- **Perceived commitment risk** — a roadmap line in a plan reads as a promise when linked from a compliance or pitch path.
- **Navigation entropy** — external docs become a second entry into PMO without the framing in [docs/README.md](../README.md) (*Internal and reference*) or the summarized map in [PLANS_HUB.md](../plans/PLANS_HUB.md).

This is an **information architecture** choice, not a claim that plans are secret: they stay **public in-tree**.

## Decision

1. **External-tier** Markdown (product guides at repo root and under **`docs/`**, excluding deliberate internal hubs — see enforcement below) **must not** use Markdown links whose targets resolve into **`plans/`** or **`.cursor/plans/`**. Prefer links to **USAGE**, **TECH_GUIDE**, **COMPLIANCE_***, **SECURITY**, **releases/**, **GLOSSARY**, and similar **product** docs; where a path is useful without a click target, use **inline code** (for example `` `docs/plans/` ``) instead of `[text](plans/...)`.
1. **Allowed link surfaces** into planning include: **`docs/plans/`** itself, **`docs/ops/`** runbooks, **`docs/README.md`** / **`docs/README.pt_BR.md`** (*Internal and reference*), **`docs/adr/`**, **CONTRIBUTING**, **AGENTS.md**, **[docs/COLLABORATION_TEAM.md](../COLLABORATION_TEAM.md)** (and **`.pt_BR.md`**) for maintainer/contributor workflow, and **gitignored** `docs/private/` (never from tracked pages into private paths). [PLANS_HUB.md](../plans/PLANS_HUB.md) is the **human-oriented table of plans** for collaborators who start from internal indexes. Prefer the **hub** or **README internal section** over deep links to individual `PLAN_*.md` from those workflow files unless a PR explicitly needs a direct plan anchor.
1. **Enforcement** is automated: **`tests/test_docs_external_no_plan_links.py`** (pre-commit / CI) scans an **external / product-guide tier** only; it **skips** the workflow files above (same set as the rule’s “where plan links are OK” intent). The standing narrative rule is **`.cursor/rules/audience-segmentation-docs.mdc`**. Changes to the scan allowlist belong in that test and rule together with a short update to this ADR if the **intent** shifts.

## Consequences

- **Positive:** Clear separation between **product truth** and **planning narrative**; collaborators still reach plans via README, CONTRIBUTING, ops runbooks, and the plans hub.
- **Negative:** Authors cannot shortcut from, for example, a compliance overview to a specific `PLAN_*.md` with one click; they link to the hub or describe paths in prose/code ticks.
- **Neutral:** ADRs and plan files may still cross-link freely; they are out of the external-tier scan.

## References

- [audience-segmentation-docs.mdc](../../.cursor/rules/audience-segmentation-docs.mdc)
- [test_docs_external_no_plan_links.py](../../tests/test_docs_external_no_plan_links.py)
- [docs/README.md](../README.md) — *Internal and reference*
- [PLANS_HUB.md](../plans/PLANS_HUB.md) · [AGENTS.md](../../AGENTS.md) — plans hub + operator/agent contract
