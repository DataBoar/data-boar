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
| **4 — Transfer hierarchy** | rsync > scp; Hub pull for stable | `Sync-WorkingTree.ps1` prefers rsync; `Build-ContainerArtefact.ps1` pulls Hub for stable tags | H1 |
| **5 — Ephemeral cleanup** | No stale bench dirs or images | `Collect-Artifacts.ps1` removes `/tmp/databoar_bench/$track/` post-collect; stale container images pruned | H1 |
| **6 — Lessons learned pipeline** | JSONL → plans/fixes | `scripts/maestro-lessons-harvest.ps1` parses JSONL events → promotes to `PLANS_TODO.md` or inline fix by priority matrix | H2 |
| **7 — Oracle XE target** | SQL matrix completeness | `Handle-target_oracle.ps1` + synthetic schema | H2 |
| **8 — Locust persona** | Load test integration | `Handle-loadtest.ps1` + `tests/locustfile.py` | H2 |
| **9 — Full A/B clean run** | v1.7.3 vs v1.7.4-rc | `maestro-benchmark-ab.ps1` green end-to-end | H1 milestone |
| **10 — `boar_fast_filter` timing** | Rust core proof | `_lc_bench_compare` delta stable vs beta confirmed | H1 milestone |
| **11 — Dependency doctor** | Graceful optional dep healing + OS-level Ansible fallback | Smoke script detects `archive_unsupported` / `ModuleNotFoundError`, tries `uv sync --extra compressed`, tests import, if `_lzma` missing attempts Ansible OS package install via narrow sudoers, retries import, marks host with `7z_UNSUPPORTED` feature flag if all attempts fail, continues scan without aborting; all attempts logged with success/failure; lessons-harvest picks up the flag | H2 |
| **12 — Server-side share validation** | NFS/CIFS/SSHFS target completeness | Target handlers validate server services + exports before declaring target READY; auto-remediation via narrow sudoers; E2E mount probe from scanner to target | H2 |

---

## Server-side share validation detail (Slice 12)

### The current gap

Target handlers (`Handle-target_nfs.ps1`, `Handle-target_cifs.ps1`, `Handle-target_sshfs.ps1`)
today validate only: **does the path directory exist on the target node?** (`test -d`).
They do NOT validate whether the share is actually accessible from the scanner node —
meaning Data Boar could fail silently trying to mount a share that was never exported.

### What each target handler should validate (and optionally remediate)

#### NFS target

```bash
# Server-side checks (run on target node via SSH):
systemctl is-active nfs-server       # NFS kernel server running
systemctl is-active rpcbind          # portmapper running (NFS dependency)
exportfs -v | grep "$TARGET_PATH"    # path is actually exported
showmount -e localhost               # confirm export visible

# If not running (narrow sudoers LABOP_NFS_SERVER):
sudo systemctl start rpcbind nfs-server
echo "$TARGET_PATH *(rw,sync,no_subtree_check)" >> /etc/exports
sudo exportfs -ra

# E2E probe from scanner node (NOT target node):
mount -t nfs $TARGET_IP:$TARGET_PATH /tmp/probe_mount_nfs -o ro,timeo=10
ls /tmp/probe_mount_nfs && echo "NFS_MOUNT_OK"
umount /tmp/probe_mount_nfs
```

#### CIFS / Samba target

```bash
# Server-side checks (run on target node via SSH):
systemctl is-active smbd             # Samba file server
systemctl is-active nmbd             # Samba NetBIOS name server (optional but typical)
smbclient -L localhost -N | grep "$SHARE_NAME"  # share visible locally

# If not running (narrow sudoers LABOP_SMB_SERVER):
sudo systemctl start smbd nmbd
# Share must exist in /etc/samba/smb.conf (configuration step, not auto-created)

# E2E probe from scanner node:
smbclient //$TARGET_IP/$SHARE_NAME -N -c "ls" 2>&1 | grep -v "^$"
```

#### SSHFS target

