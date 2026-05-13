# LAB Lessons Learned (QA/SRE) — hub

**Português (Brasil):** this page is English-only by convention (same as ADRs and plan prose); the archive folder has **[`lab_lessons_learned/README.pt_BR.md`](lab_lessons_learned/README.pt_BR.md)**.

## What this file is

- **Rolling hub** for the latest lab QA / SRE cycle: scope, verdict, and pointers to **evidence files** (benchmark JSON, checkpoint behaviour, etc.).
- **Immutable history** lives under **`docs/ops/lab_lessons_learned/`** as dated snapshots — see **[`lab_lessons_learned/README.md`](lab_lessons_learned/README.md)** for the contract and ritual.

## Latest session (summary)

**Date:** 2026-05-13 (UTC-3).

**Verdict (short):** First confirmed end-to-end A/B benchmark on a real PII corpus.
`boar_fast_filter` compiled on latitude for the first time. Critical config bug found:
`benchmark-rc.yaml` used `scan_scope:` (silently ignored) instead of `targets:` — root cause
of all prior silent "No findings" Deep benchmark runs. Fixed. v1.7.4-rc is **0.955x** (4.5%
faster) on a 10-file LGPD corpus with identical findings. Compressed scan confirmed: minor
detection inside `.zip`/`.tgz`; `.7z` needs `py7zr`. Two new use cases documented (forensic
search, intra-Brazil geographic hints).

**Full narrative (frozen):** [`lab_lessons_learned/LAB_LESSONS_LEARNED_2026_05_13.md`](lab_lessons_learned/LAB_LESSONS_LEARNED_2026_05_13.md)

**Evidence paths (repo):**

- `tests/config/benchmark-rc.yaml` — `scan_scope` → `targets` fix (commit `04d1896`)
- `scripts/maestro-benchmark-ab.ps1` — `-SleepBeforeCollect` Bug 3 fix (commit `1c5e735`)
- `tests/data/bench/synthetic_valid_cpf_3k.txt` — valid CPF corpus (on latitude, 1MB)
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
| 2026-05-13 | [`lab_lessons_learned/LAB_LESSONS_LEARNED_2026_05_13.md`](lab_lessons_learned/LAB_LESSONS_LEARNED_2026_05_13.md) (A/B benchmark confirmed; `scan_scope`→`targets` bug fixed; `boar_fast_filter` compiled on latitude; compressed scan + minor detection validated) |

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
| **`boar_fast_filter` lab venv gap** | `maturin develop --release` needed on each lab host — add to HOMELAB_VALIDATION preflight; confirmed: Rust 1.95 + maturin 1.13.3, 27s compile on latitude. |
| **Unrecognized `scan_scope` config key** | `config/loader.py` should emit WARNING when `scan_scope` key is present but `targets` is not; currently silently ignored — operators get "No findings" with no error. |
| **0.574x claim validation pending** | Current A/B shows 0.955x on 10-file corpus; needs `tests/data/bench/synthetic_valid_cpf_3k.txt` (3000 lines, 1MB) for meaningful comparison. |
| **Forensic search + geo hints** | `PLAN_FORENSIC_SEARCH_AND_GEOGRAPHIC_HINTS.md` — Slice 1 of both use cases is low effort; promote to H1 if Engajamento A validates demand. |

## Automation / assistant latch

- **Session token:** **`lab-lessons`** (English-only) loads **`.cursor/rules/lab-lessons-learned-archive.mdc`** when globs do not attach it — see [`docs/ops/OPERATOR_AGENT_COLD_START_LADDER.md`](OPERATOR_AGENT_COLD_START_LADDER.md) § *Token → rule latch (`lab-lessons`)`.
- **ADR:** [`docs/adr/ADR-0042-lab-lessons-learned-archive-contract.md`](../adr/ADR-0042-lab-lessons-learned-archive-contract.md).
