# Plan: Maestro benchmark metrics, bug fixes, and full test matrix

**Status:** Active
**Date:** 2026-05-12
**Authors:** Fabio Leitao
**Priority:** H1
**Depends on:** PLAN_SYNTHETIC_DATA_AND_CONFIDENCE_VALIDATION.md

<!-- plans-hub-summary: Fix 3 confirmed Maestro bugs causing 9h wait-states; add per-run metrics collection; build comprehensive test matrix across all lab personas, OSes, protocols, and DB targets for v1.7.3 vs v1.7.4-rc A/B. -->
<!-- plans-hub-related: PLAN_LOCUST_LOAD_TEST_INTEGRATION.md, PLAN_SQL_SAMPLING_SRE_AND_AUDIT_EVIDENCE.md -->

## Root cause analysis — 9-hour wait-state (2026-05-12)

Three confirmed bugs found by code inspection. The A/B benchmark injected smoke into tmux but crashed
immediately on the lab hosts (Bug 3), leaving `-Collect` waiting for artifacts that were never written.

### Bug 1 — SSH calls with no `ConnectTimeout` (all handlers + Maestro.ps1)

**File:** `Handle-baremetal.ps1:56`, `Handle-docker.ps1:58`, `Handle-web.ps1:98,172,186`,
`Maestro.ps1:51`

**Pattern:**

```powershell
ssh -q -o BatchMode=yes "$user@$host" "$cmd"
```

**Problem:** `BatchMode=yes` prevents password prompts but does not set a connection timeout.
If a lab host has a routing issue, RST is not sent, or SSH daemon stalls, the call hangs
**indefinitely**. This is the primary cause of multi-hour waits in Cursor terminal tasks.

**Fix:**

```powershell
ssh -q -o BatchMode=yes -o ConnectTimeout=15 -o ServerAliveInterval=30 -o ServerAliveCountMax=3 "$user@$host" "$cmd"
```

Apply to **every** `ssh` invocation across all handlers and Maestro.ps1.

### Bug 2 — `bench-rc.yaml` passed as unknown positional arg (baremetal + docker handlers)

**File:** `Handle-baremetal.ps1:30-32`, `Handle-docker.ps1:30-32`

**Pattern:**

```powershell
$configArg = if ($Deep) { "tests/config/benchmark-rc.yaml" } else { "" }
$smokeArgs += $configArg  # passes as positional arg to lab-completao-host-smoke.sh
```

**Problem:** `lab-completao-host-smoke.sh` does not accept a positional config path. Its CLI
parser hits the `*` catch-all case and exits 2:

```bash
*) echo "lab-completao-host-smoke: unknown arg: $1 (try --help)" >&2; exit 2 ;;
```

**Impact:** Every `-Deep` run on baremetal and docker personas fails silently — the tmux session
exits 2 immediately, no metrics files are written, `-Collect` finds nothing to collect.
`Handle-web.ps1` uses a separate `$configArg` (passed to `main.py --config`), not the smoke
script — web persona is unaffected.

**Fix (Option A — config via env var):**

```bash
# In lab-completao-host-smoke.sh, add to arg parser:
--bench-config)
  LC_BENCH_CONFIG="${2:-}"
  shift
  ;;
```

```powershell
# In Handle-baremetal.ps1 / Handle-docker.ps1:
if (-not [string]::IsNullOrWhiteSpace($configArg)) {
    $smokeArgs += "--bench-config $configArg"
}
```

**Fix (Option B — remove from smoke, handle in container entrypoint):**
Pass `$configArg` to `docker run` / `uv run` entrypoint only, not to the smoke script. Cleaner
for container personas; smoke script stays agnostic.

Recommendation: **Option A** for baremetal (direct invocation), **Option B** for docker/podman.

### Bug 3 — `-Collect` races async tmux execution (no completion signal)

**File:** `maestro-benchmark-ab.ps1:91-106`

**Pattern:**