```bash
# Server-side: SSHFS is SSH-native — no dedicated server daemon
# Validate:
systemctl is-active sshd             # SSH daemon running on target
ssh -o BatchMode=yes -o ConnectTimeout=5 $TARGET_USER@$TARGET_IP "test -r $TARGET_PATH && echo PATH_READABLE"

# E2E probe from scanner node:
sshfs $TARGET_USER@$TARGET_IP:$TARGET_PATH /tmp/probe_mount_sshfs -o ro,ConnectTimeout=10
ls /tmp/probe_mount_sshfs && echo "SSHFS_MOUNT_OK"
fusermount -u /tmp/probe_mount_sshfs
```

### New sudoers entries needed (LABOP_NFS_SERVER, LABOP_SMB_SERVER)

```sudoers
Cmnd_Alias LABOP_NFS_SERVER = /bin/bash /home/leitao/Projects/dev/data-boar/scripts/labop-nfs-server-ensure.sh --check, \
                              /usr/bin/bash /home/leitao/Projects/dev/data-boar/scripts/labop-nfs-server-ensure.sh --check, \
                              /bin/bash /home/leitao/Projects/dev/data-boar/scripts/labop-nfs-server-ensure.sh --apply, \
                              /usr/bin/bash /home/leitao/Projects/dev/data-boar/scripts/labop-nfs-server-ensure.sh --apply
Cmnd_Alias LABOP_SMB_SERVER = /bin/bash /home/leitao/Projects/dev/data-boar/scripts/labop-smb-server-ensure.sh --check, \
                              /usr/bin/bash /home/leitao/Projects/dev/data-boar/scripts/labop-smb-server-ensure.sh --check, \
                              /bin/bash /home/leitao/Projects/dev/data-boar/scripts/labop-smb-server-ensure.sh --apply, \
                              /usr/bin/bash /home/leitao/Projects/dev/data-boar/scripts/labop-smb-server-ensure.sh --apply
leitao ALL=(root) NOPASSWD: LABOP_NFS_SERVER, LABOP_SMB_SERVER
```

### Handler upgrade contract

Each target handler returns one of three states:
- `TARGET_READY` — server up, path exported/shared, E2E probe succeeded
- `TARGET_DEGRADED` — server up, path exported, but E2E mount failed (network/firewall issue)
- `TARGET_OFFLINE` — server not running; auto-remediation attempted; if failed, skip scan

`Handle-target_sshfs.ps1`, `Handle-target_nfs.ps1`, `Handle-target_cifs.ps1` write state
to `~/.labop-status` on the target node (currently only writes `TARGET_ACTIVE` without
distinguishing server vs client vs E2E). `Get-LabStatus.ps1` reads this to show
`[TARGET READY]`, `[TARGET DEGRADED]`, or `[TARGET OFFLINE]` in the Maestro table.

### Data Boar scan connector link

The completão validates the **infrastructure layer** (mount works). For the scan layer,
`Handle-target_nfs.ps1` should also invoke a minimal Data Boar scan via the NFS mount
path (same pattern as `Handle-target_postgres.ps1` which provisions the DB and then
signals the Data Boar scanner node). The scan result (`filesystem_findings` count on
the NFS/CIFS/SSHFS mount path) validates the full pipeline:

```
Target node (NFS/CIFS server) → mount on scanner → Data Boar scans mount → findings
```

This is the true end-to-end proof: not just "directory exists" but "Data Boar found
PII in data that lives on a remote share, accessed via protocol X."
| **11 — Dependency doctor** | Graceful optional dep healing + OS-level Ansible fallback | Smoke script detects `archive_unsupported` / `ModuleNotFoundError`, tries `uv sync --extra compressed`, tests import, if `_lzma` missing attempts Ansible OS package install via narrow sudoers, retries import, marks host with `7z_UNSUPPORTED` feature flag if all attempts fail, continues scan without aborting; all attempts logged with success/failure; lessons-harvest picks up the flag | H2 |

---

## Dependency doctor detail (Slice 11)

### Flow (ordered, graceful degradation)

