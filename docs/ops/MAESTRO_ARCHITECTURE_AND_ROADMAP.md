# Maestro — architecture, mythology, and evolution roadmap

**Português (Brasil):** [MAESTRO_ARCHITECTURE_AND_ROADMAP.pt_BR.md](MAESTRO_ARCHITECTURE_AND_ROADMAP.pt_BR.md)

**Related:** [LAB_COMPLETAO_RUNBOOK.md](LAB_COMPLETAO_RUNBOOK.md) · [COMPLETAO_OPERATOR_PROMPT_LIBRARY.md](COMPLETAO_OPERATOR_PROMPT_LIBRARY.md)

---

## 1. What Maestro is

**Maestro** is the central, persona-based, inventory-driven orchestrator for **Lab-Op** — the Data Boar homelab environment. It is not a test runner. It is not a CI pipeline. It is a **conductor**: it reads a private inventory (the score), dispatches to specialized sub-orchestrators (the musicians), and collects the evidence of a complete performance (the completão).

Maestro exists because lab validation — real hosts, real SSH, real containers, real databases, real file systems, real protocols — cannot be fully represented by unit tests or GitHub CI. When Data Boar scans a production PostgreSQL with mixed-encoding column names or a MariaDB with empty schemas, that surface is only exercised in lab. Maestro makes that exercise repeatable, documented, and comparable across versions.

### The metaphor

| Musical term | Maestro meaning |
| ------------ | --------------- |
| Maestro (conductor) | `Maestro.ps1` — reads the score, controls tempo and sequence |
| Section lead *(informally: capo di sezione — metaphor flavor only)* | `Handle-*.ps1` **handlers** — each owns its instrument section completely; the canonical term in code and docs is **handler** |
| Musician | Lab node (LAB-NODE-01, LAB-NODE-03, LAB-T14, …) — the performer |
| Instrument / Voice (Persona) | The role each node plays: `docker`, `podman`, `baremetal`, `web`, `target_postgres`, … |
| Score | `docs/private/homelab/data/inventory.json` — who plays what |
| Performance (Completão) | One full run across all nodes, all personas, all target surfaces |
| Encore (A/B benchmark) | `maestro-benchmark-ab.ps1` — stable vs rc, same score, two performances |
| Program notes | `docs/private/homelab/reports/` — evidence of each performance |

The word **completão** is Brazilian Portuguese slang for "the full works" — a deliberate nod to the cultural context of the project and a reminder that the goal is **completeness**, not perfection.

---

## 2. How it got here — brief history

The first orchestration approach was **monolithic**: `lab-completao-orchestrate-hybrid-v173.ps1` and its variants (plano-a through plano-v). These scripts hardcoded node roles, image paths, and benchmark logic in a single long PowerShell file. They worked — they measured `boar_fast_filter` import timing, ran A/B comparisons between v1.7.3 stable and v1.7.4-rc, and produced JSONL event streams. But they were brittle: each "plano" variant was a handcrafted fork, not a general system.

**Maestro** was designed to replace all 22 hybrid-plano variants with one general framework:

- **Inventory-driven:** node roles, paths, users, and capabilities come from a private JSON manifest — no hardcoded hostnames in tracked code.
- **Persona-based dispatch:** each capability is encapsulated in a `Handle-<persona>.ps1` file, called by the orchestrator based on the inventory entry. Adding a new node type = adding one handler file.
- **Phase model:** Pre-flight (build/sync artefact) → Dispatch (persona handlers) → Collect (artifact download) → Report.
- **PII isolation:** zero real hostnames, IPs, or user accounts in tracked code; all in gitignored `inventory.json`.

---

## 3. Architecture

### 3.1 Component map

