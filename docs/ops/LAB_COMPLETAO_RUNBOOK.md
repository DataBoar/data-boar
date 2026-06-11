# Lab “completão” vs CI / pytest

**Português (Brasil):** [LAB_COMPLETAO_RUNBOOK.pt_BR.md](LAB_COMPLETAO_RUNBOOK.pt_BR.md)

**Purpose:** Define what **completão** means in this project: **running the product** (CLI, API, web) on **lab hosts**, across **SSH**, with **documented** outcomes — not the same thing as `**pytest`** or `**.\scripts\check-all.ps1**` on the dev PC alone.

**Positioning (orchestration vs unit tests):** Completão is **not** a substitute for **`pytest`** or GitHub CI — it is an **orchestration and lab-environment validation** layer for **repeatable, documented** outcomes on **real** hosts. The Windows dev workstation runs **PowerShell** orchestrators against **Linux** targets over **SSH** (plus optional HTTP checks from the LAN), exercising **connectivity, permissions, runtime plumbing, and smoke paths** that unit tests alone **cannot** fully represent. Cursor rules (`.mdc`), **prompt libraries**, **fresh-agent briefs**, and **`lab_result.json`** exist so assistants can **load contracts**, prefer the right scripts, classify failures (**timeout** vs **auth** vs **parser** — see **[`COMPLETAO_OPERATOR_PROMPT_LIBRARY.md`](COMPLETAO_OPERATOR_PROMPT_LIBRARY.md)**), and leave **evidence** under **`docs/private/homelab/reports/`** with less churn — **without** implying zero human judgment for high-blast lab changes.

**New Cursor chat / zero context:** Use **[LAB_COMPLETAO_FRESH_AGENT_BRIEF.md](LAB_COMPLETAO_FRESH_AGENT_BRIEF.md)** — copy-paste prompts (**smoke-only** vs **extended**), optional checklists, follow-up blocks **B–E**, preconditions, and honest scope (what scripts run vs what needs operator config).

## Assistant and operator contract (Cursor)

- **Access:** The assistant runs `**ssh`**, scripts, and `**curl**` from the **Cursor integrated terminal** on the **operator’s Windows dev PC** — **same LAN and SSH config** as the operator’s shell (see `**homelab-ssh-via-terminal.mdc`**). Do **not** treat “assistant” as a separate network.
- **Default orchestration:** When the operator asks for **completão** or uses session keyword `**completao`**, the assistant should run `**.\scripts\lab-completao-orchestrate.ps1 -Privileged**` from the repo root unless the operator opts out. Logs: `**docs/private/homelab/reports/**`.
- **Privileged probes:** `**sudo -v`** in the smoke script requires **narrow sudoers** on each Linux host (template under gitignored `**LABOP_COMPLETÃO_SUDOERS*.md`**). `**sudo -v` in tmux** warms sudo for **that TTY**, not automatically for **non-interactive** `ssh host 'sudo …'` — for reliable `**-Privileged`** runs, align sudoers with the template.
- **On failure:** If `**sudo -v`** or SSH fails, the assistant **reminds** the operator to refresh sudoers / SSH agent / interactive sudo as needed, then **re-runs** the tests — see `**lab-completao-workflow.mdc`**.
- **Lab-as-test-datacenter scope:** For **completão**, the assistant **may** install **missing deps**, fix **app/compose ports**, add **narrow** **lab-op-to-lab-op** firewall or **VLAN** rules (via `**ufw`**, `**nftables**`, **LAB-ROUTER-01** scripts when configured), and tune **SELinux**/**AppArmor**/**fail2ban**/**sshguard**/**USBGuard**/**AIDE**/**auditd** (etc.) **only** with **least privilege** and **reversible** intent — full policy: `**lab-completao-workflow.mdc`**. Record what changed in `**docs/private/homelab/**`; never ship **secrets** or **LAN specifics** to **public** Git.
- **Wrappers + sudoers + no idle prompts:** Prefer `**lab-completao-orchestrate.ps1 -Privileged`** and related repo scripts (see `**LAB_OP_PRIVILEGED_COLLECTION.md**`, gitignored `**LABOP_COMPLETÃO_SUDOERS*.md**`) so remote hosts use **passwordless narrow sudo** for probes. **Do not** re-ask permission for the agreed SSH/`**-Privileged`** flow. **Protect** the **primary Windows dev PC** (**L-series** role, `**PRIMARY_WINDOWS_WORKSTATION_PROTECTION.md`**) and its **canonical** clone; **other** manifest hosts and **Docker** images may be **resynced** from `**origin`** / Hub for tests.

### Blast radius (contract — assistants must not confuse targets)

| Target                                                                                    | Git / repo policy                                                                                                                                                                                                                               | Rationale                                                                                                       |
| ----------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------- |
| **Primary Windows dev PC** (ThinkPad **L-series**, Cursor workspace, **canonical** clone) | **Never** `**git reset --hard`**, `**git clean -fdx**`, `**clean-slate**`, or history rewrite on the **main** working tree. Use normal `**git pull` / merge / branch / stash**.                                                                 | Continuity of evidence and history — `**PRIMARY_WINDOWS_WORKSTATION_PROTECTION.md`**.                           |
| **LAB-OP hosts** in `**lab-op-hosts.manifest.json`** (each `**repoPaths**` on SSH)        | **Safe** to `**git fetch`**, `**git pull --ff-only**`, `**lab-op-git-align-main.ps1**`, `**lab-op-git-ensure-ref**`, `**-AlignLabClonesToLabGitRef**` — these scripts affect **only** those **remote** clones, **not** the primary dev PC tree. | Disposable lab checkouts; align from GitHub **without** treating it like the primary dev PC.                    |
| **Container images** (Docker / **Swarm** / **Podman** / **Kubernetes**)                   | **Re-pull** from **Docker Hub** (or configured registry); `**docker pull`**, stack/service update, prune — **normal** for lab.                                                                                                                  | Images are **reproducible** from registry — not the same blast radius as destructive Git on the primary dev PC. |

