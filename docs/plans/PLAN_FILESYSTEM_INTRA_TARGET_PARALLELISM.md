# Plan: Filesystem intra-target parallelism (worker pool inside one target)

**Status:** Active (pool implemented on branch, benchmark pinned; resume per file is roadmap)
**Date:** 2026-11-14
**Authors:** Fabio Leitao
**Priority:** H1 / U1 (GitHub milestone v1.8.2 after the #2240 renumbering; pulled forward for the 18/Nov presentation by operator order)
**GitHub:** [#1820](https://github.com/DataBoar/data-boar/issues/1820) (pair of [#1322](https://github.com/DataBoar/data-boar/issues/1322) on the DB axis; cap from [#551](https://github.com/DataBoar/data-boar/issues/551); free-threading from [#1409](https://github.com/DataBoar/data-boar/issues/1409); resume from [#1330](https://github.com/DataBoar/data-boar/issues/1330))

<!-- plans-hub-summary: Worker pool inside one filesystem/NFS target (pure-Python threads, tier cap from #551, no new cap): workers read and detect, the target thread persists in walk order for exact serial parity; atomic inode dedup; pinned 3.14t vs GIL benchmark; per-file resume surveyed and left as roadmap (#1820). -->
<!-- plans-hub-related: PLAN_BENCHMARK_SAFE_AXIS.md, PLAN_SCHEMA_MIGRATION.md -->

**Synced with:** [PLANS_TODO.md](PLANS_TODO.md)

## Motivation

Before this plan, `core/engine.py` parallelised only **across targets**: one large filesystem tree was one target, one thread. `iter_scan_files` walked serially and `FilesystemConnector.run` read and detected one file at a time. On a local disk the time goes to detection (`filesystem_phase_breakdown_v1`: walk 0.08 %, read 0.21 %, detect 99.72 % of 2 000 `.txt` files), which is CPU work; on NFS/SSHFS each read also waits on the network.

## Decisions (operator, on the issue thread — not reopened here)

1. **Pure Python, no native extension** (2026-08-28). Threads from `concurrent.futures.ThreadPoolExecutor`. A Rust/C++/Zig extension running OS threads would bypass the GIL for every tier and leak the free-threading perk that #1409 reserves through the interpreter gate (`core/licensing/gil_container_gate.py`). With the GIL, threads only overlap I/O waits; on a free-threaded build the same code runs detection in parallel.
2. **No new cap.** The pool size comes from `scan.max_workers` **after** the existing clamp in `AuditEngine.start_audit`: `LicenseGuard.worker_cap()` (`dbmax_workers` claim, then `_TIER_DEFAULT_WORKER_CAP`: Community 2, Std 2, Pro 4, Pro+ 8, Enterprise and Partner unlimited) and the open-mode clamp `OPEN_MODE_WORKER_CAP = 2` (#856).
3. **Dedup must be thread-safe** with a dedicated concurrency test.

## Design (as implemented)

| Piece | Where | What |
| ----- | ----- | ---- |
| Budget | `core/engine.py` `_intra_target_worker_budget(max_workers, concurrent_targets)` | `max(1, max_workers // min(max_workers, n_targets))`, so `outer × inner ≤ max_workers` (no W² pool of pools). Computed once per run in `_run_audit_targets`. |
| Injection | `core/engine.py` `_run_target_inner` | `filesystem` and `nfs` targets (`NFSConnector` delegates to `FilesystemConnector`) receive `_intra_target_workers`. Other connectors are unchanged. |
| Serial path | `FilesystemConnector.run` | `workers <= 1` (default `scan.max_workers: 1`, or a direct construction without the key): same loop as before, no pool, writes go straight to `db_manager`. |
| Pool path | `FilesystemConnector._run_pool` | The target thread walks (`iter_scan_files`), filters by extension, submits `_process_file` to the pool. Each worker fills a `_RecordingSink`; the target thread replays sinks **in submission order** (`save_failure`, `on_read_barrier` failures, `save_finding`, `upsert_object_state`, audit log line). In-flight window = 4 × workers. |
| Dedup | `InodeDedup` (`claim` / `claim_dir`, one lock) | Replaces the two local sets in `iter_scan_files`; optional `dedup=` argument lets concurrent walkers share one claim set. |
| Stop | `finally: pool.shutdown(wait=True, cancel_futures=True)` | `KeyboardInterrupt` (Ctrl+C, and SIGTERM mapped by #1251) or any error: queued items are dropped, running items finish, no pool thread survives `run()`. There is no other stop API today. |
| Errors | `_drain_oldest` | A read failure is already swallowed by `_read_text_sample` (empty sample; barrier reasons recorded). An unexpected per-file exception keeps today's semantics: writes recorded before it are kept and the target aborts at the **same ordered position** as the serial path (the engine records the `error` failure). |

Thread names start with `databoar-fs-intra` (`INTRA_TARGET_THREAD_PREFIX`).

### Tier behaviour

| Tier / mode | Effective pool for one target | Note |
| ----------- | ----------------------------- | ---- |
| Any, `scan.max_workers: 1` (default) | 1 (serial, identical to before) | |
| Open mode | up to 2 | #856 clamp |
| Community / Std | up to 2 | **Behaviour change** when `max_workers ≥ 2` and few targets: those 2 slots used to sit idle on a single target. See *Open question for the operator*. |
| Pro | up to 4 | |
| Pro+ | up to 8 | |
| Enterprise / Partner | `scan.max_workers` (or the `dbmax_workers` claim) | Only tier where a free-threaded runtime is allowed by #1409, so the only one with CPU-parallel detection. |

## Tests (TDD, synthetic data only)

`tests/test_filesystem_intra_target_parallelism.py` (items `d1820_a` … `d1820_f`):

- **(a)** exact parity of persisted findings and `scan_failures` (same rows, same fields, same order) for 2/4/8 workers on a corpus with sub-folders, file and directory symlinks, hard links, 2 MB files, corrupt and encrypted PDFs and a permission-denied file; once with the real `DataScanner`; DB writes only on the target thread.
- **(b)** `workers = 1` builds no pool and matches the parallel output; no key means serial.
- **(c)** observed concurrency equals the budget (barrier, no sleeps); budget table; engine end-to-end per tier with enforced test JWTs (Community 2, Pro 4, Pro+ 8, claim 3, Enterprise 6, Community with `max_workers: 1`), open-mode clamp, two targets split 2 + 2 under Pro.
- **(d)** `InodeDedup.claim` under 16 threads; 8 threads walking overlapping trees with hard links, symlinks and a directory symlink visit each inode once; parallel scan detects each inode once.
- **(e)** read failures keep the pool and every other finding; an unexpected detector error aborts at the serial position.
- **(f)** interrupt on the target thread or inside a worker leaves no pool thread alive.

The same file passes 5/5 runs on free-threaded 3.14t with `-X gil=0`.

## Measurement

Runner: `tests/benchmarks/run_filesystem_intra_target_bench.py`; artifacts `tests/benchmarks/filesystem_intra_target_nogil.json` and `filesystem_intra_target_gil.json`; evidence test `tests/test_filesystem_intra_target_evidence.py`. Reproduce commands are in [tests/benchmarks/README.md](../../tests/benchmarks/README.md).

**Interim (2026-11-14, primary dev workstation, 12 CPUs, 2 000 synthetic `.csv`, commit `11c8db04`, CPython 3.14.10 free-threaded, GIL off before and after):** exact parity in every row, but the pool is **slower** on 3.14t: median 12.9 s serial vs 18.6 s (2 workers), 119.6 s (4), 170.7 s (8) on local disk; with 2 ms simulated read latency 17.9 s serial vs 15.8 s (2), 110.8 s (4), 175.4 s (8). Contention inside the worker path (read + detect) is under investigation before any speed claim; the 3.14-with-GIL run is pending. The artifacts are not committed until the cause is understood.

## Risks

| Risk | Mitigation / status |
| ---- | ------------------- |
| Order of findings changes | Replay in submission order: the persisted order is the serial order (tested). Audit log lines from **archive members** (`scan_archive_at_path`) are emitted on the worker, so their log order may interleave; the persisted rows do not. |
| SQLite contention (`NullPool`, one connection per call) | Workers never write; only the target thread does. Multi-target runs already wrote from several threads before #1820; that is unchanged. |
| `upsert_object_state` read-modify-write race | Same: one writer per target. |
| Memory | Window of 4 × workers recorded samples; samples are capped by `file_sample_max_chars`. |
| `on_read_barrier` | Recorded in the sink and replayed before the finding of the same file, as in the serial order. |
| Symlink / traversal guards (#1579, #1560) | Walk unchanged and still single-threaded per target; `_path_contained_under_root` and directory-symlink refusal untouched. |
| Hard-link "winner" | Serial walk keeps it deterministic. A parallel walk would make the reported alias a race (see roadmap). |
| Detector thread safety | `DataScanner` was already shared across parallel targets; the real-detector parity test and the 3.14t runs exercise it inside one target. |
| Integrity manifest | `connectors/*.py` and `core/engine.py` are `CRITICAL_MODULES`: an image built from this branch shows the runtime integrity warning until the operator re-signs the manifest for the release. |
| Behaviour change on Community/open with `max_workers ≥ 2` | Open question below. |

## Open question for the operator

Public project rule: new features are born Enterprise. Today the pool follows the existing worker cap, so Community/open with `scan.max_workers: 2` gets 2 threads inside a single target (under the GIL that only overlaps I/O). Options: (1) keep as is — the cap already *is* the tier mechanism, no new knob; (2) restrict the intra-target pool to Enterprise, which needs a tier check in the budget (a new gate, against decision 2). The implementation follows (1) until the operator decides.

## Out of scope (this plan)

- **Parallel walk / one work item per top-level folder.** Walk is 0.08 % of the local profile, below the 15 % gate of `filesystem_phase_breakdown_v1`; a parallel walk makes the reported path of a hard link or duplicate symlink a race and breaks exact parity. `InodeDedup` and `iter_scan_files(dedup=...)` are ready for it; revisit with an SSHFS/NFS measurement where `scandir` latency dominates.
- SMB, WebDAV, SharePoint connectors (separate code paths).
- Adaptive throttling inside the target (`BoarThrottler` stays per target).
- Any native extension.

## Resume per file (#1330 survey — evidence, not implemented)

`--resume <session>` checkpoints SQL/Snowflake tables only (`ScanTableCheckpoint`). Executed locally on 2026-11-14 (branch code, serial path, 6 000 synthetic `.csv` files, one filesystem target):

| Kill | Session status after kill | Rows before resume | After `--resume` | Distinct files |
| ---- | ------------------------- | ------------------ | ---------------- | -------------- |
| SIGTERM at 8 s (#1251 → `KeyboardInterrupt`) | `interrupted` | 346 | 6 346 (`completed`) | 6 000 |
| SIGKILL at 8 s | `running` | 341 | 6 341 (`completed`) | 6 000 |

A filesystem target is **re-scanned from the start**: nothing is lost, but every finding saved before the kill is **duplicated** inside the same session (346 and 341 duplicate rows). `scan_object_state` is not a usable base as is: it is keyed by `(target_name, abs_path)` across sessions and is written only for files **with** a finding, so clean files leave no trace. (A SIGINT sent to a background job of a non-interactive shell is ignored by the interpreter; operators press Ctrl+C in a foreground terminal, which behaves like the SIGTERM row.)

**Minimal design (roadmap):** new table `scan_file_checkpoints(session_id, target_name, abs_path, mtime_ns, size)` plus `_ensure_*` migration (`PLAN_SCHEMA_MIGRATION.md`); the target thread inserts one row per processed file **after** its sink is replayed (clean files included), committed in batches of ~500; on resume, the connector skips files whose `(abs_path, mtime_ns, size)` is already checkpointed for that session, and a changed file is re-scanned. Risks: one extra write per file (measure the overhead on the local profile), batch boundary may re-scan up to one batch (re-introducing up to ~500 duplicates unless findings of the unconfirmed batch are deleted on resume), path canonicalisation for symlink aliases. Effort: about 2 days with tests (schema + migration test + connector skip + kill/resume integration test). Not implemented in this slice.

## Phases

| Phase | Status |
| ----- | ------ |
| Plan + red tests | ✅ |
| Pool + budget + atomic dedup | ✅ |
| Pinned benchmark (3.14t vs 3.14 GIL, dev workstation) | ⬜ in progress — 3.14t shows contention |
| Resume survey | ✅ |
| Demo image + VPS measurement (operator / PM) | ⬜ |
| Resume per file | ⬜ roadmap |
| Parallel walk (top-level folders) | ⬜ roadmap, needs network-FS measurement |