```
scripts/
  maestro/
    Maestro.ps1                    ← Central orchestrator
    Build-ContainerArtefact.ps1    ← Build Docker image on dev PC
    Sync-WorkingTree.ps1           ← rsync/scp repo to lab host
    Sync-ContainerArtefact.ps1     ← docker save + scp image to host
    Get-LabStatus.ps1              ← SSH preflight check per node
    Collect-Artifacts.ps1          ← SCP metrics/logs from host
    handlers/
      Handle-baremetal.ps1         ← uv + Python smoke via tmux
      Handle-docker.ps1            ← docker run / compose via tmux
      Handle-dockerswarm.ps1       ← Docker Swarm service via tmux
      Handle-podman.ps1            ← Rootless Podman via tmux
      Handle-microk8s.ps1          ← k8s pod via tmux
      Handle-lxd.ps1               ← LXD container via tmux
      Handle-web.ps1               ← HTTP health check (sync); load test gate
      Handle-target_postgres.ps1   ← Synthetic PostgreSQL via compose
      Handle-target_mariadb.ps1    ← Synthetic MariaDB via compose
      Handle-target_mongodb.ps1    ← Synthetic MongoDB via compose
      Handle-target_nfs.ps1        ← NFS mount/unmount
      Handle-target_sshfs.ps1      ← SSHFS mount/unmount
      Handle-target_cifs.ps1       ← SMB/CIFS mount/unmount
  maestro-benchmark-ab.ps1        ← A/B wrapper (stable vs rc)
  lab-completao-host-smoke.sh     ← Per-host smoke (bash, runs in tmux on OS)
  lab-completao-container-smoke.sh ← Container smoke: detects Docker/Podman,
                                     starts Data Boar RC container (port 9002),
                                     writes ~/.labop-status; invoked by
                                     docker/podman handlers via tmux; calls
                                     host smoke with --skip-engine-import
```

### 3.2 Execution flow

```
Maestro.ps1 -Deep -BenchTrack beta -BenchRunId abc123
│
├─ Build-ContainerArtefact.ps1   (once, pre-flight: build data_boar:lab)
│
└─ foreach node in inventory.lab_members
   ├─ Get-LabStatus.ps1          (SSH preflight: UP/DOWN)
   ├─ Sync-WorkingTree.ps1       (rsync or scp repo to node.path)
   ├─ Sync-ContainerArtefact.ps1 (docker save → scp → docker load, if container persona)
   └─ foreach persona in node.personas (ordered: container first, web last)
      └─ Handle-<persona>.ps1 @handlerArgs
         └─ ssh: tmux send-keys → lab-completao-host-smoke.sh (async, inside tmux)
                                   or direct docker/podman/compose command
│
└─ -Collect phase (Maestro.ps1)
   └─ foreach node
      └─ Collect-Artifacts.ps1  (scp metrics from /tmp/databoar_bench/$track/)
```

### 3.3 Handler taxonomy (persona handlers)

**Handlers** (`Handle-<persona>.ps1`) are the specialized sub-orchestrators — one per persona type. Each handler owns its domain completely: it receives context from the Maestro and is fully responsible for how its section performs. In narrative docs the handlers are sometimes described with the musical metaphor of a *capo di sezione* (section lead), but the canonical code and taxonomy term is always **handler**.

Handlers are additive — one node can have multiple. The inventory entry lists them; Maestro orders dispatch (container personas first, `web` last, others in declaration order).

| Persona | Handler (`Handle-<persona>.ps1`) | What it exercises |
| ------- | ------------ | ------------- |
| `baremetal` | Handle-baremetal.ps1 | Data Boar via `uv run` on bare OS |
| `docker` | Handle-docker.ps1 | Docker CE `docker run` / `docker compose` |
| `dockerswarm` | Handle-dockerswarm.ps1 | Docker Swarm service mode |
| `podman` | Handle-podman.ps1 | Rootless Podman container |
| `microk8s` | Handle-microk8s.ps1 | Kubernetes pod via microk8s |
| `lxd` | Handle-lxd.ps1 | LXD system container |
| `web` | Handle-web.ps1 | HTTP `/health` + API reachability; load test gate |
| `target_postgres` | Handle-target_postgres.ps1 | Synthetic PostgreSQL (compose), scanned cross-host |
| `target_mariadb` | Handle-target_mariadb.ps1 | Synthetic MariaDB (compose), scanned cross-host |
| `target_mongodb` | Handle-target_mongodb.ps1 | Synthetic MongoDB (compose), scanned cross-host |
| `target_nfs` | Handle-target_nfs.ps1 | NFS share mount |
| `target_sshfs` | Handle-target_sshfs.ps1 | SSHFS mount |
| `target_cifs` | Handle-target_cifs.ps1 | SMB/CIFS mount |
| `target_oracle` *(roadmap)* | Handle-target_oracle.ps1 | Synthetic Oracle XE (compose) |
| `loadtest` *(roadmap)* | Handle-loadtest.ps1 | Locust HTTP load test after web health |

### 3.4 Inventory contract

`docs/private/homelab/data/inventory.json` — never tracked in public Git. Each `lab_member` entry:

```json
{
  "hostname": "<alias>",
  "user": "<ssh-user>",
  "ip": "<lan-ip>",
  "path": "<repo-path-on-host>",
  "personas": ["docker", "web", "target_postgres"],
  "web_port": 8088,
  "web_scheme": "http"
}
```

---

## 4. The completão concept — why it matters

CI tests synthetic data in isolation. Completão tests **integration reality**:

| CI / pytest | Completão |
| ----------- | --------- |
| Controlled synthetic corpus | Real OS, real filesystem permissions, real encoding |
| Single Python version | Multiple Python versions, multiple distros |
| GitHub-hosted runner | Operator's LAN, real hardware, real network |
| Mock database | Live PostgreSQL / MariaDB / MongoDB with synthetic data |
| No SSH, no container lifecycle | Full container pull → start → scan → stop |
| No load | Concurrent scan + API + dashboard |

A completão run that passes on all nodes and all personas is the closest thing to a **release confidence proof** available before customer deployment.

---

## 5. Known bugs (confirmed 2026-05-12)

See `PLAN_MAESTRO_BENCHMARK_METRICS_AND_FIX.md` for full analysis. Summary:

1. **Bug 1 (critical):** All SSH calls lack `ConnectTimeout` — can hang indefinitely.
2. **Bug 2 (critical):** `-Deep` handlers pass `benchmark-rc.yaml` as unknown positional arg to `lab-completao-host-smoke.sh` — every Deep run exits 2 silently; no metrics written.
3. **Bug 3 (race):** `-Collect` runs immediately after async tmux injection, before smoke finishes — SCP of non-existent artifacts.

**These three bugs caused the 9-hour wait-state observed on 2026-05-12.** Fix before next benchmark run.

---

## 6. How to use Maestro

### 6.1 Prerequisites

1. Lab hosts reachable via SSH from the dev PC (keys in `ssh-agent`).
2. `docs/private/homelab/data/inventory.json` present (copy from example in `docs/private.example/`).
3. `tmux` running on each lab host with a `completao` session (or Maestro creates it — see Bug 3 fix roadmap).
4. Docker CE / Podman installed on container-persona hosts.

### 6.2 Common invocations

```powershell
# Standard completão (smoke only, current working tree)
.\scripts\maestro\Maestro.ps1

# Deep benchmark run (uses benchmark-rc.yaml, collects metrics)
# NOTE: Bug 2 currently prevents this from working on baremetal/docker. Fix first.
.\scripts\maestro\Maestro.ps1 -Deep -BenchTrack beta -BenchRunId "20260513_post_fix"

# Collect artifacts from last async run
.\scripts\maestro\Maestro.ps1 -Collect

# A/B benchmark (stable v1.7.3 vs rc v1.7.4)
.\scripts\maestro-benchmark-ab.ps1 `
  -LegacyRef v1.7.3 -LegacyTrack stable -LegacyWebPort 18088 `
  -CandidateRef v1.7.4-rc -CandidateTrack beta -CandidateWebPort 28088 `
  -BenchCompare
