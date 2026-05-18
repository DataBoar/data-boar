# Plan: Operating-domain contacts and alias policy

**Status:** Pending
**Date:** 2026-05-14
**Authors:** Fabio Leitao
**Priority:** H1 U1
**Depends on:** —

<!-- plans-hub-summary: Doc-only policy: where public contact emails, security disclosures, and domain aliases are defined; keeps SECURITY / CoC / CONTRIBUTING aligned without duplicating third-party or personal narratives in plan Motivation. -->
<!-- plans-hub-related: PLAN_MAINTAINER_ISSUE_BATCH_AND_PMO_SYNC.md -->

## Purpose

**[#483](https://github.com/FabioLeitao/data-boar/issues/483)** (P1) tracks **decisions** about **public** contact surfaces: which **mailbox** or **alias** appears on **`SECURITY.md`**, **`CODE_OF_CONDUCT.md`**, **`CONTRIBUTING.md`**, and related **operator-facing** stubs—especially when an operator-owned **domain** or **DNS** alias is introduced.

This plan **does not** record real addresses or registrar data in the **tracked** motivation text; the maintainer keeps canonical values in the actual policy files after the decision.

## Scope

1. **Single source of truth** — One **primary** security contact path and one **community** / **conduct** path (or justified merge) documented in **`SECURITY.md`** and **`CODE_OF_CONDUCT.md`** (EN + pt-BR mirrors per **`docs-policy.mdc`**).
2. **Alias and DNS** — If a **marketing** or **short** hostname forwards to GitHub / WordPress / another **existing** surface, document **behavior for reporters** (what inbox actually reads mail) without turning plans into DNS runbooks.
3. **CONTRIBUTING** — Contributor expectations for **where** to report vulnerabilities vs. generic bugs stay clear and link **`SECURITY.md`**.

## Non-goals

- Purchasing or operating **third-party** ticket systems.
- Embedding **PII**, employer names, or legal matter details in **`PLAN_*.md`** Motivation sections.

## Acceptance criteria

- [ ] **SECURITY.md** + **SECURITY.pt_BR.md** show **consistent** contact semantics (no contradictory addresses).
- [ ] **CODE_OF_CONDUCT** pair matches escalation paths.
- [ ] **CONTRIBUTING** pair points to **`SECURITY.md`** for vulnerability reporting.
- [ ] **#483** closed with a short comment referencing this plan and the files touched.

## Sequencing

Execute as a **docs-only** PR (or paired with **`houseclean`**), **`lint-only`** / **`check-all`** per change size; run **`uv run pytest tests/test_docs_pt_br_locale.py -v`** if pt-BR prose changes materially.

**Synced with:** [PLANS_TODO.md](PLANS_TODO.md)