- **LAB-OP inventory map (hardware + software):** Before interpreting host-smoke results, assistants should `**read_file`** the private master chart `**docs/private/homelab/OPERATOR_SYSTEM_MAP.md**` and software matrix `**docs/private/homelab/LAB_SOFTWARE_INVENTORY.md**` when present (`**docs-private-workspace-context.mdc**`). `**lab-completao-orchestrate.ps1**` runs `**scripts/lab-completao-inventory-preflight.ps1**` first (default **15-day** freshness): if either file is missing or older than the threshold, it runs `**lab-op-sync-and-collect.ps1`** to refresh `**homelab-host-report**` telemetry under `**docs/private/homelab/reports/**` — then **merge** findings into the markdown inventories and bump an explicit **as-of** date (see *Inventory freshness* below). Opt out: `**-SkipInventoryPreflight`**; tune age: `**-InventoryMaxAgeDays N**`.

**Relationship:**

| Layer                  | What it is                                                  | Typical command                                                                                      |
| ---------------------- | ----------------------------------------------------------- | ---------------------------------------------------------------------------------------------------- |
| **CI / unit & guards** | Reproducible, GitHub-hosted, no LAN secrets                 | `CI` workflow, `pytest`                                                                              |
| **Dev PC gate**        | Full local hook bundle + tests before merge                 | `.\scripts\check-all.ps1`                                                                            |
| **Lab completão**      | Product + runtime + LAN + optional DB stack + optional HTTP | `scripts/lab-completao-host-smoke.sh` per host; `scripts/lab-completao-orchestrate.ps1` from Windows |

## Public vs private lab evidence (lessons learned)

| Tier | Location | Content |
| ---- | -------- | ------- |
| **Private** | `docs/private/homelab/COMPLETAO_SESSION_*.md`, `docs/private/homelab/reports/` | Full narrative, LAN, credentials, operator notes — **never** paste verbatim into public Git. |
| **Public hub** | [`docs/ops/LAB_LESSONS_LEARNED.md`](LAB_LESSONS_LEARNED.md) | Rolling summary + archive index + **follow-up** pointers into **`docs/plans/PLANS_TODO.md`**. |
| **Public archive** | [`docs/ops/lab_lessons_learned/`](lab_lessons_learned/README.md) | Immutable dated snapshots: **`LAB_LESSONS_LEARNED_YYYY_MM_DD.md`** (see README for ritual). |

**Contract:** [ADR 0042](../adr/ADR-0042-lab-lessons-learned-archive-contract.md). **Session token:** **`lab-lessons`** loads **`.cursor/rules/lab-lessons-learned-archive.mdc`** when globs do not attach it — [OPERATOR_AGENT_COLD_START_LADDER.md](OPERATOR_AGENT_COLD_START_LADDER.md) § *Token → rule latch (`lab-lessons`)*.

**Canonical multi-host checklist** (manual steps A–M): [LAB_SMOKE_MULTI_HOST.md](LAB_SMOKE_MULTI_HOST.md).

## Inventory freshness (before / during completão)

**Why:** Hardware changes rarely; **software versions** (Python, Docker, distro packages) change often and affect decisions (e.g. container-only vs native `**uv`**, connector builds). Stale private inventories increase misinterpretation.

1. **Tracked automation:** `**scripts/lab-completao-inventory-preflight.ps1`** checks `**docs/private/homelab/LAB_SOFTWARE_INVENTORY.md**` and `**OPERATOR_SYSTEM_MAP.md**`. For each file it uses, in order: a line `**<!-- lab-op-inventory-as-of: YYYY-MM-DD -->**` or `****Lab inventory as-of:** YYYY-MM-DD**` (or Portuguese *Inventário … as-of*), else **file LastWriteTime**.
2. **Default threshold:** **15 days** (`-MaxAgeDays` / `**-InventoryMaxAgeDays*`* on the orchestrator). If **stale or missing**, `**lab-completao-orchestrate.ps1`** runs `**lab-op-sync-and-collect.ps1**` (same manifest) unless `**-SkipInventoryPreflight**`. Use `**-SkipGitPullOnInventoryRefresh**` on the orchestrator only if you want reports **without** `**git pull`** on lab clones.
3. **After telemetry:** `**lab-op-sync-and-collect`** does **not** rewrite the inventories — **update** the matrices from the latest `*_labop_sync_collect.log`, then set **as-of** near the top of each file so the next run’s age check is accurate.
4. **Manual preflight:** `.\scripts\lab-completao-inventory-preflight.ps1 -AutoRefresh` (same defaults).

## Data contract preflight (optional — fail before host smoke)

**Goal:** Catch **schema drift** in lab databases (renamed/dropped columns) **before** SSH host smoke and product scans, similar in spirit to **contract testing**.

1. **Manifest (root key):** optional **`completaoDataContractsPath`** — path to a YAML file (usually under **`docs/private/homelab/`**, gitignored). Relative paths resolve from the repo root.
2. **YAML format:** copy **`docs/private.example/homelab/completao_data_contracts.example.yaml`** — lists **`checks`** with **`connection.url_from_env`** (SQLAlchemy URL in the **operator shell**, never in the YAML), **`schema`** / **`table`**, and **`require_columns`**.
3. **Runner:** **`scripts/lab_completao_data_contract_check.py`** — uses SQLAlchemy **`inspect`**; supports any dialect your URL provides (PostgreSQL, MSSQL via **`mssql+pyodbc`**, MySQL/MariaDB, SQLite, etc.).
4. **Orchestrator hook:** **`lab-completao-orchestrate.ps1`** runs the checker **after** **`lab-op-git-ensure-ref`** (when a ref check ran or was skipped) and **before** per-host SSH smoke. If the manifest sets **`completaoDataContractsPath`** but the file is **missing**, the orchestrator **throws** (misconfiguration). Opt out: **`-SkipDataContractPreflight`**.

## Structured orchestration events (JSONL) and idempotent preflights

