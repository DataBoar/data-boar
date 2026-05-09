# LAB Lessons Learned (QA/SRE) — hub

**Português (Brasil):** this page is English-only by convention (same as ADRs and plan prose); the archive folder has **[`lab_lessons_learned/README.pt_BR.md`](lab_lessons_learned/README.pt_BR.md)**.

## What this file is

- **Rolling hub** for the latest lab QA / SRE cycle: scope, verdict, and pointers to **evidence files** (benchmark JSON, checkpoint behaviour, etc.).
- **Immutable history** lives under **`docs/ops/lab_lessons_learned/`** as dated snapshots — see **[`lab_lessons_learned/README.md`](lab_lessons_learned/README.md)** for the contract and ritual.

## Latest session (summary)

**Date:** 2026-05-09 (UTC-3).

**Verdict (short):** Maestro rerun is operationally healthier after wrapper + artifact-sync hardening: Docker precheck is explicit, reachable hosts complete `Deep -> monitor -> Collect`, offline hosts stay warnings. Remaining gaps: one web health target was unavailable in-session, synthetic DB stack deploy is not yet wired in Maestro handlers, and collect/offline exit semantics still need refinement.

**Full narrative (frozen):** [`lab_lessons_learned/LAB_LESSONS_LEARNED_2026_05_09.md`](lab_lessons_learned/LAB_LESSONS_LEARNED_2026_05_09.md)

**Evidence paths (repo):**

- `scripts/maestro-deep-rc-monitor-collect.ps1`
- `scripts/maestro/Sync-ContainerArtefact.ps1`
- Private detailed logs remain in `docs/private/homelab/reports/` (public-safe summary only in this hub/archive).

## Archived sessions (public)

| Session date | Snapshot |
| ------------ | -------- |
| 2026-04-25 | [`lab_lessons_learned/LAB_LESSONS_LEARNED_2026_04_25.md`](lab_lessons_learned/LAB_LESSONS_LEARNED_2026_04_25.md) |
| 2026-04-27 | [`lab_lessons_learned/LAB_LESSONS_LEARNED_2026_04_27.md`](lab_lessons_learned/LAB_LESSONS_LEARNED_2026_04_27.md) (reading guide / regression guard for the 0.574x figure; no new measurement) |
| 2026-05-09 | [`lab_lessons_learned/LAB_LESSONS_LEARNED_2026_05_09.md`](lab_lessons_learned/LAB_LESSONS_LEARNED_2026_05_09.md) (Maestro rerun hardening + public-safe operational snapshot) |

## Follow-ups → plans (tracked)

When a lesson becomes engineering work, promote it to **`docs/plans/PLANS_TODO.md`** (and refresh `python scripts/plans-stats.py --write`). Current bridge from the 2026-05-09 session:

| Topic | Bridge |
| ----- | ------ |
| Maestro synthetic DB stack parity | Align handler path with `LAB_SMOKE_MULTI_HOST` / `LAB_COMPLETAO_RUNBOOK` stack expectations (Postgres/MariaDB/Mongo synthetic flows). |
| Collect/exit semantics with offline nodes | Split hard failure vs warning semantics so mixed rounds remain machine-readable without false-red. |
| Web readiness before long monitor loops | Optional readiness gate when `/health` is expected in test scope. |
| Completão narrative (private) | Use `docs/private/homelab/COMPLETAO_SESSION_*.md` per [`docs/ops/LAB_COMPLETAO_RUNBOOK.md`](LAB_COMPLETAO_RUNBOOK.md); mirror **numbers and pass/fail** here only. |

## Automation / assistant latch

- **Session token:** **`lab-lessons`** (English-only) loads **`.cursor/rules/lab-lessons-learned-archive.mdc`** when globs do not attach it — see [`docs/ops/OPERATOR_AGENT_COLD_START_LADDER.md`](OPERATOR_AGENT_COLD_START_LADDER.md) § *Token → rule latch (`lab-lessons`)`.
- **ADR:** [`docs/adr/0042-lab-lessons-learned-archive-contract.md`](../adr/0042-lab-lessons-learned-archive-contract.md).
