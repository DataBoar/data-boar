# Plan: Two-week execution sprint (no regressions, low toil, fast delivery)

**Status:** Active
**Date:** 2026-03-25
**Authors:** Fabio Leitao
**Priority:** H0

**Synced with:** [PLANS_TODO.md](PLANS_TODO.md)

**Previous template cycles:** Earlier uses of this file without a dated closure are **superseded** by the [Integration / active threads](PLANS_TODO.md) narrative (S0 closed, **S1 – Lab proof** selected). Close each cycle with: green `main`, explicit carryover rows, and one release or demo note if you shipped user-visible slices.

### This cycle — focus (2026-04-21 → 2026-05-04)

| Week | Theme | Outcomes |
| ---- | ----- | -------- |
| **1** | **Enterprise demo signal** | Transport + trust + global access surface exposed as **`enterprise_surface`** on **`GET /status`** / **`GET /health`** (paired slice; **not** full RBAC — see [PLAN_DASHBOARD_REPORTS_ACCESS_CONTROL.md](PLAN_DASHBOARD_REPORTS_ACCESS_CONTROL.md)). Dashboard tinted banner when license trust is **degraded**/**untrusted** or API key is misconfigured. |
| **2** | **Open-core POC / beta readiness** | **`v1.7.3`** ✅ stable baseline — next patch **`1.7.4`**: pick **one** primary (**maturity POC ready** closure **or** first scope-import vendor adapter **or** small governance slice per [PLANS_TODO.md](PLANS_TODO.md)); optional **–1L** lab proof still operator-paced. |

**Definition of done (this cycle):** At least one merged PR with tests for the governance bundle; **`check-all`** green; docs or plan rows updated; **no** silent deferral of **A3** Hub hygiene (operator) or **–1b** Scout if you touched deps/Docker.

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

### Week 1 — Stability and anti-regression baseline

1. PR hygiene baseline:
   - Ensure all active PRs are either merged, updated, or closed as superseded.
   - Require green checks before merge decisions (`gh pr checks` + mergeable state).
1. Automation hardening:
   - Keep `commit-or-pr` and `check-all` as default gate.
   - Eliminate one additional repeated manual step with script support (if any hotspot appears during the week).
1. Tests where it matters:
   - For each bugfix in the week, add one targeted regression test.
   - Avoid broad test rewrites; prioritize deterministic tests around changed behavior.
1. Corporate-Entity-C progression:
   - Pick one Corporate-Entity-C recommendation row and ship one evidence-backed slice.
1. Storage/backup urgency checkpoint (P0):
   - Execute Time Machine USB recovery triage in read-only mode and decide copy path.
   - Only repurpose disk after recovered data is validated.
1. Slack channel B (AFK awareness):
   - `SLACK_WEBHOOK_URL` set; manual ping once; **Slack CI failure notify** validated or accepted (see `OPERATOR_NOTIFICATION_CHANNELS.md` §4.1).

### Week 2 — Delivery and demo readiness

1. One production-relevant feature slice:
   - Choose one small feature with direct demo impact and bounded risk.
   - Include docs and tests in the same slice.
1. Beta-readiness checklist pass:
   - Run `check-all`, validate docs consistency, and confirm no pending critical warnings.
   - Perform one homelab validation pass if environment/time allows.
1. Toil reduction checkpoint:
   - List top 3 recurring frictions from these two weeks.
   - Convert at least one into automation or documented runbook command.
1. Delivery artifact:
   - End week 2 with one clear release-ready summary (what changed, why it matters, what is next).

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
1. If Slack is not yet verified:
   - Run **Actions → Slack operator ping** once; confirm message in your ops channel (secret `SLACK_WEBHOOK_URL`).

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