**Goal:** If the orchestrator is interrupted mid-run, operators and automation still get **machine-readable** phase boundaries (inventory, git ref, data contract, per-host smoke, summary). Failures attach a **`message`** and optional **`detail`** object per line.

1. **Main orchestrator:** each run appends one JSON object per line to **`docs/private/homelab/reports/completao_<timestamp>_orchestrate_events.jsonl`** (UTF-8, no BOM). Fields include **`v`**, **`ts`**, **`phase`**, **`status`**, **`message`**, **`host`**, **`exitCode`** (when set), **`detail`** (hashtable when set).
2. **Phases (non-exhaustive):** **`orchestrate`** (start), **`inventory_preflight`**, **`lab_git_ensure_ref`**, **`data_contract_preflight`**, **`image_preflight`**, **`host_smoke`**, **`summary`**, **`lab_result`** (machine-readable summary written at end of run), **`grc_executive_report`** (optional: runs **`scripts/generate_grc_report.py`** via **`uv run python`** after **`lab_result.json`**; writes **`GRC_EXECUTIVE_REPORT.json`** plus stamped **`completao_<stamp>_GRC_EXECUTIVE_REPORT.json`** under the same reports directory; failures are **warnings** only and do not change the completão semantic exit code), **`grc_export_artifacts`** (when the latest GRC JSON exists: runs **`scripts/export_reports.py`**; writes **`GRC_EXECUTIVE_REPORT_remediation.xlsx`** and **`GRC_EXECUTIVE_REPORT_executive.pdf`** plus stamped copies; failures are **warnings** only).
3. **Optional container image preflight (read-only, non-blocking):** manifest root **`completaoImageRefs`** — JSON array of strings (e.g. **`fabioleitao/data_boar:lab`**). Before host smoke, the script SSHs to **`completaoImageProbeSshHost`** if set (and **not** a **LAB-NODE-04** passive host), otherwise the **first non-LAB-NODE-04** manifest **`sshHost`**, and runs **`docker image inspect`** / **`podman image inspect`** for each ref (**no pull**, **no create**). Missing images or probe SSH failure emit **`warning`** JSON lines and **`Write-Warning`** text; the orchestrator **continues** to host smoke (benchmark hosts can still load images mid-flight). Opt out: **`-SkipImagePreflight`**. **LAB-NODE-04** is never used as the image-probe engine.
4. **Hybrid A/B path (`-HybridLabOpHighDensity173`):** **`lab-completao-orchestrate-hybrid-v173.ps1`** writes **`completao_hybrid_<timestamp>_events.jsonl`** with **stable vs candidate** runs: isolated **`/tmp/databoar_bench/stable`** and **`/tmp/databoar_bench/beta`** workdirs (directory name **beta** is historical; the **candidate** Docker tag tracks **`pyproject.toml`**), host ports **9001** (stable **v1.7.3**) and **9002** (**v1.7.4-rc** at time of this doc refresh), detached **tmux** per bench step when no operator **`completao`** session exists. The hybrid script **does not rely on `docker pull` / `podman pull` on targets**: on the **primary Windows dev workstation** it **`docker save` / `podman save`** both **`fabioleitao/data_boar:1.7.3`** and **`fabioleitao/data_boar:1.7.4-rc`** (unless you set pre-built paths), then **`rsync`** over SSH when **`rsync`** is on PATH else **`scp`**, then runs **`docker load` / `podman load` for both archives before** writing **`config_databoar.yaml`**. Optional overrides: **`DATA_BOAR_HYBRID_STABLE_TAR_GZ`** and **`DATA_BOAR_HYBRID_BETA_TAR_GZ`** (Windows paths; **`.tar`** or **`.tar.gz`**). It copies **`scripts/lab-completao-host-smoke.sh`** (and **`scripts/lab_completao_data_contract_check.py`** when present) into **`.../stable/scripts/`** and **`.../beta/scripts/`** for direct SSH runs from the bench dirs. Optional **`DATA_BOAR_HYBRID_REMOTE_PULL_SCRIPTS=1`** plus **`DATA_BOAR_HYBRID_REMOTE_PULL_REF`** (default branch **`main`** on **`origin`**, or **`upstream/main`**, etc.) runs **`git fetch` + `git pull --ff-only`** on the manifest **`repoPaths[0]`** clone on each engine host. Compare **`benchmark_compare`** **`delta_ms`** in JSONL for wall-clock vs **FFI/Python-boundary** interpretation.

## Agent-readable run summary (`lab_result.json`)

**Goal:** Let a fresh agent (or automation) diff the **current** run against a **previous** `lab_result.json` without parsing full console logs.

1. **Location:** same directory as other completão artifacts: **`docs/private/homelab/reports/lab_result.json`** and **`lab_status.json`** (identical payload; both **atomically** overwritten each run so agents never read a partial file) plus **`completao_<timestamp>_lab_result.json`** (one copy per stamp, next to **`completao_<timestamp>_orchestrate_events.jsonl`**).
2. **Top-level fields (non-exhaustive):** **`schemaVersion`**, **`kind`** (`data_boar_lab_completao_orchestrate`), **`run_stamp`**, **`generated_at_utc`**, **`repo_folder_name`**, **`manifest_file_name`**, **`audit_trail`** (who/what invoked the run — see below), **`exit_code_semantic`** (process exit contract + reason on the success path), **`overall_status`** (`completed`, **`completed_with_skips`**, or **`degraded`** from connectivity + host loop), **`phases`** (string map of preflight + **`host_smoke_loop`** outcomes), **`orchestration_checks`** (array of **`step`** / **`result`** rows mirroring those phases for quick diff), **`idempotency`** (which filenames are overwritten vs stamp-scoped history), **`connectivity_status`**, **`vulnerabilities_found`**, **`vulnerability_scan`**, **`performance_metrics`**, **`run_flags`**, **`artifacts`**, **`agent_readable_hint`**.
3. **Connectivity `summary` values (orchestrator heuristic):** **`no_host_records`**, **`all_hosts_completed_paths_ok`**, **`degraded`** (any host record whose **`outcome`** matches unreachable / exception / repo path / base failure patterns).
4. **`audit_trail` (traceability):** records **`windows_session_user`**, **`windows_computer_name`**, **`powershell_pid`**, UTC timestamp, and optional **`invoker_correlation`** from environment variable **`DATA_BOAR_COMPLETAO_INVOKER`** (set by the operator or automation to a ticket id, Cursor session label, or agent id). This supports ISO 27001-style accountability and LGPD-oriented operating discipline; it is **not** a legal attestation by itself.
5. **`exit_code_semantic`:** object with **`contract`** = **`DATA_BOAR_COMPLETAO_EXIT_v1`**, integer **`value`**, string **`reason`**, and a **`meanings`** map explaining codes **0–3** (see next section). On the orchestrator **success path**, the process exit code matches **`exit_code_semantic.value`** (PowerShell `exit`).