```powershell
& $MaestroScript @deepArgs | Out-Null   # returns immediately (tmux inject)
# ... no wait ...
$collectArgs = @{Collect = $true; ...}
& $MaestroScript @collectArgs | Out-Null  # tries to SCP artifacts before they exist
```

**Problem:** Handlers inject via `tmux send-keys` and return immediately. The smoke script runs
asynchronously in tmux. `Collect-Artifacts.ps1` then runs SCP on files that haven't been
created yet (or are still being written). Result: SCP fails silently or hangs on partial files.

**Fix:** Add a polling mechanism or a sentinel file approach:

```bash
# At end of lab-completao-host-smoke.sh:
echo "DONE:$LC_BENCH_RUN_ID" > "$LC_BENCH_ROOT/.completao_done_$LC_BENCH_RUN_ID"
```

```powershell
# New script: Wait-CompletaoSmoke.ps1 -- polls for sentinel file via SSH
# maestro-benchmark-ab.ps1: call Wait-CompletaoSmoke.ps1 before -Collect
```

Alternative (simpler): add a configurable `-SleepBeforeCollect` parameter to
`maestro-benchmark-ab.ps1` (default: 120 seconds), giving smoke time to finish. Not elegant
but removes the race for typical runs where smoke takes 30–90s.

---

## Hybrid-173 as spec — what it had that Maestro needs to recover

The `lab-completao-orchestrate-hybrid-v173.ps1` scripts (plano-a through plano-v) represent the
**proven measurement approach** for v1.7.3 vs v1.7.4-rc. Key capabilities to port:

1. **Detached tmux session creation** — hybrid creates `tmux new-session -d -s completao_stable`
   and `completao_beta` per track, not inject into an existing session. The Maestro assumes the
   `completao` session already exists; if it doesn't, `send-keys` fails silently on the remote.

2. **Ephemeral workdirs** — `/tmp/databoar_bench/stable` and `/tmp/databoar_bench/beta` with
   separate configs. Maestro has this via `_lc_init_bench_workdir` in the smoke script.

3. **Image distribution from dev PC** — `docker save`/`rsync`/`docker load` before run.
   Maestro delegates this to `Build-ContainerArtefact.ps1` and `Sync-ContainerArtefact.ps1` —
   verify these scripts exist and work.

4. **`boar_fast_filter` import timing** — `_lc_bench_compare()` in smoke script measures this
   but only when `LAB_COMPLETAO_BENCH_COMPARE=1`. The hybrid ran this systematically. The Maestro
   needs to set this env var in the `-BenchCompare` path (already wired in handlers but verify
   it reaches the remote env).

5. **JSONL event stream** — hybrid emitted `completao_hybrid_<timestamp>_events.jsonl` (confirmed
   in `docs/private/homelab/reports/`). The smoke script has `DATA_BOAR_COMPLETAO_JSONL_MIN_EVENT`
   but the Maestro's `-Collect` phase needs to pull this file.

---

## Comprehensive test matrix (full vision)

Once bugs 1–3 are fixed and Locust is integrated, the Maestro should exercise:

### Personas (all combinable)

| Persona | Handler | What it tests |
| ------- | ------- | ------------- |
| `baremetal` | Handle-baremetal.ps1 | uv + Python scan, bare OS |
| `docker` | Handle-docker.ps1 | Docker CE `docker run` |
| `dockerswarm` | Handle-dockerswarm.ps1 | Swarm service mode |
| `podman` | Handle-podman.ps1 | Rootless Podman |
| `microk8s` | Handle-microk8s.ps1 | k8s pod |
| `lxd` | Handle-lxd.ps1 | LXD container |
| `web` | Handle-web.ps1 | HTTP API health + Locust |
| `loadtest` *(new)* | Handle-loadtest.ps1 | Locust load test |

### Scan targets (all synthetic)

