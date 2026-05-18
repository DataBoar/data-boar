# Plan: Maintainer issue batch and PMO sync (GitHub ↔ docs/plans)

**Status:** Pending
**Date:** 2026-05-14
**Authors:** Fabio Leitao
**Priority:** H0 U0
**Depends on:** `CONTRIBUTING.md` + `docs/ops/COMMIT_AND_PR.md` workflow; `gh` CLI for triage

<!-- plans-hub-summary: Maintainer workflow: batch open GitHub issues into thin PRs, promote durable work into PLAN_*.md + PLANS_TODO + PLANS_HUB sync so the repo index matches reality. -->
<!-- plans-hub-related: PLAN_CLI_VALIDATE_DIFF_AND_DSAR_EXPORT.md, PLAN_OPERATING_DOMAIN_CONTACTS_AND_ALIAS_POLICY.md -->

## Purpose

**[#512](https://github.com/FabioLeitao/data-boar/issues/512)** coordinates **P0/P1** hygiene: closing or superseding issues without losing **traceability** in the **same** repository that ships the product.

**Problem:** `PLANS_TODO.md` mirrors execution order, and **`PLANS_HUB.md`** indexes every **`PLAN_*.md`**. Work that exists **only** in issues or chat is **not** indexed—collaborators and future sessions cannot treat it as a **committed** plan.

**Outcome:** Every non-trivial open thread either (a) maps to an existing **`PLAN_*.md`** section, or (b) gains a **new** `PLAN_*.md` plus **PLANS_TODO** dependency / phase rows, then **`python scripts/plans_hub_sync.py --write`** and **`python scripts/plans-stats.py --write`** when dashboard tables change.

## Operating principles

1. **Thin PRs** — one subject per PR where practical; Conventional Commits; **`.\scripts\check-all.ps1`** before merge.
2. **Issue → plan promotion** — When an issue describes **multi-step** product or ops work, add **`PLAN_*.md`** (English body, **`docs-plans.mdc`** header + optional `plans-hub-summary` / `plans-hub-related`).
3. **Duplicate closure** — Follow [GITHUB_ISSUE_CANONICAL_AND_DUPLICATE_CLOSE.md](../ops/GITHUB_ISSUE_CANONICAL_AND_DUPLICATE_CLOSE.md); link the canonical issue and **plan** from **`PLANS_TODO`** triage snapshot.
4. **No PII in plans** — Motivation and context stay generic; third-party names and commercial specifics live in **`docs/private/`** per **`AGENTS.md`**.

## Checklist (repeat per batch)

- [ ] `gh issue list --state open --limit 200` — refresh **`PLANS_TODO`** triage table / snapshot.
- [ ] For each **P0** cluster: implement or document deferral; **close** with PR / commit SHA evidence.
- [ ] **`python scripts/plans_hub_sync.py --write`** after any **`PLAN_*.md`** add/rename/`git mv` to **`completed/`**.
- [ ] **`python scripts/plans-stats.py --write`** when **status dashboard** source rows in **`PLANS_TODO`** change.

## Done when

- **#512** closed with a comment listing **delivered PRs** and **plan files** that subsume remaining open concerns, or an explicit **defer** with date and **`PLANS_TODO`** row.

**Synced with:** [PLANS_TODO.md](PLANS_TODO.md)
