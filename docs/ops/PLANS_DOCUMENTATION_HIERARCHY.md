# Plans documentation hierarchy (`docs/plans/`)

**Português (Brasil):** [PLANS_DOCUMENTATION_HIERARCHY.pt_BR.md](PLANS_DOCUMENTATION_HIERARCHY.pt_BR.md)

## Why this page exists

Contributors and operators sometimes conflate **GitHub issues**, **chat to-dos**, and **committed plan documents**. This runbook defines the **three-layer model** the repo actually indexes: without a `PLAN_*.md` on disk, work is **not** in the plans hub and **does not** ship the project’s PMO contract for collaborators.

## The three layers (bottom → top)

| Layer | Path / artifact | Role |
| ----- | ---------------- | ---- |
| **1 — Plan documents** | `docs/plans/PLAN_*.md` (active) and `docs/plans/completed/PLAN_*.md` (archived) | **Durable intent:** purpose, scope, slices, acceptance criteria, links to ADRs and related plans. **English-only** body for history (see `PLANS_TODO.md` intro). |
| **2 — Plans hub (index)** | `docs/plans/PLANS_HUB.md` (+ short intro `PLANS_HUB.pt_BR.md`) | **Automated table of every `PLAN_*.md`** (open + completed): title, one-line summary (`plans-hub-summary` HTML comment), optional **`plans-hub-related`** cross-links. **Not** a substitute for reading `PLANS_TODO` or the plan file. Refresh: `python scripts/plans_hub_sync.py --write` after add/rename/archive; CI checks `--check`. |
| **3 — Consolidated execution mirror** | `docs/plans/PLANS_TODO.md` | **Single operational backlog view:** dependency analysis table, integration snapshot, phased **to-do tables** per plan, GitHub triage pointers, auto-generated **status dashboard** (`plans-stats.py`). **This file tracks execution order and “what’s next”;** individual `PLAN_*.md` files hold the narrative spec. |

**Mental model:**

- **`PLAN_*.md`** = *what we agreed to build* (spec + slices).
- **`PLANS_HUB.md`** = *catalog of all plan files* (navigation).
- **`PLANS_TODO.md`** = *how it interleaves with everything else and what’s done vs pending* (ops mirror).

## GitHub issues and chat

- **Issues** are **coordination and triage** (links,_priorities, discussion). They **do not** replace layer 1.
- When an issue describes **multi-step** or **cross-cutting** work, **promote** it: add or extend a **`PLAN_*.md`**, add rows to **`PLANS_TODO.md`**, run **`plans_hub_sync.py --write`**, and **`plans-stats.py --write`** if dashboard tables change.
- **Cross-tooling** (e.g. another model or human on the same issue): use the issue thread for **handoff and decisions**, but **land** the outcome in **`docs/plans/`** so the hub stays truthful.

## Maintainers: edit order (minimal ritual)

1. Edit **`PLAN_*.md`** (status, slices, acceptance criteria).
2. Update **`PLANS_TODO.md`** (same pass when possible: dependency row, phase table, triage snapshot).
3. Run **`python scripts/plans_hub_sync.py --write`** when any `PLAN_*.md` path or **`plans-hub-summary`** / **`plans-hub-related`** changed.
4. Run **`python scripts/plans-stats.py --write`** when **`PLANS_TODO`** status rows that feed the dashboard change (see `<!-- PLANS_STATUS_DASHBOARD:START -->` block).
5. On **completion**: **`.cursor/rules/docs-plans.mdc`** — `git mv` to `docs/plans/completed/`, fix links, hub sync again, update pitch per **`pitch-roadmap-sync.mdc`** when the goal was stakeholder-visible.

## Related

- **`.cursor/rules/docs-plans.mdc`** — location, hub comments, completion workflow.
- **`docs/plans/PLANS_TODO.md`** — live backlog.
- **`docs/README.md`** — *Internal and reference* (entry point for plan links from the doc hub).
- **Audience:** **`docs/ops/`** may link into `docs/plans/`; external-tier product docs must not (see **`audience-segmentation-docs.mdc`** / `tests/test_docs_external_no_plan_links.py`).
