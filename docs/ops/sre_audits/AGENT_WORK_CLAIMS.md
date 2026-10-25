# Agent Work Claims — coordination ledger for SRE automation

> **Purpose:** Stop parallel SRE agents (Cursor Web automation, cron
> triggers, Slack triggers) from editing the same files in disjoint draft
> PRs. This is a lightweight, read-mostly ledger — not a hard lock — until
> a real `scripts/agent-claim.ps1` (or equivalent) lands.

## How to use this file (60-second pre-flight)

1. **Read the table below.** If your slice overlaps a row whose `Expires`
   is in the future, **do not edit those files**. Pick a different slice or
   add a sub-claim with explicit non-overlapping scope.
2. **Add your row** at the bottom of the table *before* the first edit, in
   the same commit as your work. This is the "claim" — visible to any other
   agent that does step (1).
3. **TTL is 24h** by default. If your work runs longer, push a follow-up
   commit that bumps `Expires`. If you abandon the slice, replace the row
   with `cancelled` instead of deleting it (so log archeology stays cheap).
4. **CI is intentionally not enforcing this yet** — it is discipline, not a
   gate. Treat it like the `ADR` habit: the cost of skipping it is felt by
   the *next* agent, not by you.

## Schema

| Column | Meaning |
| ------ | ------- |
| `PR / Branch` | Draft PR number (or branch name if PR not opened yet). |
| `Agent run` | Slack `message_ts` or short identifier of the trigger. |
| `Slice` | Short human-readable scope (one line). |
| `File scope` | Concrete files or globs the slice will edit. |
| `Started` | UTC `YYYY-MM-DD HH:MM`. |
| `Expires` | UTC `YYYY-MM-DD HH:MM` (Started + 24h unless overridden). |
| `Status` | `active` / `merged` / `cancelled` / `superseded-by-#NNN`. |

## Active claims (2026-04-27)

| PR / Branch | Agent run | Slice | File scope | Started | Expires | Status |
| ----------- | --------- | ----- | ---------- | ------- | ------- | ------ |
| #232 | sre-agent-protocol-c70a | Doctrine Slices 2-4 (RCA + benchmark evolution) | `cli/reporter.py`, `connectors/sql_sampling.py`, `core/scan_audit_log.py`, `docs/plans/BENCHMARK_EVOLUTION.md`, `docs/plans/PLAN_ENGINEERING_DOCTRINE_CONSOLIDATION.md`, `report/executive_report.py`, `scripts/lab-completao-orchestrate.ps1` | 2026-04-27 16:10 | 2026-04-28 16:10 | active |
| #233 | sre-automation-agent-protocol-5fc6 | Move `SLACK_WEBHOOK_URL` guard out of job-level `if:` | `.github/workflows/slack-*.yml` (5 files) | 2026-04-27 16:13 | 2026-04-28 16:13 | active |
| #234 | sre-automation-agent-protocol-8d7e | SRE security audit of open PRs (snapshot) | `docs/ops/sre_audits/PR_SECURITY_AUDIT_2026-04-27.md`, `docs/ops/sre_audits/README.md` | 2026-04-27 16:20 | 2026-04-28 16:20 | active |
| #235 | sre-agent-protocol-0871 | Single-pass fused regex (Pro engine) | `core/prefilter.py`, `pro/engine.py`, `pro/worker_logic.py`, `tests/benchmarks/...`, post-mortem docs | 2026-04-27 16:25 | 2026-04-28 16:25 | active |
| #236 | sre-agent-protocol-4c97 | Slices 2-4 doctrine cycle (RCA + single-pass + 0.574x baseline) | `cli/reporter.py`, `pro/engine.py`, `pro/worker_logic.py`, `docs/plans/BENCHMARK_EVOLUTION.md`, `docs/plans/PLAN_ENGINEERING_DOCTRINE_CONSOLIDATION.md`, `docs/plans/PLANS_TODO.md`, `tests/test_basic_python_scan_single_pass_parity.py`, `tests/test_cli_reporter_rca.py` | 2026-04-27 16:27 | 2026-04-28 16:27 | active — **overlaps #232 and #235** |
| #237 | sre-automation-agent-protocol-51fe | Bilingual pt-BR doctrine manifestos | `docs/ops/inspirations/*.pt_BR.md` (12 files) | 2026-04-27 16:30 | 2026-04-28 16:30 | active |
| #238 | sre-automation-agent-protocol-80c8 | Drop bogus T-SQL `OPTION (MAX_EXECUTION_TIME)` | `connectors/sql_sampling.py` and tests | 2026-04-27 16:31 | 2026-04-28 16:31 | active — **may overlap #232 sql_sampling.py edit** |
| #239 | sre-automation-agent-protocol-6bb4 | Dependabot-resync helper + Guardian audit | `scripts/dependabot-resync.{ps1,sh}`, `docs/ops/sre_audits/PR_SECURITY_AUDIT_2026-04-27_dependency_guardian.md`, `docs/ops/sre_audits/README.md` | 2026-04-27 16:49 | 2026-04-28 16:49 | active — **overlaps #234 README.md** |
| #240 | sre-automation-agent-protocol-1b76 | Close protocol-relative open-redirect in WebAuthn `safe_next_path` | `core/webauthn_*.py`, regression test | 2026-04-27 17:02 | 2026-04-28 17:02 | active |
| #241 | sre-automation-agent-protocol-6d0b | SRE PR Risk Assessor audit + reviewer assignment | `docs/ops/sre_audits/PR_RISK_ASSESSMENT_2026-04-27_assessor.md`, `docs/ops/sre_audits/README.md` | 2026-04-27 17:04 | 2026-04-28 17:04 | active — **overlaps #234 README.md** |
| #242 | sre-agent-protocol-d67a | Dependency Guardian verdict ledger | `docs/ops/sre_audits/DEPENDENCY_GUARDIAN_VERDICT_LEDGER_2026-04-27.md`, `docs/ops/sre_audits/README.md` | 2026-04-27 17:13 | 2026-04-28 17:13 | active — **overlaps #234 README.md** |
| (this PR) | sre-automation-agent-protocol-fb6c (`1777310177.655909`) | Pipeline health-check & diagnostic + claim ledger | `docs/ops/sre_audits/PIPELINE_VITALS_2026-04-27.md`, `docs/ops/sre_audits/AGENT_WORK_CLAIMS.md` | 2026-04-27 17:16 | 2026-04-28 17:16 | active — collision-free (new files only) |