| Target | Handler | Protocol | Synthetic data |
| ------ | ------- | -------- | -------------- |
| Local filesystem | baremetal | fs | `tests/data/` |
| PostgreSQL | target_postgres | TCP/psycopg2 | `PLAN_SYNTHETIC_DATA_AND_CONFIDENCE_VALIDATION.md` |
| MariaDB / MySQL | target_mariadb | TCP/mysqlclient | Same |
| MongoDB | target_mongodb | TCP/pymongo | Same |
| Oracle XE *(new)* | target_oracle *(new)* | TCP/cx_Oracle | Same |
| SMB/CIFS share | target_cifs | SMB | Synthetic share mount |
| NFS share | target_nfs | NFS | Synthetic NFS mount |
| SSHFS | target_sshfs | SSH+FUSE | Remote filesystem |

### Metrics collected per run

| Metric | Source | File |
| ------ | ------ | ---- |
| Wall clock (scan total) | smoke script `time` | `*_meta.txt` |
| vmstat (CPU/IO wait) | `_lc_capture_metrics_snapshot` | `*_vmstat.log` |
| iostat | same | `*_iostat.log` |
| RAM (free -m) | same | `*_free.log` |
| Top CPU procs | same | `*_topcpu.log` |
| `boar_fast_filter` import time | `_lc_bench_compare` | stdout / JSONL |
| Findings count | report Excel row count | via API `/api/scan` result |
| Report size (bytes) | SCP artifact | collected Excel |
| HTTP latency p50/p95 | Locust CSV | `locust_*_stats.csv` |
| Locust RPS | same | same |
| Locust failure rate | same | same |
| JSONL event count | smoke JSONL stream | `*_events.jsonl` |

### A/B delta (stable vs beta after bugs fixed)

```
maestro-benchmark-ab.ps1 \
  -LegacyRef v1.7.3 -LegacyTrack stable -LegacyWebPort 18088 \
  -CandidateRef v1.7.4-rc -CandidateTrack beta -CandidateWebPort 28088 \
  -BenchCompare -RunId "20260513_first_clean_ab"
```

Expected output in `docs/private/homelab/reports/MAESTRO_BENCHMARK_AB_*.md`:
- Wall clock delta: beta vs stable (faster = `boar_fast_filter` PyO3 fix confirmed)
- Locust RPS delta
- Findings count parity (must be equal; regression if different on same corpus)

---

## Slices

| Slice | Focus | Delivers | Priority |
| ----- | ----- | -------- | -------- |
| **1 — Bug fixes** | SSH timeout + config arg + collect race | 3 code fixes across 5 files; `tests/test_maestro_scripts.py` updated | **P0** |
| **2 — Sentinel + poll** | Reliable collect | `Wait-CompletaoSmoke.ps1` + sentinel file in smoke script | H1 |
| **3 — Detached tmux create** | No "session must exist" assumption | `Handle-*.ps1` create session if missing | H1 |
| **4 — Oracle XE target** | SQL matrix completeness | `Handle-target_oracle.ps1` + synthetic schema | H2 |
| **5 — Locust persona** | Load test integration | `Handle-loadtest.ps1` + `tests/locustfile.py` | H2 |
| **6 — Full A/B clean run** | v1.7.3 vs v1.7.4-rc | `maestro-benchmark-ab.ps1` green end-to-end | H1 milestone |
| **7 — `boar_fast_filter` timing** | Rust core proof | `_lc_bench_compare` delta stable vs beta confirmed | H1 milestone |

## Acceptance criteria (Slice 1 — bugs only)

- [ ] `tests/test_maestro_scripts.py` passes with ConnectTimeout present in all SSH calls.
- [ ] `Handle-baremetal.ps1 -Deep` correctly passes `--bench-config tests/config/benchmark-rc.yaml` to smoke script.
- [ ] `lab-completao-host-smoke.sh --bench-config tests/config/benchmark-rc.yaml` exits 0 (or uses the config).
- [ ] `maestro-benchmark-ab.ps1` has `-SleepBeforeCollect` parameter with default 120s.
- [ ] One dry-run `Maestro.ps1 -Deep -BenchTrack stable` on a single lab host returns in <5 minutes (not 9 hours).