## Telemetry-first exit codes (`DATA_BOAR_COMPLETAO_EXIT_v1`)

**Goal:** CI, release prompts, and assistants map failures **without** parsing every log line.

| Code | Class | Typical sources in this repo |
| --- | --- | --- |
| **0** | Full success | Orchestrator finished with **`overall_status`** = **`completed`** (connectivity summary not **degraded**). **`lab_completao_data_contract_check.py`** returns **0**. **`lab-completao-host-smoke.sh`** returns **0** after emitting its diagnostic bundle. |
| **1** | Infrastructure / permission / reachability | SSH probe or transport failure, **`lab_completao_data_contract_check.py`** DB URL env empty or DB **`database error:`** connectivity/auth, orchestrator **`degraded`** or **`completed_with_skips`**. (Container **image preflight** is **non-blocking**: missing images log **`warning`** and the run continues.) |
| **2** | Data, schema, or repo contract | **`lab_completao_data_contract_check.py`** missing-column / YAML shape errors (after connect), remote clone missing **`scripts/lab-completao-host-smoke.sh`** (embedded SSH guard uses **exit 2**), **`lab-completao-host-smoke.sh`** unknown CLI argument (**exit 2**). |
| **3** | Compliance violation (reserved) | Policy or scanner hooks that assert a governed breach (baseline scripts do **not** emit **3** yet; reserve for future wiring). |

**Note:** Uncaught PowerShell **`throw`** paths may still end with the host default non-zero code (**1**) before **`lab_result.json`** is written — use **`completao_*_orchestrate_events.jsonl`** for partial-run forensics.

## Target git ref for reproducible completão (LAB clones)

Host smoke runs `scripts/lab-completao-host-smoke.sh` from each `repoPaths` checkout. If those clones drift arbitrarily, a completão run is **not** comparable to CI, a release gate, or another session — you are exercising **whatever commit happens to be checked out**.

1. **Declare a ref:** optional root key `**completaoTargetRef`** in `docs/private/homelab/lab-op-hosts.manifest.json` (see `docs/private.example/homelab/lab-op-hosts.manifest.example.json`), and/or pass `**-LabGitRef**` to `lab-completao-orchestrate.ps1`. CLI `**-LabGitRef**` wins when non-empty; otherwise the manifest value is used.
2. **Check before smoke:** When a ref is set and `**-SkipLabGitRefCheck`** is **not** passed, the orchestrator runs `**scripts/lab-op-git-ensure-ref.ps1`** in **Check** mode (after inventory preflight, before SSH smoke). It `git fetch`es on each clone (**branch** fetch must succeed; **tag** fetch is best-effort so “would clobber existing tag” cannot abort the remote script before `LABOP_REF_*` lines — see script header) and **fails** if `HEAD` is not the resolved commit for that ref (`main` / `origin/main` → `origin/main` tip; release tags, branch names, and full SHAs supported). Logs: `docs/private/homelab/reports/lab_op_git_ensure_ref_*.log`.
3. **Release tags vs inventory refresh:** `lab-op-sync-and-collect.ps1` (run when inventory markdown is stale) performs `**git pull --ff-only`** on lab clones, which advances them to **latest `main`**. That can **break** a pin to `**vX.Y.Z`**. When testing a **tag**, pass `**-SkipGitPullOnInventoryRefresh`** on `lab-completao-orchestrate.ps1` so refresh does not move clones before **ensure-ref**; refresh private inventories manually if needed.
4. **Align / reset on LAB only:** `**lab-op-git-ensure-ref.ps1 -Mode Reset`**, `**lab-op-git-align-main.ps1**`, or `**lab-completao-orchestrate.ps1 -AlignLabClonesToLabGitRef**` with `**-LabGitRef**` (or manifest `**completaoTargetRef**`) apply **only** to `**repoPaths`** on **manifest SSH hosts** — **never** to the operator’s **canonical** clone on the **primary Windows dev PC**. Same risk class as `**lab-op-git-align-main.ps1`** on those remotes (drops local commits on **lab** clones / detached HEAD at tag).

## Pre-Big-Bang gate (LAB mirror + network clearance)

**Goal:** Before a high-blast “Big Bang” lab session, make **LAB-OP clones** match `**origin/main`** or a **release tag** (e.g. `**v1.7.3`**), avoid inventory refresh `**git pull**` fighting a tag pin, and collect **read-only** firewall / dependency hints. **This script never mutates the operator’s Windows/WSL2 canonical working tree** — only manifest `**repoPaths`** on SSH hosts.

