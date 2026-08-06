# ADR 0078 — Multi-pattern regex acceleration gated by benchmark (RegexSet before Vectorscan)

- **Date (UTC):** 2026-06-30
- **Authors:** Fabio Leitao
- **Deciders:** Fabio Leitao

## Status

Proposed

### Status history

- 2026-06-30 — Proposed (research closure GitHub #1078)
- 2026-07-31 — **Amended:** RegexSet spike on ~284 real patterns **failed** the performance gate (5.7× slower than a loop of cached `Regex`; default `size_limit` 10 MiB did not compile — needed ≥20 MiB). Next engineering step is **cached individual `Regex` + Python translator** per [PLAN_RUST_REGEX_STAGE.md](../plans/PLAN_RUST_REGEX_STAGE.md) / [#1414](https://github.com/DataBoar/data-boar/issues/1414) — not RegexSet as default. Vectorscan gate unchanged in spirit (see Decision).
- 2026-08-06 — **#1415 withdrawn:** a proposed Context amend that called the batch-hot-path premise “false” (citing [#1411](https://github.com/DataBoar/data-boar/issues/1411)) is **RETIRADO** — that claim was born from a false #1411 narrative; Context below is restored to the pre-#1415 text. Status remains **Proposed**.

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

Matching **is** the hotspot for text-heavy local profiles, but **Rust prefilter already addresses the batch hot path**. The original recommendation preferred a **`RegexSet` spike** before Vectorscan FFI.

**RegexSet spike (2026-07-31, probe outside repo — bus #1413):** On the **detector-stage** workload (~284 patterns, identical hit counts 119182), a loop of compiled `Regex` took **0.686 s** vs `RegexSet::matches` **3.907 s** (**5.7× slower** for Set). Cause: `matches()` evaluates **all** patterns — no early exit. Set also failed to compile under the crate default **10 MiB** `size_limit` (needed ≥20 MiB). Therefore RegexSet is **not** the next shipping path for the open-domain YAML regex stage.

## Decision

1. **No Vectorscan / Hyperscan dependency** on `main` until:
   - the **chosen** multi-pattern acceleration path (now: **cached individual `Regex` loop** + Python pattern translator for `re`↔crate parity — see PLAN_RUST_REGEX_STAGE / #1414) fails to meet targets on a feature branch; **and**
   - benchmark on a **representative mixed corpus** (PDF + text + connector path) still shows matching ≥ **10–15%** of end-to-end time.
2. **Next engineering step:** implement the detector regex stage with **`Vec<Regex>` cached per detector instance** and a **Python-side translator** (port `translate.py` from the 2026-07-31 probe) — **not** Vectorscan, and **not** `RegexSet` as the default engine for that stage. RegexSet remains available in the dependency tree for other experiments; it is **rejected** for this call site based on the spike above.
3. If Vectorscan is ever adopted: **Enterprise-tier optional**, **graceful degrade** to current path on no-AVX hosts — never hard dependency of open-core.
4. Pin benchmark artifacts under `tests/benchmarks/` when re-run; do not cite ADR-0007 for perf (synthetic corpus ADR — RO correction #1078). Cite detector-stage numbers with declared scope (isolated matching ≠ prefilter 3-pattern hotspot).

## Consequences

- **Positive:** Avoids premature FFI/build blast radius; keeps min-spec story intact; avoids shipping a multi-pattern path measured **slower** than a simple Regex loop.
- **Negative:** Pattern count growth still pressures detector until the cached-Regex + translator path ships (#1414).
- **Watch:** Re-run `filesystem_phase_breakdown` on SMB/NFS lab host before enabling parallel walk (#1080). Re-evaluate RegexSet only if a future API gains early-exit semantics that change the 5.7× result.

## References

- GitHub **#1078**, **#1080** (perf front); **#1413** (bus), **#1414** (mother — Rust regex stage)
- [PLAN_RUST_REGEX_STAGE.md](../plans/PLAN_RUST_REGEX_STAGE.md)
- `tests/benchmarks/README.md`, `run_rust_prefilter_hotspot_bench.py`, `run_filesystem_phase_breakdown_bench.py`
- Local probe (not tracked): `~/data-boar-drafts/regex-parity-probe-2026-07-31/` (`regex_stage_parity_bench.json`)
