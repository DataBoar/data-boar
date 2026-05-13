# Plan: Next wave after core trust foundations (platform + GTM)

**Status:** Pending
**Date:** 2026-04-02
**Authors:** Fabio Leitao
**Priority:** H1

## Purpose

Define the next three execution fronts after:
1) evidence packet template, 2) zero-trust connector matrix, 3) service tier template.

## Next 3 fronts (prioritized)

### N1 — Multi-format reporting and outcome measurement

- Add decision-ready outputs beyond spreadsheets (for example JSON evidence bundle, PDF executive summary, and API export profile).
- Define measurable post-remediation trend signals (risk-down indicators by source/domain over time).
- Keep report language safe: technical evidence, not legal attestation.

### N2 — Modular connector/runtime architecture roadmap

- Define connector capability tiers and dependency packs (`core` / `plus` / `full`) with explicit operational and licensing boundaries.
- **Scope import (distinct from live connectors):** optional **export → canonical schema → YAML/JSON config fragments** for inventory bootstrap (monitoring, ITSM, assessment breadcrumbs) — see [PLAN_SCOPE_IMPORT_FROM_EXPORTS.md](PLAN_SCOPE_IMPORT_FROM_EXPORTS.md); partner-friendly “accelerator” narrative alongside open-core baseline.
- Document interoperability path for polyglot modules when justified (Python-first orchestration with optional constrained sidecar services).
- Tie to least-privilege and auditability controls before expansion.

### N3 — Productized academic-to-market evidence stream

- Convert thesis/portfolio outputs into product trust artifacts (case-style notes, methods, repeatability packets).
- Keep private personal/professional details in `docs/private/` and produce public-safe derivatives.
- Align learning roadmap with shipping roadmap so certifications and academic work directly improve product value.

## Deliverables

- One tracked doc slice per front.
- Updated roadmap references in `PLANS_TODO.md`.
- At least one testable or auditable artifact per front.

## Guardrails

- No compliance-certification claims.
- No secret or private partner/customer data in tracked files.
- No expansion that breaks token-aware execution discipline.