1. **Run from the dev PC (Cursor terminal):** `**.\scripts\lab-op-pre-big-bang.ps1`**
  - `**-Ref origin/main**` (default) or `**-Ref v1.7.3**` (or another tag / SHA / branch name supported by `**lab-op-git-ensure-ref.ps1**`).
  - `**-ForceLabGitReset`:** runs `**lab-op-git-ensure-ref.ps1 -Mode Reset`** on each manifest clone (LAB-only destructive align / detached tag checkout). Without it, **Check** only (fails if clones do not match the resolved ref).
  - **Tag pins:** for `**vX.Y.Z`**, the script runs `**lab-completao-inventory-preflight.ps1 -AutoRefresh -SkipGitPullOnRefresh**` first (unless `**-SkipInventoryWarmup**`) so a stale inventory refresh does not `**git pull**` lab clones to `**main**` before the tag alignment.
  - `**-IncludeProbes`:** SSH per host for `**LABOP_BB_GIT_*`**, `**ufw` / `fail2ban` / `ss**` snippets (best-effort `**sudo -n**`), and on **LAB-NODE-03** / **LAB-NODE-04** hosts a `**python3`** **zlib/bz2/lzma** import smoke plus `**xbps-query` / `dpkg`** hints.
  - `**-OrchestratorSshSourceIp`:** embeds a concrete **fail2ban `ignoreip`** hint for the orchestration PC during SSH bursts.
2. **Log output:** `**docs/private/homelab/reports/lab_op_pre_big_bang_<timestamp>.log`** includes `**LABOP_BB_GIT_ENSURE_REF_OK**` when `**lab-op-git-ensure-ref**` succeeds, `**LABOP_BB_OPERATOR_FIREWALL_CLEAR_PENDING**`, and a **non-executable** checklist (UFW/nft, Postgres **5432**, MariaDB **3306**, NFS/SMB ports, AppArmor/SELinux / **auditd**, fail2ban / **sshguard**). **“Firewall Clear”** is an **operator attestation** after applying narrow rules in **tmux** with `**sudo -v`** — the script does **not** auto-open firewall holes.
3. **After this gate:** run `**lab-completao-orchestrate.ps1`** (and hybrid paths if used) with the same `**-LabGitRef**` / manifest `**completaoTargetRef**` policy as in *Target git ref* above.

## Capability coverage (documentation + code truth)

**Goal:** Learn **observed** behaviour vs **documented** intent — **English** docs and **code** are canonical ([docs/README.md](../README.md)). Completão should **exercise** (where lab resources allow): **remote storage** (NFS, SSHFS, SMB/CIFS — OS mounts and/or connector paths per [TECH_GUIDE.md](../TECH_GUIDE.md)); **databases** ([deploy/lab-smoke-stack](../deploy/lab-smoke-stack/), connectors per [ADDING_CONNECTORS.md](../ADDING_CONNECTORS.md)); **file types**, **extensions**, **hidden/dot** paths, **archives**; **local vs remote** targets; **LGPD-oriented discoverables** as **detection language** ([COMPLIANCE_AND_LEGAL.md](../COMPLIANCE_AND_LEGAL.md) — not legal advice); **ML/DL sensitivity** ([SENSITIVITY_DETECTION.md](../SENSITIVITY_DETECTION.md), [TESTING.md](../TESTING.md)); **reports** and **dashboard** flows; **POC** paths — maturity questionnaire ([SMOKE_MATURITY_ASSESSMENT_POC.md](SMOKE_MATURITY_ASSESSMENT_POC.md)), **WebAuthn/FIDO2** JSON RP ([SMOKE_WEBAUTHN_JSON.md](SMOKE_WEBAUTHN_JSON.md), [SECURE_DASHBOARD_AUTH_AND_HTTPS_HOWTO.md](SECURE_DASHBOARD_AUTH_AND_HTTPS_HOWTO.md), [ADR 0033](../adr/ADR-0033-webauthn-open-relying-party-json-endpoints.md)). **Secure-by-design** claims must align with [SECURITY.md](../SECURITY.md) and **what actually ran**. Record **pass / gap / drift** in **private** session notes (`docs/private/homelab/`) — **policy:** `**.cursor/rules/lab-completao-workflow.mdc*`* (capability matrix section).

## Scripts (tracked)

