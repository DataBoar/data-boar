# LAB Lessons Learned — session snapshot 2026-05-09

**Archive note:** Immutable snapshot for the UTC-3 lab session focused on Maestro orchestration hardening and rerun validation. Keep this file frozen; add newer sessions as new dated files.

Date: 2026-05-09 (UTC-3 session)

## Scope Executed

- Maestro rerun after local Docker engine startup.
- New wrapper execution path (`Deep -> monitor loop -> Collect`) with explicit precheck.
- Artifact sync hardening for container tar distribution to remote hosts.
- Private evidence capture and structured private session notes update.

## 1) Operational Readiness Outcome

- Wrapper precheck confirms local Docker reachability before `Maestro -Deep`.
- Deep orchestration completed on currently reachable hosts.
- Monitor loop executed with stable `TARGET_ACTIVE` status on reachable hosts.
- Collect phase completed for reachable hosts; offline hosts remained non-blocking warnings.

Public-safe summary:

- Reachable hosts exercised: `4`
- Offline hosts skipped with warnings: `5`

## 2) What improved (code + behavior)

- Added explicit Docker precheck to `scripts/maestro-deep-rc-monitor-collect.ps1`.
- Hardened `scripts/maestro/Sync-ContainerArtefact.ps1`:
  - non-interactive `scp` (`BatchMode`) with timeout;
  - explicit warning path on `scp`/remote load failure;
  - no false positive `SUCCESS` messaging when transfer/load fails.

## 3) Remaining risks

- One web health path (`/health` on configured lab web target) was unavailable during the run window.
- Maestro path still does not include explicit synthetic DB stack deployment (Postgres/MariaDB/Mongo) in handlers; this remains aligned with runbook backlog and should be promoted as tracked follow-up.
- Exit-code semantics still need refinement so partial collect warnings (offline nodes) do not look like full hard failure for otherwise successful online validation.

## 4) Evidence posture (public vs private)

- Detailed host-level logs remain private in `docs/private/homelab/reports/` and `docs/private/homelab/reports/COMPLETAO_SESSION_2026-05-09.md`.
- Public tree carries only aggregate counts, validated behavior, and next actions.

## Follow-ups -> plans (tracked candidates)

| Topic | Bridge |
| ----- | ------ |
| Maestro synthetic DB stack parity | Align handlers/wrapper with lab runbook stack contract from `docs/ops/LAB_SMOKE_MULTI_HOST.md` and `docs/ops/LAB_COMPLETAO_RUNBOOK.md`. |
| Exit-code semantics for mixed online/offline rounds | Refine collect/result contract to separate infra warnings from hard orchestration failure. |
| Web readiness gate | Add optional fast gate before long monitor loops when `/health` is expected in scope. |

