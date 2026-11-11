# Benchmark artifacts (`tests/benchmarks/`)

Pinned JSON files back performance narratives in docs and `docs/CLAIMS.yml`.
Regenerate only with intent — commit artifact and prose together.

| Benchmark id | Runner | What it measures | What it does **not** measure |
| ------------ | ------ | ---------------- | ---------------------------- |
| `official_pro_v1` | `run_official_bench.py` | OpenCore Python vs Pro+ `ProcessPoolExecutor` + `process_chunk_worker` on 200k seeded rows; **speed + safe gate** (`benchmark_gate.py`) | Rust `filter_batch` hotspot; end-to-end scan |
| `rust_prefilter_hotspot_v1` | `run_rust_prefilter_hotspot_bench.py` | `OpenCorePreFilter.filter_candidates` vs `FastFilter.filter_batch` on the same batch | Worker pool, ML/DL, connectors, Maestro gate (#1021) |
| `rust_per_call_cost_v1` | `run_rust_per_call_cost_bench.py` | Per-call PyO3 loop vs single `filter_batch`; short/long corpora; `RegexStageEngine.match_names` | End-to-end scan I/O (see `rust_tier_scan_io_v1`) |
| `rust_tier_scan_io_v1` | `run_rust_tier_scan_io_bench.py` | ``AuditEngine`` filesystem scan at each tier ``worker_cap`` (enforced JWT bench) | SMB/NFS, ML/DL, full product multi-target |
| `filesystem_phase_breakdown_v1` | `run_filesystem_phase_breakdown_bench.py` | Walk/glob vs read sample vs detect on synthetic `.txt` tree (local disk) | SMB/NFS, PDF extraction, parallel walk decisions (#1080) |

## Regenerate `rust_prefilter_hotspot_v1`

```bash
uv sync
uv run maturin develop --release --manifest-path rust/boar_fast_filter/Cargo.toml
uv run python tests/benchmarks/run_rust_prefilter_hotspot_bench.py \
  --rows 200000 --warmup 2 --iterations 5 \
  --output tests/benchmarks/rust_prefilter_hotspot.json
uv run pytest tests/test_rust_prefilter_hotspot_evidence.py -v
```

Requires `boar_fast_filter` in the active venv (`importorskip` in the evidence test).

## Regenerate `rust_per_call_cost_v1` (#2182)

```bash
uv sync
uv run maturin develop --release --manifest-path rust/boar_fast_filter/Cargo.toml
uv run python tests/benchmarks/run_rust_per_call_cost_bench.py \
  --rows 20000 --warmup 1 --iterations 5 \
  --output tests/benchmarks/rust_per_call_cost.json
uv run pytest tests/test_rust_per_call_cost_evidence.py -v
```

Sync `RUST_REGEX_STAGE_MIN_TEXT_CHARS` in `core/rust_regex_stage.py` with
`activation.activation_min_text_chars` from the artifact before commit.

## Regenerate `rust_tier_scan_io_v1` (#2182)

```bash
uv sync
uv run maturin develop --release --manifest-path rust/boar_fast_filter/Cargo.toml
uv run python tests/benchmarks/run_rust_tier_scan_io_bench.py \
  --files 350 --workers 16 --iterations 1 \
  --output tests/benchmarks/rust_tier_scan_io.json
uv run pytest tests/test_rust_tier_scan_io_evidence.py -v
```

Uses ephemeral test JWTs (same helpers as ``tests/test_worker_cap.py``); no network.

## Regenerate `official_pro_v1`

```bash
uv run python tests/benchmarks/run_official_bench.py \
  --rows 200000 --workers 8 \
  --output tests/benchmarks/official_benchmark_200k.json
uv run pytest tests/test_official_benchmark_200k_evidence.py -v
```

The 200k artifact records Pro **slower** than OpenCore in that composite profile (~0.574×).
Do **not** use it for the Rust prefilter ~11–13× headline — use `rust_prefilter_hotspot_v1`.

**Safe axis (#1338):** `benchmark_gate.py` blocks when `opencore_hits != pro_hits` or
`speedup_vs_opencore < 0.574`. Reference manifest:
`tests/benchmarks/reference_manifests/official_pro_v1_200k.json`. Plan:
`docs/plans/PLAN_BENCHMARK_SAFE_AXIS.md`.

## Regenerate `filesystem_phase_breakdown_v1`

```bash
uv run python tests/benchmarks/run_filesystem_phase_breakdown_bench.py \
  --files 2000 --iterations 3 \
  --output tests/benchmarks/filesystem_phase_breakdown.json
```

Use results to gate parallel filesystem walk (#1080) and to complement `rust_prefilter_hotspot_v1` for #1078 (local txt profile only).
