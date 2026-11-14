# Plan: Filesystem intra-target parallelism (worker pool inside one target)

**Status:** Active (pool, detector ML fix, per-file resume with batched atomic writes; parallel walk and DB per-table parallelism are separate work)
**Date:** 2026-11-14
**Authors:** Fabio Leitao
**Priority:** H1 / U1 (GitHub milestone v1.8.2 after the #2240 renumbering; pulled forward for the 18/Nov presentation by operator order)
**GitHub:** [#1820](https://github.com/DataBoar/data-boar/issues/1820) (pair of [#1322](https://github.com/DataBoar/data-boar/issues/1322) on the DB axis; cap from [#551](https://github.com/DataBoar/data-boar/issues/551); free-threading from [#1409](https://github.com/DataBoar/data-boar/issues/1409); resume from [#1330](https://github.com/DataBoar/data-boar/issues/1330))

<!-- plans-hub-summary: Worker pool inside one filesystem/NFS target (pure-Python threads, tier cap from #551, no new cap): workers read and detect, the target thread persists in walk order for exact serial parity; atomic inode dedup; pinned 3.14t vs GIL benchmark; per-file resume with batched atomic writes, no duplicates after SIGTERM/SIGKILL (#1820). -->
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
| Stop | `finally: pool.shutdown(wait=True, cancel_futures=True)` | An interrupt or error raised on the target thread or in a worker: queued items are dropped, running items finish, no pool thread survives `run()`. There is no other stop API today. **Limit (found 2026-11-14 with #1322):** the pool only exists with `scan.max_workers > 1`, where the engine runs the target on its own thread pool; a SIGTERM / Ctrl+C lands in the main thread and the engine waits for the target to finish (measured: exit 5.1 s after SIGTERM, all 3 000 files scanned). See PLAN_DB_PER_TABLE_PARALLELISM.md. |
| Errors | `_drain_oldest` | A read failure is already swallowed by `_read_text_sample` (empty sample; barrier reasons recorded). An unexpected per-file exception keeps today's semantics: writes recorded before it are kept and the target aborts at the **same ordered position** as the serial path (the engine records the `error` failure). |

Thread names start with `databoar-fs-intra` (`INTRA_TARGET_THREAD_PREFIX`).

### Tier behaviour

| Tier / mode | Effective pool for one target | Note |
| ----------- | ----------------------------- | ---- |
| Any, `scan.max_workers: 1` (default) | 1 (serial, identical to before) | |
| Open mode | up to 2 | #856 clamp |
| Community / Std | up to 2 | **Behaviour change** when `max_workers ≥ 2` and few targets: those 2 slots used to sit idle on a single target. Accepted; see *Tier decision*. |
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

Runner: `tests/benchmarks/run_filesystem_intra_target_bench.py`; artifacts `tests/benchmarks/filesystem_intra_target_{nogil,gil}.json` (with the fix) and `filesystem_intra_target_{nogil,gil}{,_ml_lock}_before_fix.json`; evidence test `tests/test_filesystem_intra_target_evidence.py`. Reproduce commands are in [tests/benchmarks/README.md](../../tests/benchmarks/README.md).

**Pinned results** (2026-11-14, primary dev workstation, 12 CPUs, one target of 2 000 synthetic `.csv` files plus 80 alias links, whole scan through `AuditEngine.start_audit` — walk, read, detect, persist, no report; median in seconds of 3 iterations (before fix) or 5 iterations (fix: load average 1 min 1.06 at the start of the `cedd97cf` run; re-measurement at `3736feda`: 1.31 at the start of the 3.14t run and 2.60 at the start of the 3.14 run, recorded in each JSON); exact finding parity, ordered and sorted, in **every** row; GIL state identical before and after each run):

| Runtime | Detector ML step | Profile | Serial | N=2 | N=4 | N=8 | Best vs serial |
| ------- | ---------------- | ------- | ------ | --- | --- | --- | -------------- |
| 3.14t, GIL off | before fix (`d661e225`) | local disk | 13.57 | 18.80 | 121.16 | 175.98 | 0.72× (collapse) |
| 3.14t, GIL off | before fix | 2 ms simulated read wait | 17.86 | 16.98 | 111.34 | 179.72 | 1.05× |
| 3.14, GIL | before fix | local disk | 13.28 | 14.95 | 15.62 | 17.31 | 0.89× |
| 3.14, GIL | before fix | 2 ms simulated read wait | 16.27 | 15.03 | 17.37 | 17.57 | 1.08× |
| 3.14t, GIL off | fix (`cedd97cf`, per-finding commits; artifact replaced) | local disk | 6.75 | 4.19 | 4.42 | 4.38 | 1.61× |
| 3.14t, GIL off | fix (`cedd97cf`) | 2 ms simulated read wait | 11.35 | 5.00 | 4.20 | 4.68 | 2.70× |
| 3.14, GIL | fix (`cedd97cf`) | local disk | 6.82 | 7.47 | 8.27 | 7.76 | 0.91× (threads slower) |
| 3.14, GIL | fix (`cedd97cf`) | 2 ms simulated read wait | 11.39 | 8.73 | 8.37 | 8.43 | 1.36× |
| 3.14t, GIL off | **fix + batched writes** (`3736feda`, pinned) | local disk | **4.70** | **4.21** | **3.90** | **3.53** | **1.33×** |
| 3.14t, GIL off | fix + batched writes | 2 ms simulated read wait | 9.27 | 6.09 | 4.64 | 3.94 | 2.35× |
| 3.14, GIL | fix + batched writes | local disk | **4.45** | 5.56 | 6.43 | 6.96 | 0.80× (threads slower) |
| 3.14, GIL | fix + batched writes | 2 ms simulated read wait | 8.81 | 6.52 | 6.81 | 7.64 | 1.35× |

Option (a) (lock around the ML step, bench harness only, before the fix) removed the collapse but gave no gain: 3.14t 13.61 / 12.73 / 13.23 / 13.98 s on local disk; 3.14 with GIL 13.30 / 13.68 / 13.69 / 14.52 s.

Reading the numbers without inflating them (operator decision on the ML fix approved on 2026-11-14):

- **Default unchanged:** with `scan.max_workers: 1` (the default) there is no pool; the only change a default scan sees is the detector fix.
- **(i) The detector fix alone roughly doubles the serial scan:** 3.14t 13.57 → 6.75 s (2.0×), 3.14 with the GIL 13.28 → 6.82 s (1.95×), N = 1, in every tier.
- **(ii) Pool on 3.14t (GIL off), with the fix, local disk:** pinned (`3736feda`, batched writes) 1.12× (N=2), 1.21× (N=4), 1.33× (N=8); with a 2 ms simulated wait 1.52× / 2.00× / 2.35×. Before the batched writes (`cedd97cf`): 1.61× (N=2), 1.53× (N=4), 1.54× (N=8) over the fixed serial scan. An earlier 3-iteration run under load average ~3 gave 1.54× / 1.58× / 1.17×; N=8 is the noisiest row. With a 2 ms simulated wait per read: 2.27–2.70×.
- **(iii) With the GIL the pool gains no CPU on local disk:** pinned (`3736feda`) 0.64–0.80×, getting worse with N; 2 ms simulated wait 1.15–1.35×. Before the batched writes: 0.83–0.91× (the earlier 3-iteration run: 0.62–0.85×). With the 2 ms simulated wait it only overlaps I/O: 1.31–1.36× (earlier run 1.05–1.29×). On the 1-vCPU VPS only real I/O overlap can show.
- **(iv) What limits the gain beyond N=2 on local disk:** the single writer. With detection stubbed out, the same scan costs 3.0 s serial and 3.3 s with 4 workers on 3.14t — walk, read and, mostly, one SQLite commit plus an `upsert_object_state` and an audit log line per finding, all on the target thread; the pool flattens at ≈ 4.2–4.4 s, near that floor. Why N=8 was worse than N=4 in the loaded 3-iteration run was not investigated beyond that. The per-file resume below batches those writes into one transaction per batch; re-measured at `3736feda` (pinned artifacts), the **serial** scan got faster (3.14t 6.75 → 4.70 s, 3.14 6.82 → 4.45 s), so the pool's relative gain shrank: the single writer is still the floor.

**Cause (profiled 2026-11-14, micro-benchmarks of 400–450 samples per row, 3.14t vs 3.14):** regex matching and TF-IDF vectorisation scale with threads; the ML step does not. `RandomForestClassifier.predict_proba` (called from `SensitivityDetector._predict_ml_confidence`) always runs through `joblib.Parallel` (here with `n_jobs=1`), and `joblib.Parallel` entered concurrently from several threads collapses on the free-threaded build: a bare `joblib.Parallel(n_jobs=1)` over 100 no-op items costs 0.05 s for 400 calls serially and 20.5 s with 4 threads on 3.14t (0.07 s → 0.06 s with the GIL). Limiting native thread pools (`OMP/OPENBLAS/MKL_NUM_THREADS=1`, `threadpoolctl.threadpool_limits(1)`) changes nothing. Accumulating the per-tree `predict_proba(X, check_input=False)` directly, in the same order and divided by the number of trees, gives **bit-identical** probabilities and runs 0.75 s → 0.27 s (4 threads) on 3.14t and 0.32 s serial with the GIL, against 1.4–1.55 s serial for the forest call. The same collapse affected multi-target scans on free-threaded runtimes before this fix.

**Options compared** (micro-benchmark of `scan_file_content`, 400 in-memory samples, seconds for N = 1 / 2 / 4 / 8 threads, output identical to the serial reference in every cell):

| Option | 3.14t (GIL off) | 3.14 (GIL) | Touches the detector |
| ------ | --------------- | ---------- | -------------------- |
| None (as shipped) | 1.51 / 2.30 / 19.7 / 32.9 | 1.60 / 1.59 / 2.23 / 2.23 | no |
| (a) lock around the ML step only | 1.55 / 1.57 / 1.65 / 1.89 | 1.48 / 1.70 / 2.08 / 1.82 | no (applied by a caller) |
| (b) forest probabilities without `joblib.Parallel` | 0.59 / 0.38 / 0.31 / 0.23 | 0.47 / 0.59 / 0.85 / 0.88 | yes |
| (b2) `joblib.parallel_config(backend="sequential")` | 1.72 / 2.76 / 19.1 / 32.8 | 1.44 / 2.16 / 2.40 / 2.47 | yes |
| (c) ML as a serial phase after the pool (estimate) | 1.58 / 1.54 / 1.66 / 1.75 | 1.60 / 1.98 / 1.80 / 1.78 | yes (splits `analyze`) |

(a) removes the collapse but cannot gain: ML is about 93 % of detection time and stays serial. (b) is the only option with a gain. (b2) keeps `Parallel` on the path. (c) costs what (a) costs and needs a larger detector change.

**Fix (b) — operator decision approved on 2026-11-14, applied in its own commit `ffdd4785` (`perf(detector)`, the only change to `core/detector.py` in #1820; revert that commit alone to restore the old path).** `SensitivityDetector._predict_ml_confidence` now calls the module helper `_forest_predict_proba(self._model, X)` instead of `self._model.predict_proba(X)`:

```python
def _forest_predict_proba(model, X):
    from sklearn.ensemble import RandomForestClassifier
    import numpy as np

    estimators = getattr(model, "estimators_", None)
    validate = getattr(model, "_validate_X_predict", None)
    if (
        not isinstance(model, RandomForestClassifier)
        or not estimators
        or validate is None
        or getattr(model, "n_outputs_", 1) != 1
    ):
        return model.predict_proba(X)  # unchanged path
    Xv = validate(X)
    acc = np.zeros((Xv.shape[0], int(model.n_classes_)), dtype=np.float64)
    for est in estimators:  # same order and float64 sum as sklearn's accumulator
        acc += est.predict_proba(Xv, check_input=False)
    acc /= len(estimators)
    return acc
```

Bit-identical to `predict_proba` (`np.array_equal`). Risk: `_validate_X_predict` is private sklearn API; mitigated by the fallback to `predict_proba` for anything that is not a single-output `RandomForestClassifier` with the expected attributes, and by `tests/test_detector_forest_predict_1820.py` (red first in `d661e225`): bit-identical probabilities, unchanged `ml_confidence` with `joblib.Parallel` forbidden, single-class model, no model, non-forest fallback, 8 threads.

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
| Behaviour change on Community/open with `max_workers ≥ 2` | Accepted; see *Tier decision*. |

## Tier decision (closed)

Decided 2026-11-14 (project-manager, under the operator's rule "ceiling from the existing tier cap, no new cap"): the pool follows the existing worker cap for every tier. Community/open with `scan.max_workers: 2` gets up to 2 threads inside a single target (with the GIL they only overlap I/O); the default `max_workers: 1` changes nothing. No tier check is added to the budget.

## Out of scope (this plan)

- **Parallel walk / one work item per top-level folder.** Walk is 0.08 % of the local profile, below the 15 % gate of `filesystem_phase_breakdown_v1`; a parallel walk makes the reported path of a hard link or duplicate symlink a race and breaks exact parity. `InodeDedup` and `iter_scan_files(dedup=...)` are ready for it; revisit with an SSHFS/NFS measurement where `scandir` latency dominates.
- SMB, WebDAV, SharePoint connectors (separate code paths).
- Per-file isolation of unexpected exceptions: an unexpected error while processing one file keeps aborting the target at the same ordered position as the serial path (decided 2026-11-14). Read failures were already isolated by `_read_text_sample`.
- Adaptive throttling inside the target (`BoarThrottler` stays per target).
- Any native extension.

## Resume per file (implemented 2026-11-14, extends #1330)

**Before** (survey on the pool branch, 6 000 synthetic `.csv`, one filesystem target, serial): `--resume` re-scanned the whole filesystem target. Nothing was lost, but every finding saved before the kill was duplicated in the same session — SIGTERM at 8 s: 346 rows before, 6 346 after resume (6 000 distinct); SIGKILL at 8 s: 341 → 6 341. `scan_object_state` could not serve as the base: it is cross-session and written only for files with a finding.

**Design (as implemented):**

- New table `scan_file_checkpoints(session_id, target_name, abs_path, mtime_ns, size)` with `_ensure_scan_file_checkpoints_table` (legacy DBs gain it on open; test included).
- The target thread queues each finished candidate file's recorded writes (findings, failures, read barriers, object-state upsert) together with its checkpoint, and `LocalDBManager.persist_file_batch` commits a batch in **one transaction** (every 256 files or 1 s, and on interrupt). A file's findings and its checkpoint become durable together, so a hard kill loses the whole unflushed batch — findings and checkpoints — and `--resume` re-scans those files **without duplicating**. Batching also cuts the per-finding commits of the single writer.
- On resume the walk skips files whose `(abs_path, mtime_ns, size)` matches the session checkpoint. A file changed since its checkpoint is re-scanned and its earlier findings in the session (including archive / SQLite-as-DB members) are replaced; the file-name match is literal (LIKE wildcards escaped).
- Serial and pool paths share it. A DB manager without these methods (test doubles) keeps immediate per-call writes and no checkpoints. `--resume` on a fresh run is a no-op lookup.

**Evidence after the change** (same corpus and procedure, `python main.py --config … --resume <session>`):

| Kill | Session after kill | Rows before resume | After `--resume` | Distinct files | Uninterrupted run |
| ---- | ------------------ | ------------------ | ---------------- | -------------- | ----------------- |
| SIGTERM at 8 s | `interrupted` | 390 | **6 000** (`completed`) | 6 000 | 6 000 |
| SIGKILL at 8 s | `running` | 384 | **6 000** (`completed`) | 6 000 | 6 000 |

No duplicate and no loss. `tests/test_filesystem_file_resume.py` checks the same with stub detection on serial and pool runs: identical multiset of findings and failures against an uninterrupted run, skip of checkpointed files, lost last batch (simulated kill -9), changed file, fresh-session checkpoint count, legacy DB, literal file-name match.

**Limits:**
- A file interrupted by an **unexpected exception** (the target aborts with `error`, same as before) keeps its partial writes without a checkpoint; resuming re-scans it and can duplicate that one file's partial findings.
- Failures (`scan_failures`) of a file that **changed** between the runs are not replaced, only its findings.
- The checkpoint key is path + mtime + size, not a content hash: a rewrite that keeps both mtime and size is treated as unchanged.
- Live finding counts during a scan lag by up to one batch (≤ 1 s).

## Phases

| Phase | Status |
| ----- | ------ |
| Plan + red tests | ✅ |
| Pool + budget + atomic dedup | ✅ |
| Detector ML fix (operator-approved) | ✅ |
| Pinned benchmark (3.14t vs 3.14 GIL, dev workstation) | ✅ |
| Resume survey | ✅ |
| Demo image + VPS measurement (operator / PM) | ⬜ |
| Resume per file | ✅ |
| Parallel walk (top-level folders) | ⬜ roadmap, needs network-FS measurement |
