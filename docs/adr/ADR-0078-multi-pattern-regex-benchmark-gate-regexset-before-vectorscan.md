# ADR 0078 — Multi-pattern regex acceleration gated by benchmark (RegexSet before Vectorscan)

- **Date (UTC):** 2026-06-30
- **Authors:** Fabio Leitao
- **Deciders:** Fabio Leitao

## Status

Proposed

### Status history

- 2026-06-30 — Proposed (research closure GitHub #1078)

## Context

Off-band research (#1078) proposed **Vectorscan** (Hyperscan fork) for SIMD multi-pattern matching as `norm_tag` patterns grow (#1056, #1074/#1075). RO verification noted:

- `boar_fast_filter` uses **one Rust regex per call**; Python `re` in `core/detector.py` is not multi-pattern single-pass.
- **Vectorscan** adds C/FFI build complexity and **AVX2-biased** gains — tension with **no-AVX min-spec** lab hosts (#821).
- Crate **`regex::RegexSet`** (already in the dependency tree) offers portable multi-pattern matching **before** any external engine.

**Benchmark gate (2026-06-30, primary Linux):**

| Artifact | Finding |
| --- | --- |
| `rust_prefilter_hotspot_v1` | Rust `filter_batch` ~**4.7×** vs Python prefilter on 200k rows (pinned JSON refreshed) |
| `filesystem_phase_breakdown_v1` | On 2k local `.txt` files: **~99.7%** wall time in detect/matching vs **~0.1%** walk — walk parallelization **not** justified on this profile (#1080 🟡) |

Matching **is** the hotspot for text-heavy local profiles, but **Rust prefilter already addresses the batch hot path**. Further wins should prefer **`RegexSet` in `boar_fast_filter`** (no new dep) before Vectorscan FFI.

## Decision

1. **No Vectorscan / Hyperscan dependency** on `main` until:
   - `RegexSet` prototype on a **feature branch** fails to meet targets; **and**
   - benchmark on a **representative mixed corpus** (PDF + text + connector path) still shows matching ≥ **10–15%** of end-to-end time.
2. **Next engineering step (when scheduled):** spike `RegexSet` in `rust/boar_fast_filter` with parity tests — **not** Vectorscan.
3. If Vectorscan is ever adopted: **Enterprise-tier optional**, **graceful degrade** to current path on no-AVX hosts — never hard dependency of open-core.
4. Pin benchmark artifacts under `tests/benchmarks/` when re-run; do not cite ADR-0007 for perf (synthetic corpus ADR — RO correction #1078).

## Consequences

- **Positive:** Avoids premature FFI/build blast radius; keeps min-spec story intact.
- **Negative:** Pattern count growth may still pressure detector until RegexSet ships.
- **Watch:** Re-run `filesystem_phase_breakdown` on SMB/NFS lab host before enabling parallel walk (#1080).

## References

- GitHub **#1078**, **#1080** (perf front)
- `tests/benchmarks/README.md`, `run_rust_prefilter_hotspot_bench.py`, `run_filesystem_phase_breakdown_bench.py`