1. `**scripts/lab-completao-host-smoke.sh**` (run **on each Linux lab host**, from repo root): `uv`, `docker` / `podman`, `deploy/lab-smoke-stack` compose `ps` if present, optional `**LAB_COMPLETAO_HEALTH_URL`** or `**--health-url**` for `/health`, quick `**import core.engine**` unless `**--skip-engine-import**` (or `**LAB_COMPLETAO_SKIP_ENGINE_IMPORT=1**`) — see **Container-only lab hosts** below. `**--privileged`**: read-only snapshots via `**sudo -n**` (iptables/nft/ufw/fail2ban-related) — skips if sudo cannot run non-interactively.
2. `**scripts/lab-completao-orchestrate.ps1**` (run **on the Windows dev PC**): reads `**docs/private/homelab/lab-op-hosts.manifest.json`** (same idea as `**lab-op-sync-and-collect.ps1**`); optional root `**completaoTargetRef**` or CLI `**-LabGitRef**` triggers `**lab-op-git-ensure-ref.ps1**` before smoke unless `**-SkipLabGitRefCheck**`; SSH to each `**sshHost**`, runs the bash script for each `**repoPaths**` entry; optional per-host `**completaoHealthUrl**`: after SSH smoke, `**Invoke-WebRequest**` from the dev PC (LAN client view); optional `**completaoEngineMode`:** `**container`** or `**completaoSkipEngineImport`:** `**true`** passes `**--skip-engine-import**` to the host smoke (Docker Swarm / Podman-only hosts with **no** bare-metal `**uv`**); writes `**docs/private/homelab/reports/completao_<timestamp>_allhosts.log**`, per-host `*_completao_host_smoke.log`, and **`lab_result.json`** / **`lab_status.json`** (same JSON; plus stamped copy) — see *Agent-readable run summary* above.
3. **Passwordless sudo (narrow)** — same discipline as `**homelab-host-report.sh`**: template under **gitignored** `**docs/private/homelab/LABOP_COMPLETÃO_SUDOERS.pt_BR.md`**. Do **not** commit real sudoers content to GitHub.
4. **Session log / lessons template** — `**docs/private/homelab/COMPLETAO_SESSION_TEMPLATE.pt_BR.md`** (gitignored private tree): date, host, pass/fail, value, lessons learned. Filled examples stay under `**docs/private/homelab/**` as `**COMPLETAO_SESSION_YYYY-MM-DD.md**` (operator-only; never public GitHub).
5. `**scripts/lab-op-repo-status.ps1**` (Windows): `**git fetch**` + `**git status -sb**` on each `**repoPaths**` (no reset). Optional `**-PullFfOnly**` for `**git pull --ff-only**` when the clone is strictly behind. **Start here** when orchestrate reports `**MISSING_SCRIPT`** — usually the clone is older than `**main**`.
6. `**scripts/lab-op-git-ensure-ref.ps1**` (Windows): for each host, `**git fetch**` on each `**repoPaths**` clone, then **Check** (fail if `HEAD` ≠ resolved ref) or **Reset** (destructive checkout/reset to match the ref). Used automatically by `**lab-completao-orchestrate.ps1`** when `**completaoTargetRef**` / `**-LabGitRef**` is set — see *Target git ref for reproducible completão* above.
7. `**scripts/lab-op-pre-big-bang.ps1*`* (Windows): optional **Pre-Big-Bang gate** — `**lab-op-git-ensure-ref`** (Check or `**-ForceLabGitReset**` for Reset), tag-aware inventory warmup, operator firewall / fail2ban / AppArmor checklist, and `**-IncludeProbes**` for read-only `**ufw` / fail2ban / `ss**` and **LAB-NODE-03 / LAB-NODE-04** compression dependency hints. See *Pre-Big-Bang gate* above. Does **not** modify the canonical dev PC clone.
8. `**scripts/lab-op-git-align-main.ps1`** (Windows): for each host in the same manifest, `**git fetch**` + `**git reset --hard origin/main**` on each `**repoPaths**` entry. **Destructive** (drops local commits on the clone); use when LAB-OP trees must match GitHub `**main`** and you accept losing local-only commits on those clones. For non-`**main**` refs (e.g. release tags), prefer `**lab-op-git-ensure-ref.ps1 -Mode Reset**`.
9. **Ansible (optional):** `**ops/automation/ansible/playbooks/lab-op-data-boar-git-sync.yml`** — alignment via group `**lab_op_data_boar**` in a local inventory (see `**inventory.example.ini**`). Reproducible when Ansible is already part of your operator workflow.
10. **Filesystem templates (tracked, copy to private or `~` on Linux):** `**docs/private.example/homelab/config.lab-fs-varlog.example.yaml`**, `**config.lab-fs-home-user.example.yaml**` — run `**main.py**` **on the same host** as the paths (SSH + `export PATH=$HOME/.local/bin:$PATH`; `**mkdir -p`** report/sqlite dirs first). `**/var/log**` may emit `**permission_denied**` for non-root users on some files — expected.
11. **MongoDB in completão:** connector `**driver: mongodb`**; install `**pymongo**` with `**uv sync --extra nosql**`. Bring up the optional stack: `**deploy/lab-smoke-stack**`: `**docker compose -f docker-compose.yml -f docker-compose.mongo.yml up -d**` (published port **27018** by default). If Mongo is down, the target fails as **unreachable**, not **unsupported**.

## Container-only lab hosts (Docker Swarm, Podman stack, no bare-metal `uv`)

Some lab machines are **orchestrator** or **policy** roles: the operator runs Data Boar **only** via **Docker** / **Podman** / **Docker Swarm** (stack or service), and **does not** rely on `**uv`** on the host for SSH-driven checks. That is a **valid** completão posture when recorded in the private manifest — assistants should **not** treat “`uv` not in PATH” on those hosts as a defect to “fix” by forcing a host Python env.

1. In `**docs/private/homelab/lab-op-hosts.manifest.json`**, set `**completaoEngineMode**` to `**container**` **or** `**completaoSkipEngineImport`** to `**true**` for that `**sshHost**`. `**lab-completao-orchestrate.ps1**` then passes `**--skip-engine-import**`; the smoke logs an explicit **skipped** line for `**import core.engine`** instead of implying failure.
2. **Success criteria** on those hosts: container runtime CLI healthy, optional `**deploy/lab-smoke-stack`** `**compose ps**` when compose is used there, and/or `**completaoHealthUrl**` (e.g. published `**8088**`) returning **200** from the dev PC.
3. **Filesystem / CLI scans** against paths on that host still need **some** runtime (bind-mounted `**uv run`** inside a container, or another documented path). The host smoke **does not** replace that — note in private session files which approach you used.

See `**docs/private.example/homelab/lab-op-hosts.manifest.example.json`** for optional fields.

## Hardware-limited lab nodes (LAB-NODE-04, LAB-NODE-03 Void, Alpine/musl; Kubernetes deferred)

