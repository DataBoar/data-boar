# Plan: Benchmark safe axis (recall gate)

**Status:** Active
**Date:** 2026-07-27
**Authors:** Fabio Leitao
**Priority:** H1 / U1
**GitHub:** [#1338](https://github.com/DataBoar/data-boar/issues/1338) (blocks [#1337](https://github.com/DataBoar/data-boar/issues/1337) sampling dedup — safe axis must exist first)

<!-- plans-hub-summary: Add a blocking safe (recall) axis to the existing benchmark gate beside wall-clock speed — exact finding-count parity on synthetic reference corpora; optimization that drops detections fails even when faster (#1338). -->
<!-- plans-hub-related: BENCHMARK_EVOLUTION.md, PLAN_MAESTRO_BENCHMARK_METRICS_AND_FIX.md, PLAN_SYNTHETIC_DATA_AND_CONFIDENCE_VALIDATION.md -->

**Synced with:** [PLANS_TODO.md](PLANS_TODO.md)

## Motivation

The performance gate today measures **one axis only: speed** (NASA Safe-Hold at **0.574×** OpenCore/Pro ratio in `pro/engine.py` and `pro/worker_logic.py`). There is **no axis that reproves recall loss**. For a compliance scanner, **false negatives are worse than slowness**.

Precedent already measured by hand: **v1.7.3 → v1.7.4-rc** on the synthetic LGPD filesystem corpus = **10816ms → 10330ms** with **26 findings on both sides**. That **26 = 26** check is the safe axis in disguise — this plan makes it **explicit, machine-readable, and blocking**.

Inspiration: [ponytail](https://github.com/DietrichGebert/ponytail) benchmark table column **`safe`** — optimizations that eat validation fail even when LOC/tokens/time improve.

## Reference corpora (public, synthetic only — #1288)

| Corpus ID | Harness | Fixture | Expected recall | Tolerance |
| --------- | ------- | ------- | --------------- | --------- |
| `synthetic_seed_200k` | `tests/benchmarks/run_official_bench.py` | Deterministic `generate_test_data()` seed (CPF/card/email mix) | **100 000** hits OpenCore **and** Pro at 200k rows | **Exact** — `opencore_hits == pro_hits == expected` |
| `synthetic_lgpd_10file` | `tests/config/benchmark-rc.yaml` → `tests/data/` | Synthetic homelab/LGPD scan tree (no customer exports) | **26** findings per A/B round (lab operator precedent) | **Exact** — legacy == candidate == 26 |

**Never** promote customer or field exports into tracked fixtures. Real engagement numbers stay in private lab notes only.

### Why exact tolerance (no band)

1. **Deterministic seeds** — `official_pro_v1` uses a fixed repeating pattern; there is no sampling RNG in the harness path.
2. **Compliance posture** — a “±1 finding” band would allow silent PII drops; the product promise is evidence-oriented detection, not approximate recall.
3. **Precedent** — the recorded A/B already used **equality** (26=26, 100k=100k), not a confidence interval.

If a future corpus introduces intentional stochastic sampling (#1337), the safe axis still applies **before** dedup changes ship: candidate must match baseline on the **same** corpus draw.

## Gate axes (no cross-axis compensation)

| Axis | Rule | Blocking? |
| ---- | ---- | --------- |
| **speed** | `speedup_vs_opencore >= 0.574` (Safe-Hold floor) | Yes |
| **safe** | `opencore_hits == pro_hits` (+ manifest expected when pinned) | Yes |

A change that is **30% faster** but **drops one hit** → **FAIL** (`safe_axis`).

## Implementation map (existing harness — no new runner)

| Location | Role |
| -------- | ---- |
| `tests/benchmarks/benchmark_gate.py` | Shared evaluation + CLI |
| `tests/benchmarks/run_official_bench.py` | Runs benchmark, prints **time + recall**, embeds `gate` block, `--enforce-gate` exit code |
| `tests/benchmarks/reference_manifests/*.json` | Pinned expected recall per corpus |
| `tests/test_benchmark_safe_axis_gate.py` | Regression: mutation faster + −1 hit → reprove |
| `tests/test_official_benchmark_200k_evidence.py` | Existing pinned JSON guard (complementary) |
| `scripts/benchmark-ab.ps1` / `scripts/run-benchmark.ps1` | Lab wall-clock wrappers — operator adds finding counts to private notes; `evaluate_ab_recall_parity()` documents 26=26 check |

## Phases

| # | Phase | Status |
| - | ----- | ------ |
| 1 | PLAN + hub sync + PLANS_TODO row | ✅ Done |
| 2 | `benchmark_gate.py` + manifest + `run_official_bench.py` gate block | ✅ Done |
| 3 | Pytest gate proofs (`test_benchmark_safe_axis_gate.py`) | ✅ Done |
| 4 | #1337 sampling dedup — only after #1338 merged | ✅ Done ([#1337](https://github.com/DataBoar/data-boar/issues/1337)) |

## Acceptance (#1338)

- [x] `docs/plans/PLAN_BENCHMARK_SAFE_AXIS.md` with `plans-hub-summary`
- [x] `python scripts/plans_hub_sync.py --write`
- [x] Entry in `docs/plans/PLANS_TODO.md`
- [x] Corpus + tolerance documented (exact, synthetic-only)
- [x] Blocking check in `run_official_bench.py` harness
- [x] Report shows time **and** recall together
- [x] Test: faster mutation losing one hit → gate **FAIL**

## Operator commands

```bash
# Regenerate artifact + gate (CI-scale rows optional for local dev)
uv run python tests/benchmarks/run_official_bench.py \
  --rows 200000 --workers 8 \
  --output tests/benchmarks/official_benchmark_200k.json

uv run pytest tests/test_benchmark_safe_axis_gate.py tests/test_official_benchmark_200k_evidence.py -v

# Evaluate an existing JSON artifact
uv run python tests/benchmarks/benchmark_gate.py tests/benchmarks/official_benchmark_200k.json
```
