# Plan: Two-week execution sprint (no regressions, low toil, fast delivery)

**Status:** Active
**Date:** 2026-07-11
**Authors:** Fabio Leitao
**Priority:** H0

**Synced with:** [PLANS_TODO.md](PLANS_TODO.md)

**Previous template cycles:** Earlier windows in this file are **superseded** by the current sequencing in [PLANS_TODO.md](PLANS_TODO.md) (*Integration / active threads* + *What to start next*). Close each cycle with: green `main`, explicit carryover rows, and one short outcome note.

### This cycle — focus (2026-07-11 → 2026-07-24)

| Week | Theme | Outcomes |
| ---- | ----- | -------- |
| **1** | **Post3 stabilization + branch hygiene** | Keep docs-only and behavior slices separated (e.g. docs split PR without RBAC coupling), close/supersede stale overlap PRs, and leave one clean canonical track per theme. |
| **2** | **One selected delivery slice, no regression** | Ship one primary row from [PLANS_TODO.md](PLANS_TODO.md) (*S2a trust-state* **or** one **M-PILOT-READY** blocker), with tests and docs in the same slice and no broadened scope. |

**Definition of done (this cycle):** At least one merged PR for the selected slice; **`check-all --enforced`** green before publish/merge; docs/plan rows updated when scope moves; no silent carryover.

---

## Purpose

Deliver a short, realistic 2-week sprint that keeps **tests green**, avoids regressions, reduces repeatable toil, and moves demo -> beta readiness with small, auditable slices.

## Operating constraints

- Critical-first: security/regression/CI blockers before feature polish.
- Token-aware: one coherent slice at a time, minimal context drift.
- Safety-aware + security-aware: no shortcuts around checks.
- Locale-aware: EN canonical docs + pt-BR sync where applicable.
- Commerciality-aware: no private/commercial sensitive data in tracked docs.
- Brand/narrative-aware: keep Data Boar story consistent with shipped capabilities.

## Two-week scope (essential only)

### Week 1 — Stabilization and anti-overlap baseline

1. PR hygiene baseline:
   - Ensure active PRs are either merged, updated, or closed as superseded.
   - Keep one canonical PR per concern (docs-only vs RBAC/API behavior vs governance).
1. Automation hardening:
   - Keep `check-all --enforced` as pre-push/pre-merge proof.
   - Keep script-first execution (`check-all`, `lint-only`, `quick-test`, `commit-or-pr`) over ad-hoc command sequences.
1. Tests where it matters:
   - For each behavior change, keep one targeted regression test in the same PR.
   - Avoid broad rewrites; prioritize deterministic tests around changed paths.
1. Branch divergence control:
   - Prefer merge-main-in for protected branches where force-push is blocked.
   - Park operator-gated PRs when they require non-autonomous approvals.

### Week 2 — Delivery and checkpoint closure

1. One production-relevant feature slice:
   - Choose one small slice from `PLANS_TODO` with direct demo/ops impact and bounded risk.
   - Include docs and tests in the same slice.
1. Beta-readiness checklist pass:
   - Run `check-all --enforced`, validate docs consistency, and confirm no pending critical warnings.
   - Perform one homelab validation pass if environment/time allows.
1. Toil reduction checkpoint:
   - List top 3 recurring frictions from these two weeks.
   - Convert at least one into automation or documented runbook command.
1. Delivery artifact:
   - End week 2 with one concise summary (what shipped, what stayed carryover, what starts next).

## Daily execution template (very short)

1. Start-of-day (5 min):
   - If plan context feels scattered, use token **`pmo-view`** to open PMO files in Markdown Preview and pick the single daily slice before coding.
   - Confirm top priority slice and risk.
   - Confirm branch/PR state.
1. Build block (60–120 min):
   - Implement one narrow slice.
   - Add/update targeted tests.
1. Gate (10–20 min):
   - Run scripted checks (`check-all` or relevant subset when justified).
   - Fix or rollback before context switching.
1. Close (5 min):
   - Record what was done and next atomic step.

## Auto mode execution pack (token-aware default)

Use this pack when running outside MAX/Turbo, keeping one coherent objective per session:

1. Session start (scope lock):
   - `git status -sb`
   - `git fetch origin`
   - `gh pr list --state open`
1. One-slice execution:
   - pick one slice from `PLANS_TODO.md` and avoid side tracks unless blocking.
1. Quality gate by slice type:
   - docs-only: `.\scripts\lint-only.ps1`
   - code/behavior: `.\scripts\check-all.ps1`
1. Safe close:
   - `.\scripts\preview-commit.ps1`
   - `.\scripts\commit-or-pr.ps1 -Action Preview -Title "<title>" -Body "<bullets>"`
1. Optional progress snapshot:
   - `.\scripts\progress-snapshot.ps1` (today / 3 days / 7 days).

## Today mode (low-attention / high-speed)

When the operator has limited attention/time, run this order:

1. Fast triage:
   - Optional quick scope lock: use **`pmo-view`** first, check `PLANS_TODO.md` + this two-week plan, then commit to one objective.
   - Check open PRs + check status.
   - Pick one single objective for today.
1. Single safe slice:
   - Prefer workflow or regression-proofing change over broad feature change.
1. Minimal proof:
   - One targeted test + one script/check execution.
1. Stop clean:
   - Leave explicit next step (one-liner) to resume tomorrow without re-discovery.
1. If a branch is operator-gated or protected:
   - Prefer status report + park over risky history rewrites.

## PMO shorthand alignment

- **`pmo-view`**: use when you need a fast visual alignment pass (tables/roadmap) before choosing a week or today slice.
- **`feature`**: default execution token for the chosen slice.
- **`sidequest`**: only for bounded detours; always return to the selected two-week/today objective.

## Definition of done (two-week plan)

- No unresolved critical regression/security issue opened by this sprint.
- Core checks remain green on merged slices.
- At least 2 targeted regression tests added (or updated) for real bug-risk areas.
- At least 1 repeatable toil converted to script/automation or a short runbook step.
- One demo-relevant feature slice shipped with docs + tests.
- Carryover has explicit status/date for deferred items (no silent backlog).

## Not in scope (for this 2-week sprint)

- Large refactors crossing many subsystems.
- New broad taxonomy keywords without clear gap from existing ones.
- Multi-front work in parallel that increases review and merge complexity.

## Risks and mitigations

- Risk: overload from too many active tracks.
- Mitigation: one active slice at a time; finish -> gate -> move.
- Risk: green tests but weak coverage on changed behavior.
- Mitigation: mandatory targeted regression test for each fix.
- Risk: productivity loss by context switches.
- Mitigation: use "Today mode" and explicit close note each day.
