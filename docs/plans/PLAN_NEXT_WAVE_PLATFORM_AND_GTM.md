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
- **Scope import (distinct from live connectors):** optional **export → canonical schema → YAML/JSON config fragments** for inventory bootstrap (monitoring, ITSM, assessment breadcrumbs) — see [PLAN_SCOPE_IMPORT_FROM_EXPORTS.md](completed/PLAN_SCOPE_IMPORT_FROM_EXPORTS.md); partner-friendly “accelerator” narrative alongside open-core baseline.
- Document interoperability path for polyglot modules when justified (Python-first orchestration with optional constrained sidecar services).
- Tie to least-privilege and auditability controls before expansion.

### N3 — Productized academic-to-market evidence stream

- Convert thesis/portfolio outputs into product trust artifacts (case-style notes, methods, repeatability packets).
- Keep private personal/professional details in `docs/private/` and produce public-safe derivatives.
- Align learning roadmap with shipping roadmap so certifications and academic work directly improve product value.

## Partner channel thesis — data-protection / backup vendors (criticality overlay)

Natural enterprise channel that complements **N2's** partner-friendly accelerator narrative. Backup / data-protection platforms (e.g. **Cohesity**, **Rubrik**, **Veeam**, **Commvault**, **Veritas**) already own the **install base** and already **fan data out** into snapshots, DR sites, and long-retention tiers — but their **own maturity checklists** ask the customer whether they have visibility into **which data is most critical / most sensitive**. That is exactly Data Boar's output.

- **Positioning (one line):** the platform **asks** “do you know which data is most critical?”; Data Boar is the **answer** — a criticality/sensitivity **evidence overlay**, not a backup, restore, or recoverability claim.
- **Why it qualifies leads cheaply:** the gap is **self-identified by the vendor's own assessment**, so the discovery workshop attaches to an existing budget conversation instead of creating a new one.
- **Scope discipline:** keep it an **evidence overlay** — no recoverability guarantees, no DR product claims, no vendor certification. Ingest **restored/mounted read-only copies** and **export catalogues** as scan roots; reuse the file/compressed/SQL pipeline (ties to N2 scope-import accelerators).
- **Buyer-facing narrative (generic, no vendor names):** [../use-cases/BACKUP_AND_DATA_PROTECTION_ESTATE_CRITICALITY.md](../use-cases/BACKUP_AND_DATA_PROTECTION_ESTATE_CRITICALITY.md) ([pt-BR](../use-cases/BACKUP_AND_DATA_PROTECTION_ESTATE_CRITICALITY.pt_BR.md)).
- **Promotion gate:** stays a thesis until **repeatable revenue evidence** appears; only then promote a row in `PLANS_TODO.md` (*Partner / sector demand*) — do **not** add buyer-facing links into `docs/plans/`.

### Complementary category — shift-left SAST (Privado-class) — [#1066](https://github.com/FabioLeitao/data-boar/issues/1066)

**Shift-left** tools trace PII **through source code** (CI of the dev pipeline); Data Boar traces **where data already lives** (production, backups, shares, shadow imports). They are **adjacent, not substitutes**.

- **GTM angle:** compliance artefacts built from **evidence**, not human memory, have proven demand (RoPA / app-store data-safety narratives). A team already using shift-left PII SAST in CI is a **natural lead** for production inventory with Data Boar.
- **No product action here:** do not add Code Property Graph, Joern, or Privado as dependencies; Semgrep in `check-all` remains **generic security SAST**, not data-flow PII inventory.

## Deliverables

- One tracked doc slice per front.
- Updated roadmap references in `PLANS_TODO.md`.
- At least one testable or auditable artifact per front.

## Guardrails

- No compliance-certification claims.
- No secret or private partner/customer data in tracked files.
- No expansion that breaks token-aware execution discipline.
