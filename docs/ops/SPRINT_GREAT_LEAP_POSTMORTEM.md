# Sprint post-mortem: Pro+ discovery, Rust pre-filter, SRE throttling

**Português (Brasil):** [SPRINT_GREAT_LEAP_POSTMORTEM.pt_BR.md](SPRINT_GREAT_LEAP_POSTMORTEM.pt_BR.md)

This note separates **verified evidence** from **aspirational lab targets**. Only verified rows should appear in customer-facing material.

## Verified in this repository session (evidence-backed)

Source of truth: [LAB_LESSONS_LEARNED.md](LAB_LESSONS_LEARNED.md) (hub; dated snapshot: [lab_lessons_learned/LAB_LESSONS_LEARNED_2026_04_25.md](lab_lessons_learned/LAB_LESSONS_LEARNED_2026_04_25.md)), `tests/benchmarks/official_benchmark_200k.json`, checkpoint file from kill test.

| Topic | Result |
| ----- | ------ |
| Rust extension `boar_fast_filter` | Built and importable in project `.venv` (PyO3 updated for CPython 3.13). |
| Official benchmark (200k rows, 8 workers) | OpenCore `0.252242s`, Pro path `0.439419s`, `speedup_vs_opencore = 0.574` (Pro is **0.574x as fast as** OpenCore in this profile, i.e. ~`1.74x` more wall-clock — Pro **slower**). |
| Checkpoint + kill resume | `last_processed_id` advanced from `104000` to table end; second run completed with consistent finding counts. |
| Throttling | `BoarThrottler` increased concurrency toward configured max during scan. |

## Not verified here (do not claim without a reproducible lab run)

The numbers below are **examples of what a future lab-op campaign might target**. They are **not** recorded as measured outcomes in this repo session.

| Claim | Status |
| ----- | ------ |
| 1,000,000 mock rows end-to-end | Not executed in this documentation pass. |
| OpenCore ~420s vs Pro+ ~28s (~15x) | Not measured; contradicts current official benchmark artifact. |
| “100% false positive reduction” on random numeric sequences | Not measured as a controlled study; Luhn reduces obvious non-Luhn card shapes only. |
| Full `completao` orchestrator green on lab-op | Not completed end-to-end in this assistant session. |

## Technical conclusions (honest)

- **Checkpointing and throttling** are the strongest “mission critical” wins captured here.
- **Performance marketing** needs a benchmark profile aligned with real workloads (chunk size, downstream ML cost, I/O realism) before quoting speedups.
- **Direction vs ratio (do not double-invert).** `speedup_vs_opencore = 0.574` and the operator phrasing **"0.574x mais lento"** point to the **same** outcome (Pro slower); the JSON ratio is `OpenCore / Pro` time. Pro takes roughly **`1 / 0.574 ≈ 1.74x`** the OpenCore wall-clock in this profile. The regression guard [`tests/test_official_benchmark_200k_evidence.py`](../../tests/test_official_benchmark_200k_evidence.py) pins this direction plus the OpenCore ↔ Pro findings parity (`100,000` hits on both paths) so future executive copy or manifests cannot drift from the recorded artifact silently.

## Next verification steps

1. Re-run `tests/benchmarks/run_official_bench.py` at scale after tuning chunking and worker count; archive JSON under `tests/benchmarks/`.
2. Run full lab-op `completao` and attach logs under private homelab reports per runbook.
3. If integrity auto-defense is required in product, implement per `INTEGRITY_CHECK_ALPHA_LOGIC.md` with an ADR.