## Suggested merge order (to minimise rebase pain)

This is advisory; the maintainer decides.

1. **#240** (security fix, isolated 2-file diff) — can land any time.
2. **#238** (security fix, narrow `connectors/sql_sampling.py` slice) — land
   before #232 so #232's RCA-block edit to the same file is the rebase, not
   the loser.
3. **#233** (CI guard fix, isolated to `.github/workflows/slack-*.yml`).
4. **#237** (pt-BR docs, isolated to inspirations folder).
5. **Cluster B (audit ledger):** **#234 → #239 → #241 → #242** in that
   order. The first one creates `README.md`; the others rebase to extend it.
6. **Cluster A (doctrine slices):** **#235 → #232 → #236**, with #236
   trimmed to its non-overlapping diff (the new tests are the unique
   contribution; the `pro/engine.py` and `cli/reporter.py` edits should be
   reviewed for redundancy with #235 and #232).
7. **Dependabot backlog (#221-#226):** standard `chore(deps):` triage after
   the SRE cluster clears.

## Why a markdown ledger (not a real lock file)

- **Defensive architecture** (`DEFENSIVE_SCANNING_MANIFESTO.md`): a real
  cross-process lock would be tempting to bolt onto SQLite/Redis/whatever
  the agents already touch — no thanks. A markdown table edited inside the
  same PR has zero blast radius.
- **Fallback discipline** (`THE_ART_OF_THE_FALLBACK.md`): the ledger *is*
  the fallback for the still-unbuilt automated lock. When the real
  primitive lands, this file becomes the seed dataset for it.
- **GTD-friendly:** the ledger doubles as a status board the maintainer can
  scan from a phone GitHub mobile session, no terminal required.

## Future hardening (out of scope for this PR)

- `scripts/agent-claim.ps1 -PrNumber <N> -Files <glob>` that appends a row
  here, refuses to start if the scope overlaps an active row, and emits a
  `ci-fail-claim-conflict` artifact so CI can flag races.
- Pre-commit hook that fails if a PR diff touches files claimed by another
  active row (cross-PR; needs `gh` in the hook environment, so opt-in).
- Slack `:octagonal_sign:` reply from `slack-operator-ping` workflow when a
  new claim conflicts with an active one.