```
Smoke detects archive_unsupported or ModuleNotFoundError for py7zr
  |
  +- Step 1: uv sync --extra compressed
  |     Log: "[DepDoctor] Attempting uv sync --extra compressed on $HOST"
  |     Test: uv run python3 -c "import py7zr"
  |     If OK -> retry scan -> log: "[DepDoctor] SUCCESS: py7zr installed via uv sync"
  |
  +- Step 2: if _lzma missing (import fails with No module named _lzma)
  |     Detect OS package manager on remote host:
  |       apt     -> "apt-get install -y liblzma-dev"    (Debian/Ubuntu/Zorin)
  |       xbps    -> "xbps-install -y xz-devel"          (Void Linux)
  |       pacman  -> "pacman -S --noconfirm xz"           (Arch/Manjaro)
  |       dnf     -> "dnf install -y xz-devel"            (Fedora/RHEL/Rocky)
  |       zypper  -> "zypper install -y xz-devel"         (openSUSE)
  |       apk     -> "apk add xz-dev"                     (Alpine)
  |       none    -> skip, go to Step 3
  |     Log: "[DepDoctor] PM detected: $PM. Installing $PKG on $HOST via narrow sudoers"
  |     Run: ssh $HOST "sudo -n $PM_INSTALL_CMD"   (NOPASSWD entry per distro)
  |     Log: exit code + stdout/stderr captured
  |     If package installed -> uv python install (or pyenv reinstall) to rebuild Python
  |     Test: uv run python3 -c "import py7zr"
  |     If OK -> retry scan -> log: "[DepDoctor] SUCCESS: _lzma resolved via OS PM ($PM)"
  |
  +- Step 3: Ansible playbook (complex/multi-step or insufficient sudoers)
  |     Run: ansible-playbook scripts/maestro/playbooks/install_lzma_dev.yml -l $HOST
  |     Log attempt, PM used, outcome, any package manager output captured
  |     Test: uv run python3 -c "import py7zr"
  |     If OK -> retry scan -> log: "[DepDoctor] SUCCESS: _lzma resolved via Ansible"
  |
  +- Step 4: all attempts failed
        Log: "[DepDoctor] FAILURE: 7z unavailable on $HOST after all remediation attempts."
        Write inventory feature flag:
          { "7z": false, "reason": "lzma_unavailable",
            "pm_tried": "$PM", "last_attempt": "$DATE", "steps_tried": 3 }
        Continue scan without .7z targets -- do NOT abort completao
        Emit WARNING in Maestro final report
        lessons-harvest.ps1 converts flag to action item in PLANS_TODO
```

### Ansible playbook contract

`scripts/maestro/playbooks/install_lzma_dev.yml` (to be created in Slice 11):
- Detects distro family (`ansible_os_family`: Debian, RedHat, Arch, Void, Suse, Alpine)
  and uses the correct package name per distro (see Step 2 table above)
- Requires narrow sudoers entries per distro — template in
  `docs/private/homelab/LABOP_COMPLETAO_SUDOERS*.md`
- Scope: **additive only** — never removes packages, never upgrades OS, never changes Python version
- Idempotent: checks if lzma header already present before running package manager
- After install: triggers `uv python install` (or `pyenv install`) to rebuild Python with lzma support
- Logs every step to `docs/private/homelab/reports/dep_doctor_$HOST_$DATE.log`
- Fails loudly with diagnostic if distro not recognized — does not guess

### Feature flag in inventory

After a failed dependency doctor run, `docs/private/homelab/data/inventory.json` gains:

```json
{
  "hostname": "latitude",
  "feature_flags": {
    "7z": false,
    "7z_reason": "lzma_unavailable",
    "7z_doctor_attempted": "2026-05-13",
    "7z_doctor_result": "needs_python_rebuild"
  }
}
```

Maestro respects this flag on future runs: skips `.7z` scan targets for flagged hosts without
re-attempting the doctor (unless operator passes `-ForceRedoctor` flag).

---

## Transfer hierarchy (Slice 4 detail)