- **Alpine Linux / musl host (eMachines E527 — 5th host, [#821](https://github.com/FabioLeitao/data-boar/issues/821)):** Celeron 900, 3.8 GB RAM. musl libc requires packages compiled against musl (`apk add` not `apt`/`dnf`). Key notes for completão:
  - `uv` and Python wheels with C extensions may require **musl-compatible wheels** or source builds — set `completaoSkipEngineImport: true` in the manifest and validate via container or passive path until native engine import is confirmed.
  - Slow CPU: if the smoke script hits a `HealthTimeoutSec` deadline (default varies by script), **increase the timeout** for this host via manifest field `completaoHealthTimeoutSec` or by passing `--health-timeout N` to the smoke script. Start with **60 s** and lower only after a successful run.
  - Standard `apk` packages: `python3`, `py3-pip`, `docker`, `openssh`.
  - Log any additional packages needed in **`docs/private/homelab/LAB_SOFTWARE_INVENTORY.md`** and the completão session notes.
- **LAB-NODE-04 (no Docker on hardware):** set `**completaoHardwareProfile`** to a value starting with `**LAB-NODE-04**` (or use an `**sshHost**` alias containing `**LAB-NODE-04**`). `**lab-completao-orchestrate.ps1**` then runs the **passive** path only: `**.venv/bin/python3`** or `**python3 -m databoar --help**`, plus **journal/syslog** tails — **no** container smoke on that host. Treat **NFS** exports as passive scan targets if that is the only role.
- **LAB-NODE-03 (Void, `mysqlclient` compile):** `**LAB-NODE-03`** / `**minibt**` aliases (or `**completaoHardwareProfile**` starting with `**LAB-NODE-03-void**`) force `**--skip-engine-import**` and log `**xbps-install**` hints; keep **MySQL/MariaDB** connector and **heavy DB** work on **LAB-NODE-02** and **LAB-NODE-01**. If `**uv sync`** still fails after native devel packages, use a **private branch** or **gitignored** `**pyproject`** overlay **on that host only** — do **not** strip database extras from the **canonical** tracked `**pyproject.toml`** in Git.
- **Skip-on-failure:** the orchestrator **continues** other hosts after **SSH probe** failure, **repo directory** health failure, or **LAB-NODE-04** passive-base failure — each emits `**skip-on-failure`** lines in `**docs/private/homelab/reports/**`.
- **Kubernetes:** not part of this hardware-first completão pass; schedule separately when cluster capacity is available.

## Recommended slice order (one host at a time)

1. **Target ref (recommended for comparable runs):** set `**completaoTargetRef`** (e.g. `**origin/main**` or `**vX.Y.Z**`) and/or `**-LabGitRef**` on `**lab-completao-orchestrate.ps1**`; use `**-SkipGitPullOnInventoryRefresh**` when pinning a **tag**. Optional: `**lab-op-repo-status.ps1`** (inspect) then `**lab-op-git-align-main.ps1**`, `**lab-op-git-ensure-ref.ps1**`, or `**git pull --ff-only**` when you accept **destructive** reset or fast-forward on LAB clones.
2. **Host smoke:** `**lab-completao-orchestrate.ps1`** (or `**lab-completao-host-smoke.sh**` over SSH) until `**MISSING_SCRIPT**` is gone and, for **native** hosts, `**import core.engine`** succeeds. **Container-only** hosts (manifest `**completaoEngineMode`:** `**container`** or `**completaoSkipEngineImport`:** `**true`**) **skip** bare-metal import; validate **Docker/Podman/Swarm** + `**completaoHealthUrl`** instead.
3. **FS `/var/log`:** copy `**config.lab-fs-varlog.example.yaml`**, run `**uv run python main.py --config …**` **on that Linux host** (not from Windows unless paths are mounted).
4. **FS home tree:** same with `**config.lab-fs-home-user.example.yaml`** (adjust the `/home/user/...` path to your lab user if needed).
5. **CLI completão** from the dev PC with a **private** YAML (DBs on a hub + synthetic FS under the repo) — see `**docs/ops/LAB_EXTERNAL_CONNECTIVITY_EVAL.md`** and private `**config.complete-eval.yaml**` pattern.
6. **API / web:** start `**main.py --web`** on a host; `**curl http://<host>:8088/health**` from another LAN machine; then browser. Add `**completaoHealthUrl**` to the manifest for orchestrate to probe from Windows.

## Automation boundary vs assistant-led remediation

- **Built-in scripts** (`lab-completao-orchestrate`, host-smoke) **do not** by themselves open **firewalls** or relax **LSM**/**integrity** tools — they **probe** and **log**.
- When the operator asks for **completão** and wants tests **unblocked**, the assistant **may apply** **narrow**, **lab-op-scoped**, **least-privilege** fixes (packages, ports, `**ufw`**/**nft**, UniFi via `**LAB-ROUTER-01.ps1`** when keys exist, container paths, NFS/SMB/SSHFS mounts per product support) per `**lab-completao-workflow.mdc**`. **Escalate** to the operator before **broad** or **irreversible** hardening changes.
- **Production readiness** stays **iterative**: repeat completão, file issues, patch code/docs, re-run.

## Automation reuse and documented learnings

- **Encode repeat work:** When a completão step is **repeatable**, add or extend `**scripts/`**, **Ansible** under `**ops/automation/ansible/`**, or **manifest** fields — hub: **[TOKEN_AWARE_SCRIPTS_HUB.md](TOKEN_AWARE_SCRIPTS_HUB.md)**; policy: `**lab-completao-workflow.mdc`** (*Automation reuse + documented learnings*).
- **Git A/B on the Windows dev clone (timed):** **`scripts/benchmark-ab.ps1`** creates **`benchmark_runs/`**, guards a dirty tree (**`-AutoStash`** / **`-AllowDirty`**), checks out a legacy **tag** then restores your saved **branch/HEAD**, runs **`lab-completao-orchestrate.ps1`** twice with **`Measure-Command`**, copies recent **`docs/private/homelab/reports/`** files per round, and writes **`benchmark_runs/times.txt`**. Lighter ref-only harness without local checkout: **`scripts/run-benchmark.ps1`**.
- **Capture signals in private session notes** (`docs/private/homelab/`, template `**COMPLETAO_SESSION_TEMPLATE.pt_BR.md*`*): **timeouts**, **wall-clock** duration, **unexpected slowness**, **FP/FN** vs **known synthetic** ground truth (report vs expected), **confidence** on **real** paths (e.g. system log trees, home-directory samples), **latency** over **public APIs** / **SSH** / **low-resource** lab hosts vs faster machines, and any **default**/**doc** mismatch. These feed `**PLANS_TODO.md`** / **issues** — **no** raw PII in public Git.

## Quick start

1. For hosts where you run the **product on bare metal**, ensure the repo clone and `**uv`** (often `**~/.local/bin/uv**` — `**lab-completao-host-smoke.sh**` prepends that to `**PATH**`); run `**uv sync**` and `**uv sync --extra nosql**` if Mongo targets are in your YAML (and [TECH_GUIDE.md](../TECH_GUIDE.md) extras for compressed/shares as needed). For **container-only** hosts (Swarm manager, Podman-only, etc.), set `**completaoEngineMode`:** `**container`** (or `**completaoSkipEngineImport`:** `**true`**) and rely on **HTTP** / compose / stack checks — do **not** assume `**uv`** on the host.
2. Optional manifest fields: `**docs/private.example/homelab/lab-op-hosts.manifest.example.json**` (root `**completaoTargetRef**` documented in `**docs/private.example/homelab/README.md**`; per-host `**completaoHealthUrl**`, `**completaoEngineMode**`, `**completaoSkipEngineImport**`).
3. From repo root on Windows: `**.\scripts\lab-completao-orchestrate.ps1 -Privileged**` (assistant-led completão default; omit `**-Privileged**` only if you must avoid privileged probes).
4. Append lessons to the private template (**timeouts**, **FP/FN**, **latency**, **confidence**); link findings to `**PLANS_TODO.md`** / issues when product gaps appear.

### 🚀 Lab completão test strategy (v1.7.3+)

Resilience-focused gates for release-quality completão (synthetic data only in tracked examples; real paths stay in `**docs/private/**`).

#### A. Layer hygiene (pre-flight)

- **Check:** Confirm no Git metadata is baked into runtime roots where the product should ship as an artifact (e.g. container `**/app`** without a nested repo).
- **Command:** `[ ! -d /app/.git ]` — exit code **0** means `**.git` is absent** (expected for image-style trees). Adjust `**/app`** if your compose mount uses a different root.

#### B. Test data matrix

1. **Obvious positives:** `.csv` and `.sql` files with **synthetic** CPFs and credit-card patterns (no real PANs).
2. **False-positive noise:** System logs (e.g. `**/var/log/syslog`**) and binary blobs to exercise noise handling.
3. **Network latency:** NFS volume from `**LAB-NODE-03`** to `**LAB-NODE-04**` with `**tc qdisc**` delay simulation on the path (document the exact `**tc**` recipe in private session notes).

#### C. Performance monitoring

During scans, the agent should watch:

- **Primary Windows dev PC (Win11):** Docker process **RAM** usage on the orchestrating workstation.
- **LAB-NODE-04:** **SoC temperature** and **I/O wait** (critical on low-margin hardware to avoid thermal or SD-card stalls being misread as product defects).

### 🌐 Heterogeneous infrastructure matrix

Canonical **personas** (ENT / PRO / edge / bridge), Ansible entrypoints, and evidence live in **[LAB_OP_HOST_PERSONAS.md](LAB_OP_HOST_PERSONAS.md)** ([pt-BR](LAB_OP_HOST_PERSONAS.pt_BR.md)) — update that page when lab roles shift; keep this matrix as a **quick glance** only.

| Host               | OS                  | Runtime (default intent) | Role in testing |
| ------------------ | ------------------- | -------------------------- | --------------- |
| **Primary dev PC** | Win11/WSL2 (Deb 13) | Docker Desktop             | Central orchestrator and Windows scan (`C:\Users\fabio`). |
| **LAB-NODE-02**       | Zorin OS 18 Pro     | **Docker Swarm + Git**     | **PRO/partner:** local **`uv`**, chord-chart / PII scan (`/home/leitao/documents`), synthetic DBs on Swarm. |
| **LAB-NODE-01**            | LMDE 7              | **Podman**                 | **ENT-like:** container-first validation **without** relying on metal **`uv`** for product truth; share scans. |
| **LAB-NODE-03**        | Void Linux          | **Optional** Podman (often **`.labop-skip-lab-node-01-podman`**) | **Bridge:** **`curl`** / **`completaoHealthUrl`** / light **`--web`** latency; not a second Swarm manager by default. |
| **LAB-NODE-04**           | Debian Trixie       | **None** on metal (NFS / paths as **target**) | **Edge / soup sink:** resilience and I/O-bound paths; optional minimal **`databoar`** CLI to measure “how bad” — see personas doc. |

### 🛠️ Dynamic configuration generation (agent)

The agent should author **temporary `config.yaml`** files (or fragments to merge) from **[TECH_GUIDE.md](../TECH_GUIDE.md)** and **[USAGE.md](../USAGE.md)** — **never** commit real credentials or LAN-only paths to public Git; keep working copies under `**docs/private/`** or paste only synthetic excerpts in the session transcript.

1. **LAB-NODE-01 scenario (Podman / container-only):** build `config.yaml` to scan `**/data`** (bind mount from the LAB-NODE-02 share or another agreed mount); typical injection `podman run … -v /tmp/config.yaml:/app/config.yaml …` (see [DOCKER_SETUP.md](../DOCKER_SETUP.md)).
2. **LAB-NODE-02 scenario (Git / Swarm):** DB mode with **service names** on the overlay; ingestion mode with **synthetic** soups only.

#### Advanced test scenarios

1. **Cross-share scan:** LAB-NODE-01 mounts a share from LAB-NODE-02; SMB/NFS scan as supported (private notes).
2. **Container soup:** volumes on Swarm services (synthetic data).
3. **Podman vs Docker:** parity for rootless (LAB-NODE-01) vs Docker/Swarm on other hosts, same image or `**uv`** aligned to the completão ref.

### 🧠 Stress and heuristic scenarios

1. **Chord-chart challenge (false positives):** Scanning `/home/leitao/documents` on LAB-NODE-02 contains music files. Heuristics must be validated **not** to raise alerts there without real sensitive literals.
2. **Real-world data:** Deep scan of `/home/leitao` (Linux) and `C:\Users\fabio` (Windows) for historical PII-class findings.
3. **Rootless container scan:** On LAB-NODE-01, validate binary behaviour inside Podman with **no** local host Python/`uv` dependencies.

**Path integrity check:** `/home/leitao` and `C:\Users\fabio` are **operator profile paths** used in completão docs and are **excepted** in `tests/test_pii_guard.py` for public maintainer paths; `**/var/log`** matches the tracked template [config.lab-fs-varlog.example.yaml](../private.example/homelab/config.lab-fs-varlog.example.yaml) and the **Test data matrix** (logs) subsection earlier in this runbook.