```

### 6.3 Reading results

After a run with `-Collect`:
- `docs/private/homelab/reports/` — per-run Markdown notes, JSONL event streams, vmstat/iostat/free logs.
- `docs/private/homelab/reports/MAESTRO_BENCHMARK_AB_*.md` — A/B round comparison table.
- Per-host `/tmp/databoar_bench/<track>/metrics/` — raw benchmark metric files (before collection).

Session keyword: **`completao`** in Cursor chat → runs `lab-completao-orchestrate.ps1 -Privileged` (the simpler wrapper). **`lab-lessons`** → archives session notes.

---

## 7. Evolution roadmap

### 7.1 Near-term (bugs + reliability — H1)

See `PLAN_MAESTRO_BENCHMARK_METRICS_AND_FIX.md` Slice 1–3:

- Fix SSH timeouts (Bug 1)
- Fix `--bench-config` arg (Bug 2)
- Add sentinel file + `Wait-CompletaoSmoke.ps1` (Bug 3)
- Create tmux session if missing (instead of requiring pre-existing `completao` session)

### 7.2 Medium-term (completeness — H2)

- **Locust persona** (`Handle-loadtest.ps1`) — HTTP load test after health check; A/B RPS/latency delta. See `PLAN_LOCUST_LOAD_TEST_INTEGRATION.md`.
- **Oracle XE target** (`Handle-target_oracle.ps1`) — complete the SQL connector matrix.
- **Full metrics comparison** — structured diff report: findings count parity, scan wall-clock, `boar_fast_filter` import delta, RAM peak, IO wait.
- **Ansible integration** — replace `scp`-based provisioning with idempotent Ansible playbooks for lab stack bring-up.

### 7.3 Long-term — Maestro as a standalone companion product (H3/H4)

Maestro is architecturally generic: any inventory-driven, persona-based SSH orchestrator for multi-host validation. It is not inherently tied to Data Boar. Potential evolution paths:

#### 7.3.1 Open-source companion tool

Extract Maestro's core (inventory schema, persona dispatch, artifact collect) into a small standalone PowerShell module or Python CLI that anyone can use to orchestrate multi-host lab smoke tests for any product. Data Boar ships its own handler pack; third-party integrators write their own.

#### 7.3.2 Academic context (lato sensu / stricto sensu)

The Maestro design embodies several concepts relevant to applied computer science theses:

- **Persona-based distributed test orchestration** — a formal study of the persona taxonomy as a design pattern for heterogeneous lab environments.
- **Evidence-based release confidence** — Maestro as an operator-facing "release proof" system; connecting to the `boar_fast_filter` Rust/PyO3 integration as a measurable performance contract.
- **Reproducible lab benchmarking** — the A/B methodology (isolated workdirs, sentinel files, JSONL event streams) as a contribution to reproducible science in software engineering.

Any of these could form a chapter or a case study in a stricto sensu thesis, grounded in the Data Boar codebase as a real-world artifact.

#### 7.3.3 Commercial context

In the consulting engagement model (Engajamento A — law firm, Engajamento B — pharma distribution), Maestro can serve as the **deployment validation tool** that runs after a Data Boar instance is deployed at a client site:

- Client receives a Docker image → run `Maestro.ps1` against client's inventory → completão output is the **delivery evidence**.
- Future: a customer-facing "health check" mode that produces a report the client's IT team can read, separate from the full homelab benchmark.

---

## 8. Naming and taxonomy alignment

Maestro aligns with the broader Data Boar mythology:

| Data Boar concept | Maestro equivalent |
| ----------------- | ------------------ |
| Data Sniffing (discovery pass) | Pre-flight phase (`Get-LabStatus`) |
| Deep Boring (compliance depth) | `-Deep` mode (benchmark-rc.yaml, full metrics) |
| Safe-Hold (halt on missing evidence) | Missing inventory → hard exit 1; SSH DOWN → skip with warning |
| Audit Trail | `docs/private/homelab/reports/` + JSONL event stream |
| Boar (thoroughness) | Completão — digs through every target, every persona, leaves nothing unexercised |

The handlers are the boar's tusks: each one specialized for a specific substrate, collectively covering the full data soup of the lab.

---

## 9. Files in this ops directory related to Maestro

| File | Purpose |
| ---- | ------- |
| [LAB_COMPLETAO_RUNBOOK.md](LAB_COMPLETAO_RUNBOOK.md) | Operator contract: what completão is, blast radius, assistant access |
| [LAB_COMPLETAO_FRESH_AGENT_BRIEF.md](LAB_COMPLETAO_FRESH_AGENT_BRIEF.md) | Copy-paste prompts for zero-context agent sessions |
| [COMPLETAO_OPERATOR_PROMPT_LIBRARY.md](COMPLETAO_OPERATOR_PROMPT_LIBRARY.md) | Failure classification, follow-up blocks, pre-canned briefs |
| [LAB_SMOKE_MULTI_HOST.md](LAB_SMOKE_MULTI_HOST.md) | Manual multi-host checklist (steps A–M) |
| [LAB_LESSONS_LEARNED.md](LAB_LESSONS_LEARNED.md) | Rolling public hub for completão findings |
| `scripts/maestro/` | All Maestro handler and orchestrator code |
| `scripts/lab-completao-host-smoke.sh` | Per-host smoke script (runs in tmux on lab hosts) |
| `scripts/maestro-benchmark-ab.ps1` | A/B benchmark wrapper |
| `docs/plans/PLAN_MAESTRO_BENCHMARK_METRICS_AND_FIX.md` | Bug fixes + full test matrix roadmap |
| `docs/plans/PLAN_LOCUST_LOAD_TEST_INTEGRATION.md` | Locust HTTP load test integration |
