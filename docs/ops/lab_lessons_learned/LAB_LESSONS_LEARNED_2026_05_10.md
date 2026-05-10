# LAB Lessons Learned - session snapshot 2026-05-10

**Archive note:** Immutable snapshot for the UTC-3 lab session focused on Maestro reruns with DB target handlers and cross-host readiness checks.

Date: 2026-05-10 (UTC-3 session)

## Scope Executed

- Maestro wrapper runs with `Deep -> monitor -> Collect` and strict web readiness in the first pass.
- Additional reruns with `-SkipMonitor` to validate DB target handlers (`target_postgres`, `target_mariadb`, `target_mongodb`) under real host constraints.
- Handler hardening iteration for Podman hosts:
  - engine branch ordering and health checks;
  - Podman direct-run fallback for DB services;
  - fully-qualified image references (`docker.io/library/...`) to satisfy short-name policies.

## 1) Operational Readiness Outcome

- Reachable hosts (four inventory nodes: primary lab laptop class, secondary x86 lab host, two edge/SBC class hosts) completed Deep and Collect.
- Offline hosts remained warnings-only, preserving machine-readable success for reachable rounds.
- Web readiness remained healthy on the primary lab laptop class host (`/health` reachable after precheck warning path).
- DB target readiness moved forward:
  - `target_mariadb` on the secondary x86 lab host reached SUCCESS with deterministic port fallback (`33306` in latest run; fallback path available).
  - `target_postgres` on the primary lab laptop class host reached SUCCESS with deterministic port fallback (`55434` in latest run).
  - `target_mongodb` reached SUCCESS when temporarily colocated on the secondary x86 lab host (`27018`), closing the minimum "all DB targets in one run" proof on reachable hosts.

Public-safe summary:

- Reachable hosts exercised: `4`
- Offline hosts skipped with warnings: `5`
- Network-only (ICMP up, SSH down): `1`

## 2) What improved (code + behavior)

- Added dedicated Maestro handlers for DB targets:
  - `scripts/maestro/handlers/Handle-target_mariadb.ps1`
  - `scripts/maestro/handlers/Handle-target_postgres.ps1`
  - `scripts/maestro/handlers/Handle-target_mongodb.ps1`
- Hardened handler logic to avoid provider fragility on Podman-only nodes:
  - Podman path now uses direct `podman run` with explicit seed mounts and published ports.
  - Image references now use fully-qualified names for Podman policy compatibility.
- Anti-regression guard remained green:
  - `uv run pytest tests/test_maestro_scripts.py -q` -> `19 passed`.
- Sync strictness hardening completed:
  - `Sync-WorkingTree` now returns boolean-only (`return [bool]$syncOk`) and only initializes tmux sessions when sync succeeds.
  - `Maestro` now casts sync result as boolean before deciding handler dispatch.

## 3) Remaining risks (now concrete)

- **WSL2 SSH reachability:** designated WSL2 lab host stayed ICMP-only in all observed rounds; Mongo ran via another reachable lab host, accepted as current operational target for this release gate.
- **All-to-all measurement gap:** DB target deployment is operational for reachable hosts, but full cross-host matrix still needs one consolidated evidence round with per-host config capture.

## 4) Evidence posture (public vs private)

- Detailed host outputs and prompts remain private under `docs/private/homelab/reports/`.
- Public tree captures aggregate results, root causes, and explicit next actions only.

## Follow-ups -> plans (tracked candidates)

| Topic | Bridge |
| ----- | ------ |
| DB port-collision handling | Deterministic fallback implemented in handlers; keep as maintenance guard with explicit chosen-port logs. |
| WSL2 Mongo target reachability | Optional future infra follow-up if/when moving Mongo back from the secondary x86 lab host to an isolated WSL2 target becomes desirable. |
| Sync strictness contract | Implemented; keep anti-regression tests to avoid output-stream contamination and false-positive sync truthiness. |
| Cross-host DB matrix evidence | Execute one all-to-all validation round with per-host config files proving each runtime can query all deployed synthetic DB targets. |
