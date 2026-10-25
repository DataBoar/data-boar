# LAB Lessons Learned — session snapshot 2026-04-25

**Archive note:** Immutable snapshot for the UTC−3 session described in the hub
[`../LAB_LESSONS_LEARNED.md`](../LAB_LESSONS_LEARNED.md). Do not rewrite this file;
add newer sessions as new dated files under this directory.

Date: 2026-04-25 (UTC-3 session)

## Scope Executed

- Rust extension accessibility check (`boar_fast_filter` import in project `.venv`).
- Official benchmark run (`tests/benchmarks/run_official_bench.py`).
- Kill-and-resume checkpoint validation using `ProOrchestrator` + `BoarStateTracker`.
- Throttler behavior observation during scan.

## 1) Performance (OpenCore vs Pro+)

Source: `tests/benchmarks/official_benchmark_200k.json`

- Rows: `200,000`
- Workers: `8`
- OpenCore time: `0.252242s`
- Pro+ time: `0.439419s`
- Performance gain: `0.574x` (Pro+ slower in this benchmark profile)
- Findings parity: `100,000` hits in both paths

QA note:

- This benchmark shape is pre-filter dominated and includes multiprocessing overhead.
- Result is valid but not yet a "Pro+ speedup" business-case profile.
- Next tuning target: larger payload/chunk calibration + heavier downstream scan stage.

## 2) Checkpoint Efficacy (Kill Test)

Scenario:

- Dataset: `data/qa_completao_300k.db` (`300,000` rows).
- Checkpoint file: `data/qa_completao_state.json`.
- Process force-killed mid-run.

Observed state after kill:

- `last_processed_id`: `104000`
- `status`: `IN_PROGRESS`

Resume run outcome:

- Final state: `last_processed_id=300000`, `status=COMPLETED`.
- Resume findings count: `147000`.
- Consistency check: remaining rows = `300000 - 104000 = 196000`; with 3/4 flagged pattern => `147000` expected.
- Conclusion: resume continued from the saved offset without evidence of reset-to-zero.

## 3) Throttling Behavior

Observed during resumed scan:

- `BoarThrottler.current_workers` reached `8` (configured max).
- Starting baseline is `1`; reaching `8` confirms adaptive concurrency adjustments occurred while scan progressed.

SRE conclusion:

- Throttler path is active in runtime and reacts by increasing concurrency in stable latency conditions.

## Final QA/SRE Verdict (this cycle)

- Rust bridge: **OK** (built and importable in `.venv`).
- Checkpoint + resume after forced termination: **OK**.
- Throttler adjustment during scan: **OK**.
- Official benchmark business-case speedup: **NOT MET YET** in current profile (`0.574x`).

Recommended next step:

- Run benchmark with production-like workload (larger chunks + heavier post-filter stage) before claiming Pro+ performance uplift in executive material.

## Related governance notes

- Verified vs aspirational metrics: [docs/ops/SPRINT_GREAT_LEAP_POSTMORTEM.md](../SPRINT_GREAT_LEAP_POSTMORTEM.md) ([pt-BR](../SPRINT_GREAT_LEAP_POSTMORTEM.pt_BR.md)).
- Integrity defense design spec: [docs/ops/INTEGRITY_CHECK_ALPHA_LOGIC.md](../INTEGRITY_CHECK_ALPHA_LOGIC.md) ([pt-BR](../INTEGRITY_CHECK_ALPHA_LOGIC.pt_BR.md)).
