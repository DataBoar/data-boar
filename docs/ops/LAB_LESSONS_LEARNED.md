# LAB Lessons Learned (QA/SRE) — hub

**Português (Brasil):** this page is English-only by convention (same as ADRs and plan prose); the archive folder has **[`lab_lessons_learned/README.pt_BR.md`](lab_lessons_learned/README.pt_BR.md)**.

## What this file is

- **Rolling hub** for the latest lab QA / SRE cycle: scope, verdict, and pointers to **evidence files** (benchmark JSON, checkpoint behaviour, etc.).
- **Immutable history** lives under **`docs/ops/lab_lessons_learned/`** as dated snapshots — see **[`lab_lessons_learned/README.md`](lab_lessons_learned/README.md)** for the contract and ritual.

## Latest session (summary)

**Date:** 2026-06-18 (UTC-3).

**Verdict (short):** Release-gate (#406) acceptance attempt for `1.7.4-rc` → `1.7.4`, run from
the temporary primary Linux dev workstation ([ADR 0068](../adr/ADR-0068-primary-linux-dev-workstation-temporary.md)).
**Gate NOT accepted** — finding-parity never measured; the scan did not start on any node.
Blocked **before** any audit by two infra-level issues (not product defects): a
**Windows-bound orchestrator** (`cmd.exe` core) that cannot run on the only available host,
and **persistent per-node provisioning gaps** (`uv` non-interactive `PATH`; native fast-filter
extension absent on ARM/musl/minimal nodes) that **recur across the fleet**. Central lesson:
the same failure on N nodes is **signal aggregation = "lab not provisioned"** that should
escalate and abort, not be retried as per-node noise. Gate stays **OPEN**; **no** version bump.

**Full narrative (frozen):** [`lab_lessons_learned/LAB_LESSONS_LEARNED_2026_06_18.md`](lab_lessons_learned/LAB_LESSONS_LEARNED_2026_06_18.md)

**Evidence paths:**

- `scripts/lab-completao-orchestrate.ps1` — `cmd.exe` core (`Invoke-CmdCapture`) blocks Linux execution
- `docs/private/homelab/reports/completao_20260618_*_orchestrate_events.jsonl` — preflight `ok` → runner death (private)
- `docs/private/homelab/COMPLETAO_SESSION_2026-06-18.md` — per-host narrative (private; public summary only here)

## Previous session (summary)

**Date:** 2026-05-13 (UTC-3).

**Verdict (short):** First confirmed end-to-end A/B benchmark on a real PII corpus.
`boar_fast_filter` compiled on the laptop lab node for the first time. Critical config bug found:
`benchmark-rc.yaml` used `scan_scope:` (silently ignored) instead of `targets:` — root cause
of all prior silent "No findings" Deep benchmark runs. Fixed. v1.7.4-rc is **0.955x** (4.5%
faster) on a 10-file LGPD corpus with identical findings. Compressed scan confirmed: minor
detection inside `.zip`/`.tgz`; `.7z` needs `py7zr`. Two new use cases documented (forensic
search, intra-Brazil geographic hints).

**Full narrative (frozen):** [`lab_lessons_learned/LAB_LESSONS_LEARNED_2026_05_13.md`](lab_lessons_learned/LAB_LESSONS_LEARNED_2026_05_13.md)

**Evidence paths (repo):**

- `tests/config/benchmark-rc.yaml` — `scan_scope` → `targets` fix (commit `04d1896`)
- `scripts/maestro-benchmark-ab.ps1` — `-SleepBeforeCollect` Bug 3 fix (commit `1c5e735`)
- `tests/data/bench/synthetic_valid_cpf_3k.txt` — valid CPF corpus (on the laptop lab node, 1MB)
- `docs/plans/PLAN_FORENSIC_SEARCH_AND_GEOGRAPHIC_HINTS.md` — new use case plan
- Private logs remain in `docs/private/homelab/reports/` (public-safe summary only here).

**Verdict (short):** Maestro `Deep -> monitor -> Collect` is stable for reachable hosts with deterministic DB target fallback and stricter sync contract: Postgres, MariaDB, and MongoDB executed together in one run with Mongo colocated on a reachable secondary lab host (inventory alias recorded only under `docs/private/`). Sync flow now returns boolean-only and only initializes tmux after valid sync, preventing handler dispatch on contaminated output paths.

**Full narrative (frozen):** [`lab_lessons_learned/LAB_LESSONS_LEARNED_2026_05_10.md`](lab_lessons_learned/LAB_LESSONS_LEARNED_2026_05_10.md)

**Evidence paths (repo):**

- `scripts/maestro-deep-rc-monitor-collect.ps1`
- `scripts/maestro/Build-ContainerArtefact.ps1`
- `scripts/maestro/Sync-ContainerArtefact.ps1`
- `scripts/maestro/handlers/Handle-target_mariadb.ps1`
- `scripts/maestro/handlers/Handle-target_postgres.ps1`
- `scripts/maestro/handlers/Handle-target_mongodb.ps1`
- Private detailed logs remain in `docs/private/homelab/reports/` (public-safe summary only in this hub/archive).

## Archived sessions (public)

| Session date | Snapshot |
| ------------ | -------- |
| 2026-04-25 | [`lab_lessons_learned/LAB_LESSONS_LEARNED_2026_04_25.md`](lab_lessons_learned/LAB_LESSONS_LEARNED_2026_04_25.md) |
| 2026-04-27 | [`lab_lessons_learned/LAB_LESSONS_LEARNED_2026_04_27.md`](lab_lessons_learned/LAB_LESSONS_LEARNED_2026_04_27.md) (reading guide / regression guard for the 0.574x figure; no new measurement) |
| 2026-05-09 | [`lab_lessons_learned/LAB_LESSONS_LEARNED_2026_05_09.md`](lab_lessons_learned/LAB_LESSONS_LEARNED_2026_05_09.md) (Maestro rerun hardening + public-safe operational snapshot) |
| 2026-05-10 | [`lab_lessons_learned/LAB_LESSONS_LEARNED_2026_05_10.md`](lab_lessons_learned/LAB_LESSONS_LEARNED_2026_05_10.md) (DB target handlers enabled; Podman target fixed for MariaDB; remaining port/SSH blockers captured) |
| 2026-05-13 | [`lab_lessons_learned/LAB_LESSONS_LEARNED_2026_05_13.md`](lab_lessons_learned/LAB_LESSONS_LEARNED_2026_05_13.md) (A/B benchmark confirmed; `scan_scope`→`targets` bug fixed; `boar_fast_filter` compiled on the laptop lab node; compressed scan + minor detection validated) |
| 2026-06-18 | [`lab_lessons_learned/LAB_LESSONS_LEARNED_2026_06_18.md`](lab_lessons_learned/LAB_LESSONS_LEARNED_2026_06_18.md) (#406 acceptance blocked: Windows-bound orchestrator + recurring fleet provisioning gaps; gate stays open) |

## Follow-ups → plans (tracked)

When a lesson becomes engineering work, promote it to **`docs/plans/PLANS_TODO.md`** (and refresh `python scripts/plans-stats.py --write`). Current bridge from the 2026-05-09 session:

| Topic | Bridge |
| ----- | ------ |
| Maestro synthetic DB stack parity | Minimum all-in-one run succeeded on reachable hosts (Postgres + MariaDB + MongoDB); next closure is full all-to-all evidence with additional hosts online. |
| Collect/exit semantics with offline nodes | Implemented baseline (`warnings != hard-fail`); keep as maintenance guard only. |
| Web readiness before long monitor loops | Implemented (`skip/warn/fail` gate in wrapper + runtime behavior proven). |
| WSL2 lab target reachability | Optional infra follow-up only (out of current release gate) if/when you want Mongo back on isolated WSL2 host. |
| Sync strictness on rsync warning | Implemented: `Sync-WorkingTree` now returns boolean-only and gates tmux/session init behind successful sync; Maestro casts sync result as boolean before handler dispatch. Keep as maintenance guard. |
| Completão narrative (private) | Use `docs/private/homelab/COMPLETAO_SESSION_*.md` per [`docs/ops/LAB_COMPLETAO_RUNBOOK.md`](LAB_COMPLETAO_RUNBOOK.md); mirror **numbers and pass/fail** here only. |
| **`.7z` support missing** | Add `py7zr` to `pyproject.toml` `[compressed]` optional extra — `sample2.7z` failed with `archive_unsupported` (2026-05-13 session). |
| **`boar_fast_filter` lab venv gap** | `maturin develop --release` needed on each lab host — add to HOMELAB_VALIDATION preflight; confirmed: Rust 1.95 + maturin 1.13.3, 27s compile on the laptop lab node. |
| **Unrecognized `scan_scope` config key** | **Closed:** `normalize_config()` logs WARNING when `scan_scope:` is present (`config/loader.py`; test `test_scan_scope_key_emits_warning`). |
| **0.574x claim validation pending** | Current A/B shows 0.955x on 10-file corpus; needs `tests/data/bench/synthetic_valid_cpf_3k.txt` (3000 lines, 1MB) for meaningful comparison. |
| **Forensic search + geo hints** | `PLAN_FORENSIC_SEARCH_AND_GEOGRAPHIC_HINTS.md` — Slice 1 of both use cases is low effort; promote to H1 if Engajamento A validates demand. |
| **Cross-platform completão runner** | `lab-completao-orchestrate.ps1` `cmd.exe` core blocks Linux execution (2026-06-18). Replace with a Linux-capable transport so the gate can run from the primary Linux dev workstation (ADR-0068). |
| **Fleet `uv` non-interactive PATH** | `uv` missing from non-interactive SSH `PATH` on multiple nodes (2026-06-18) → scans never start. Provision `PATH` (e.g. `~/.profile`/sudoers env) fleet-wide. |
| **Native fast-filter build matrix** | `boar_fast_filter` is x86_64-glibc only; ARM/musl/minimal nodes lack a wheel **and** on-host Rust/maturin (recurrence of the 2026-05-13 single-node follow-up). Multi-arch/musl wheels or accept pure-Python fallback scope. |
| **Auditor escalates repeated failure** | Smoke/orchestrator should aggregate the **same failure across N nodes** into a single "lab-not-provisioned" verdict and abort with a diagnosis, instead of per-node retry (2026-06-18 lesson). |
| **`protect_canonical` guard** | Make canonical-clone protection load-bearing in the Maestro sync path (covers both primary dev hosts), not a runtime agent decision — ties to ADR-0068. |

## Automation / assistant latch

- **Session token:** **`lab-lessons`** (English-only) loads **`.cursor/rules/lab-lessons-learned-archive.mdc`** when globs do not attach it — see [`docs/ops/OPERATOR_AGENT_COLD_START_LADDER.md`](OPERATOR_AGENT_COLD_START_LADDER.md) § *Token → rule latch (`lab-lessons`)`.
- **ADR:** [`docs/adr/ADR-0042-lab-lessons-learned-archive-contract.md`](../adr/ADR-0042-lab-lessons-learned-archive-contract.md).
