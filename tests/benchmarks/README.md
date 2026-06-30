# Benchmark artifacts (`tests/benchmarks/`)

Pinned JSON files back performance narratives in docs and `docs/CLAIMS.yml`.
Regenerate only with intent — commit artifact and prose together.

| Benchmark id | Runner | What it measures | What it does **not** measure |
| ------------ | ------ | ---------------- | ---------------------------- |
| `official_pro_v1` | `run_official_bench.py` | OpenCore Python vs Pro+ `ProcessPoolExecutor` + `process_chunk_worker` on 200k seeded rows | Rust `filter_batch` hotspot; end-to-end scan |
| `rust_prefilter_hotspot_v1` | `run_rust_prefilter_hotspot_bench.py` | `OpenCorePreFilter.filter_candidates` vs `FastFilter.filter_batch` on the same batch | Worker pool, ML/DL, connectors, Maestro gate (#1021) |
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

## Regenerate `official_pro_v1`

```bash
uv run python tests/benchmarks/run_official_bench.py \
  --rows 200000 --workers 8 \
  --output tests/benchmarks/official_benchmark_200k.json
uv run pytest tests/test_official_benchmark_200k_evidence.py -v
```

The 200k artifact records Pro **slower** than OpenCore in that composite profile (~0.574×).
Do **not** use it for the Rust prefilter ~11–13× headline — use `rust_prefilter_hotspot_v1`.

## Regenerate `filesystem_phase_breakdown_v1`

```bash
uv run python tests/benchmarks/run_filesystem_phase_breakdown_bench.py \
  --files 2000 --iterations 3 \
  --output tests/benchmarks/filesystem_phase_breakdown.json
```

Use results to gate parallel filesystem walk (#1080) and to complement `rust_prefilter_hotspot_v1` for #1078 (local txt profile only).
