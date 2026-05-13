# LAB Lessons Learned — 2026-05-13 (A/B benchmark + compressed scan + config key fix)

**Session date:** 2026-05-13 (UTC-3)
**Session type:** Benchmark A/B (v1.7.3 vs v1.7.4-rc) + full corpus scan + config bug discovery
**Host:** latitude (primary engine host; mini-bt and t14 online but not exercised in this session)

## Verdict (short)

First confirmed end-to-end A/B benchmark run on a real PII corpus. Bug in `benchmark-rc.yaml`
(`scan_scope` key) was the root cause of all prior silent "No findings" benchmark runs.
`boar_fast_filter` compiled and validated on latitude for the first time. `v1.7.4-rc` is
faster and produces identical findings to `v1.7.3`. Minor detection and compressed archive
scanning confirmed working. Two new commercial use cases documented.

## Session timeline

1. **Bug 3 (collect race) fixed** — `maestro-benchmark-ab.ps1` gained `-SleepBeforeCollect 120`
   parameter to prevent async tmux smoke running past the `-Collect` SCP phase. Regression
   test added to `tests/test_maestro_scripts.py`.
2. **`boar_fast_filter` compiled on latitude** — Rust extension was missing from the lab host
   venv. Built via `maturin develop --release` (Rust 1.95 + maturin 1.13.3, 27s compile time).
   Confirmed: `boar_fast_filter OK` via `uv run python3`.
3. **Silent "No findings" root cause found** — `tests/config/benchmark-rc.yaml` used `scan_scope:`
   as the config key; the canonical key is `targets:`. The product either silently ignores
   `scan_scope` or normalizes it differently. Every prior Deep benchmark run was scanning
   nothing. Fixed in commit `04d1896`.
4. **A/B benchmark results (real PII corpus, LGPD documents)**:
   - corpus: `/home/leitao/Documents/LGPD/` (10 files: xlsx, pdf, docx, csv, txt)
   - v1.7.3 (`rust_fast_filter: false`): **10816ms**, 26 findings
   - v1.7.4-rc (`rust_fast_filter: true`): **10330ms**, 26 findings
   - **Ratio: 0.955x** — rc is 4.5% faster on this small corpus
   - Finding parity: identical — **no regression** ✅
5. **Compressed archive scan** — `scan_compressed: true` with `.zip` and `.tgz`:
   - `sample1.zip` → HIGH | LGPD_CPF, PHONE_BR, DATE_DMY + **DOB_POSSIBLE_MINOR** ✅
   - `sample3.tgz` → HIGH | LGPD_CPF, PHONE_BR, DATE_DMY + **DOB_POSSIBLE_MINOR** ✅
   - `sample4.tar.bz2` → HIGH | ML_DETECTED ✅
   - `sample2.7z` → **FAIL** — `py7zr` not installed (`archive_unsupported` error)
6. **Two new commercial use cases documented** — `PLAN_FORENSIC_SEARCH_AND_GEOGRAPHIC_HINTS.md`:
   - Breach forensics: targeted identifier search across all data sources via `regex_overrides`
   - Intra-Brazil geographic breadcrumbs: DDD codes, CEP ranges, CNPJ state, PEP terminology

## Key measurements

| Metric | Value | Notes |
| ------ | ----- | ----- |
| `core.engine` import time (v1.7.3) | **2457ms** | First-call timing, warm venv |
| `boar_fast_filter` find_spec time (v1.7.4-rc) | **82ms** | 30× faster import |
| Full scan v1.7.3 (LGPD corpus, 10 files) | **10816ms** | `rust_fast_filter: false` |
| Full scan v1.7.4-rc (LGPD corpus, 10 files) | **10330ms** | `rust_fast_filter: true` |
| A/B ratio (small corpus) | **0.955x** | Larger corpus needed for 0.574x claim |
| Compressed scan (zip+tgz) | 15+ findings | Minor detection confirmed inside archives |
| `.7z` support | **MISSING** | Requires `py7zr` optional dep |

## Bugs found and fixed this session

| Bug | File(s) | Fix | Commit |
| --- | ------- | --- | ------ |
| Bug 3: collect race (async tmux vs -Collect SCP) | `maestro-benchmark-ab.ps1` | `-SleepBeforeCollect 120` parameter | `1c5e735` |
| `scan_scope` → `targets` in benchmark config | `tests/config/benchmark-rc.yaml` | Changed key to `targets:` | `04d1896` |

## Bugs confirmed fixed in prior commits (pre-session)

| Bug | Status |
| --- | ------ |
| Bug 1: SSH calls without ConnectTimeout | ✅ Already fixed in `65359ad` |
| Bug 2: configArg passed as positional arg to smoke script | ✅ Already fixed in `65359ad` |

## Open gaps identified

| Gap | Severity | Action |
| --- | -------- | ------ |
| `py7zr` missing for `.7z` support | Medium | Add to `[compressed]` optional dep in `pyproject.toml` |
| `boar_fast_filter` not in lab venv (needs manual `maturin develop`) | Medium | Document in HOMELAB_VALIDATION; add to completão preflight check |
| 0.574x ratio not reproduced — needs larger corpus | Low | Scale test with `tests/data/bench/synthetic_valid_cpf_3k.txt` (3000 lines, 1MB); current corpus too small |
| Cross-host scans (mini-bt/t14 → latitude via sshfs/nfs/cifs) | Low | Next completão session; not urgent |
| `scan_scope` key silently ignored vs `targets` — no warning emitted | Medium | Should emit a WARNING: "scan_scope is not a recognized key; did you mean targets?" |

## Evidence paths (repo)

- `tests/config/benchmark-rc.yaml` — fixed config (commit `04d1896`)
- `scripts/maestro-benchmark-ab.ps1` — added `-SleepBeforeCollect` (commit `1c5e735`)
- `tests/test_maestro_scripts.py` — added `test_maestro_benchmark_ab_has_sleep_before_collect`
- `tests/data/bench/synthetic_valid_cpf_3k.txt` — valid CPF corpus (on latitude, 1MB)
- `docs/plans/PLAN_MAESTRO_BENCHMARK_METRICS_AND_FIX.md` — open action items
- `docs/plans/PLAN_FORENSIC_SEARCH_AND_GEOGRAPHIC_HINTS.md` — new use case plan
- Private logs: `docs/private/homelab/reports/` on latitude

## Follow-ups → plans

| Topic | Action |
| ----- | ------ |
| `.7z` support | Add `py7zr` to `pyproject.toml` `[compressed]` optional extra |
| `boar_fast_filter` in lab hosts | Add `maturin develop --release` step to completão preflight or HOMELAB_VALIDATION |
| `scan_scope` warning | Emit WARNING in `config/loader.py` when `scan_scope` key is present but `targets` is not |
| Larger benchmark corpus | Use `tests/data/bench/synthetic_valid_cpf_3k.txt` as standard corpus; re-run A/B to confirm 0.574x claim |
| Forensic search use case | `PLAN_FORENSIC_SEARCH_AND_GEOGRAPHIC_HINTS.md` Slice 1 — config template, low effort |
| Geographic breadcrumbs | Same plan Slice 1 — DDD regex overlays |