**Priority:** `rsync` > `scp` — never `unison` (bidirectional; overkill for one-way push).

`Sync-WorkingTree.ps1` strategy:
1. Try `rsync -az --delete --exclude=.git --exclude=.venv` — fastest, delta-only, handles large trees well.
2. Fall back to `scp -r` if `rsync` not in PATH on either end — log which path was taken.

`Build-ContainerArtefact.ps1` / image distribution:
1. **Stable tags** (e.g. `v1.7.3`, `latest`): `docker pull fabioleitao/data_boar:$tag` from Hub on lab host directly when possible — avoids `docker save`/`scp`/`docker load` round-trip entirely.
2. **RC/beta tags** (not on Hub): build locally on dev PC → `docker save` → `rsync`/`scp` → `docker load` on lab host (current behaviour).
3. **Guard:** before build, check if `docker images -q fabioleitao/data_boar:$tag` returns a valid ID on the lab host — skip transfer entirely if image already present and not stale.

Env var override: `DATA_BOAR_MAESTRO_FORCE_LOCAL_BUILD=1` forces local build even for stable tags (for testing image changes not yet published).

## Ephemeral cleanup policy (Slice 5 detail)

**After `-Collect` phase completes successfully:**

On each lab host (via SSH after SCP):

```bash
# Remove bench workdir for this run_id only (not other concurrent runs)
rm -rf /tmp/databoar_bench/$LC_BENCH_TRACK/metrics/$LC_BENCH_RUN_ID_* 2>/dev/null || true
# Remove sentinel after confirmed collect
rm -f /tmp/databoar_bench/$LC_BENCH_TRACK/.completao_done_$LC_BENCH_RUN_ID 2>/dev/null || true
# Prune benchmark container images older than 3 runs
docker image prune -f --filter "label=maestro.bench=true" 2>/dev/null || true
```

**Keep:**
- `/tmp/databoar_bench/$track/` root and `.checkpoint_isolation_marker` (needed by parallel runs)
- `docs/private/homelab/reports/` on dev PC — never delete; this is the audit trail

**Parameter:** `maestro-benchmark-ab.ps1` gains `-SkipCleanup` flag (default: clean). `Maestro.ps1 -Collect` gains `-CleanupAfterCollect` flag.

## Lessons learned pipeline (Slice 6 detail)

After each completão session, `scripts/maestro-lessons-harvest.ps1`:

1. Parses JSONL event stream from `docs/private/homelab/reports/completao_*.jsonl`.
2. Extracts `status: failed` / `status: warning` events with their `phase` and `message`.
3. For each finding, checks against **existing priority matrix**:
   - Matches an open H0/H1 plan → appends as evidence bullet to that plan's carryover.
   - Matches H2/H3 → creates or updates a `PLAN_MAESTRO_LAB_FINDINGS_YYYY_MM.md` stub.
   - No plan match → emits a low-effort inline fix suggestion in the harvest report.
4. Outputs `docs/private/homelab/reports/LESSONS_HARVEST_$runId.md` for operator review.
5. Operator promotes actionable items to `PLANS_TODO.md` or `PLAN_MAESTRO_*.md` manually — harvest never writes to tracked plans automatically (audit trail, not autopilot).

Token-aware: harvest runs `--quick` mode by default (last session only); `--all` for full history audit.

## Acceptance criteria (Slice 1 — bugs only)

- [ ] `tests/test_maestro_scripts.py` passes with ConnectTimeout present in all SSH calls.
- [ ] `Handle-baremetal.ps1 -Deep` correctly passes `--bench-config tests/config/benchmark-rc.yaml` to smoke script.
- [ ] `lab-completao-host-smoke.sh --bench-config tests/config/benchmark-rc.yaml` exits 0 (or uses the config).
- [ ] `maestro-benchmark-ab.ps1` has `-SleepBeforeCollect` parameter with default 120s.
- [ ] One dry-run `Maestro.ps1 -Deep -BenchTrack stable` on a single lab host returns in <5 minutes (not 9 hours).
