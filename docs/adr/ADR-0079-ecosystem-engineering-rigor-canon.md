# ADR 0079 — Ecosystem engineering rigor canon (UMADR satellites)

- **Status:** Proposed
- **Date (UTC):** 2026-07-01
- **Authors:** Fabio Leitao
- **Deciders:** Fabio Leitao

## Status history

- **2026-07-01:** Proposed — hoist operator HITL rigor boilerplate from satellite repos into one canonical, referenceable ADR (#994).

## Context

Several Data Boar ecosystem repositories (**quirky-quati**, **carrion-crow**, and scaffolds seeded from the same template) carry **identical or near-identical** ADR sets (`0001`–`0012`) that encode the operator’s **Human-in-the-Loop (HITL) engineering rigor** — RCA-first discipline, no brittle mitigations, taxonomy preservation, audit-gate parity, regression-test anchors, and related posture.

That boilerplate is **not disposable copy-paste noise**; it is the **canon of rigor** the operator expects agents and contributors to follow. Duplicating it per repo creates drift. The canonical home for **global** rigor decisions is **data-boar**; satellites **reference** this ADR (and linked siblings) instead of maintaining parallel full text.

Audit source: operator vault `UMADR-NORMALIZATION-PLAYBOOK.md` (2026-07-01); satellite trees compared via `DataBoar/quirky-quati` and `DataBoar/carrion-crow`.

## Decision

### 1. Global × local criterion

Before hoisting or retaining an ADR in a satellite repo, apply:

> **Would this decision make sense verbatim in another ecosystem repo?**
>
> - **Yes** (rigor, process, HITL, governance, PowerShell invariants, test discipline) → **global** — authoritative text lives in **data-boar**; satellites use a **reference stub**.
> - **No** (names a product script, repo path, consumer-specific contract) → **local** — stays in the satellite only.

Examples: *contextual contract for `inv.ps1`* → **local**; *RCA before fix* → **global**.

### 2. Canon index (satellite stub → authoritative record)

| Topic (typical satellite stub) | Scope | Authoritative record in data-boar |
| ------------------------------ | ----- | --------------------------------- |
| Contextual / product contract (e.g. `inv.ps1` schema) | **Local** | Satellite ADR only |
| Root cause analysis first | Global | [ADR 0047](ADR-0047-rca-first-defect-investigation-and-fix-discipline.md) |
| No brittle mitigations | Global | [ADR 0049](ADR-0049-no-brittle-mitigations-robust-input-handling.md) |
| Full replacement for architectural changes | Global | **This ADR** §3.1 |
| Engineering rigor (determinism, boundaries) | Global | **This ADR** §3.2 |
| Operator-facing taxonomy preservation | Global | [ADR 0048](ADR-0048-operator-facing-taxonomy-and-naming-contract-preservation.md) |
| Code is source of truth | Global | **This ADR** §3.3 · [ADR 0062](ADR-0062-agent-containment-triple-audit-offband-pingpong.md) (repo over LLM consensus) |
| Operator intent / blameless collaboration | Global | [ADR 0046](ADR-0046-operator-intent-and-blameless-collaboration.md) |
| PowerShell engineering pitfalls | Global (PS repos) | **This ADR** §3.4 |
| Audit gate as single source of truth | Global | **This ADR** §3.5 · [ADR 0072](ADR-0072-commit-gate-vs-release-gate-distinct-criteria.md) (commit vs release) |
| Regression test discipline | Global | **This ADR** §3.6 |
| Plans segregation (external docs ↔ plans) | Global | [ADR 0004](ADR-0004-external-docs-no-markdown-links-to-plans.md) |

Satellites **replace** duplicated global stubs with one short **reference-stub ADR** pointing here (and to [ADR 0000](ADR-0000-project-origin-and-adr-baseline.md) for UMADR format).

### 3. Hoisted global principles (authoritative text)

#### 3.1 Full replacement required

When hardening or refactoring operational automation at an **architecture** level:

- Deliver a complete, production-ready replacement artifact reviewable as a single unit.
- Partial snippets are acceptable only for explicitly scoped, low-risk tactical fixes.

#### 3.2 Engineering rigor

Adopt production-grade standards for script and automation changes:

- Input validation and edge-case handling at system boundaries.
- Deterministic behavior: same inputs produce same outputs.
- Integrity controls with documented semantics (e.g. hashing caps).
- Explicit error capture — runs do not silently abort without a recorded failure mode.
- Observability: manifests or logs include run options, counts, and errors where applicable.

#### 3.3 Code is source of truth

- Executable code is authoritative.
- Comments and documentation must match code behavior, not the reverse.
- Behavior-changing PRs include documentation updates in the same PR when docs would otherwise lie.

#### 3.4 PowerShell engineering pitfalls

Repository-level invariants for strict-mode PowerShell:

1. **Collection returns:** emit collections via `Write-Output -NoEnumerate (...)` to avoid pipeline unrolling to `$null`.
2. **Nested function scope:** nested helpers do not inherit parent locals; use `$script:` or return values explicitly.
3. **ReparsePoint ≠ symlink only:** gate symlink detection on `LinkType`, not `ReparsePoint` alone (cloud placeholders).
4. **Empty pipeline sort:** wrap `@($Records | Sort-Object ...)` so `.Count` is safe under `Set-StrictMode -Version Latest`.

#### 3.5 Audit gate as single source of truth

Local pre-commit and remote CI must not diverge. One wrapper script is the **definition** of the quality gate; CI invokes that script (or its cross-platform twin), not a parallel rule set.

- **data-boar:** `./scripts/check-all.sh` / `check-all.ps1` ([CONTRIBUTING.md](../../CONTRIBUTING.md)).
- **PowerShell satellites:** `scripts/dev/audit.ps1` (or equivalent) wired from `.githooks/pre-commit` and `ci.yml`.
- New checks land in the **gate script**, not only in workflow YAML.
- `git commit --no-verify` is emergency-only and must be followed by remediation ([ADR 0049](ADR-0049-no-brittle-mitigations-robust-input-handling.md)).

#### 3.6 Regression test discipline

- Every behavioural fix should land with a test in the same PR (or immediate follow-up).
- Tests cite an anchor (`# regression-anchor:` comment, ADR id, or contract name).
- Negative / control cases where feasible (not happy-path-only).
- Tests must not mutate the tracked working tree; use temp fixtures.
- Framework choice is repo-specific (pytest here; Pester on PS scaffolds); the **discipline** is global.

## Consequences

- **Positive:** One auditable rigor canon; satellites stay thin; operator HITL posture is preserved without per-repo drift.
- **Positive:** Clear global×local rule for future ADRs and agent sessions.
- **Negative:** Satellite PRs must replace boilerplate with stubs (one-time normalization per repo).
- **Ongoing:** Material changes to hoisted principles amend this ADR (Status history) or spawn a numbered sibling ADR when scope splits.

## References

- [ADR 0000 — UMADR ecosystem regency](ADR-0000-project-origin-and-adr-baseline.md)
- [ADR 0046](ADR-0046-operator-intent-and-blameless-collaboration.md) · [0047](ADR-0047-rca-first-defect-investigation-and-fix-discipline.md) · [0048](ADR-0048-operator-facing-taxonomy-and-naming-contract-preservation.md) · [0049](ADR-0049-no-brittle-mitigations-robust-input-handling.md)
- [ADR 0004 — External docs must not link into plans](ADR-0004-external-docs-no-markdown-links-to-plans.md)
- [ADR 0072 — Commit gate vs release gate](ADR-0072-commit-gate-vs-release-gate-distinct-criteria.md)
- GitHub [#994](https://github.com/FabioLeitao/data-boar/issues/994)
