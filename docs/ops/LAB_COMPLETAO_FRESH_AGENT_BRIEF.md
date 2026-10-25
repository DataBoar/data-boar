# Lab completão — brief for a fresh Cursor agent (copy-paste)

### 🧠 GOLDEN RULES FOR THE AGENT (v1.7.3)

- **Zero config drift:** Generate ephemeral `config.yaml` files under **`/tmp/`** on each node, based strictly on **`docs/TECH_GUIDE.md`** (canonical technical reference; do not invent keys).
- **Sudo warmth:** Use the **`tmux`** session named **`completao`**, which already has **`sudo -v`** warmed on all nodes where that workflow applies.
- **LAB-NODE-01 restriction:** On host **LAB-NODE-01**, do **not** rely on host **`python`** or **`uv`** — use **`podman run`** only for the product runtime.
- **Data soups:** On **LAB-NODE-02**, bring up the **Swarm** DB stack **before** starting DB-target scans.

**Português (Brasil):** [LAB_COMPLETAO_FRESH_AGENT_BRIEF.pt_BR.md](LAB_COMPLETAO_FRESH_AGENT_BRIEF.pt_BR.md)

**Use when:** You open a **new chat** with **no prior context** and want the assistant to run **completão** the same way as the **repo contracts** (`lab-completao-workflow.mdc`, `LAB_COMPLETAO_RUNBOOK.md`).

**Thin daily use:** **[`COMPLETAO_OPERATOR_PROMPT_LIBRARY.md`](COMPLETAO_OPERATOR_PROMPT_LIBRARY.md)** ([pt-BR](COMPLETAO_OPERATOR_PROMPT_LIBRARY.pt_BR.md)) — line **`completao`** + **`tier:…`** shorthand + **`scripts/completao-chat-starter.ps1`**; keep this file’s blocks **A–E** for full prose when you adjust contracts.

## Blast radius contract (non-negotiable — assistants must not “forget”)

| Where | Never (destructive Git / clean-slate on canonical tree) | Always OK for completão |
| ----- | -------------------------------------------------------- | ------------------------- |
| **Primary Windows dev PC** (ThinkPad **L-series**, this repo in Cursor) | **`git reset --hard`**, **`git clean -fdx`**, **`clean-slate`**, history rewrite on the **main** working copy | **`git pull`**, merge, branch, stash; temp-only audits under **`%TEMP%`** |
| **LAB-OP hosts** in **`lab-op-hosts.manifest.json`** (SSH `repoPaths`) | N/A — these clones are **meant** to track GitHub | **`git fetch` / `pull --ff-only`**, **`lab-op-git-align-main.ps1`**, **`lab-op-git-ensure-ref`**, **`-AlignLabClonesToLabGitRef`**, **`lab-op-repo-status.ps1 -PullFfOnly`** — run **autonomously** from the dev PC scripts; **do not** ask the operator to babysit per-host manual `git` unless SSH fails |
| **Container images** (Docker / Swarm / Podman / Kubernetes) | N/A for primary dev PC Git | **Re-pull** from **Docker Hub** (or configured registry); **`docker pull`**, stack update — **normal** |

Full table: **`LAB_COMPLETAO_RUNBOOK.md`** (*Blast radius*). Primary workstation policy: **`PRIMARY_WINDOWS_WORKSTATION_PROTECTION.md`**.

## Preconditions (operator workstation)

- **Same** Windows dev PC, **same** repo clone, **Cursor integrated terminal** (not a remote “AI datacenter”).
- **`docs/private/homelab/lab-op-hosts.manifest.json`** present (copy from **`docs/private.example/homelab/lab-op-hosts.manifest.example.json`** when needed). For hosts that run Data Boar **only** via **Docker Swarm / Podman** (no bare-metal **`uv`**), set **`completaoEngineMode`:** **`container`** (or **`completaoSkipEngineImport`:** **`true`**) so the smoke does **not** treat missing **`uv`** as a failure — see **`LAB_COMPLETAO_RUNBOOK.md`** (*Container-only lab hosts*).
- **Reproducible LAB revision (recommended):** optional root **`completaoTargetRef`** in the manifest (e.g. **`origin/main`** or **`vX.Y.Z`**) and/or **`-LabGitRef`** on **`lab-completao-orchestrate.ps1`** so host smoke runs against a **known** commit — see **`LAB_COMPLETAO_RUNBOOK.md`** (*Target git ref for reproducible completão*). Use **`-SkipGitPullOnInventoryRefresh`** when pinning a **release tag** so inventory refresh does not **`git pull`** lab clones to **`main`** first.
- **`ssh`** to manifest hosts works from that terminal (keys / `~/.ssh/config`).
- Optional: **narrow sudoers** for **`sudo -n`** on Linux hosts — see **`LAB_OP_PRIVILEGED_COLLECTION.md`** and gitignored **`LABOP_COMPLETÃO_SUDOERS*.md`**.

## Read first (order)

0. **Optional (fresh chat / token-aware):** **[`OPERATOR_AGENT_COLD_START_LADDER.md`](OPERATOR_AGENT_COLD_START_LADDER.md)** ([pt-BR](OPERATOR_AGENT_COLD_START_LADDER.pt_BR.md)) — one-screen ladder + task router; then **[`LAB_OP_HOST_PERSONAS.md`](LAB_OP_HOST_PERSONAS.md)** ([pt-BR](LAB_OP_HOST_PERSONAS.pt_BR.md)) for ENT / PRO / edge / bridge vs Ansible + manifest knobs.
1. **[`AGENTS.md`](../../AGENTS.md)** — Quick index row **Lab completão** and session token **`completao`**.
2. **[`LAB_COMPLETAO_RUNBOOK.md`](LAB_COMPLETAO_RUNBOOK.md)** — contracts, scripts, **slice order**, capability coverage, automation + learnings.
3. **`.cursor/rules/lab-completao-workflow.mdc`** — always-on policy (SSH, **`-Privileged`**, no idle “may I SSH?” prompts, **L-series** protection, doc+code matrix, timeouts/FP-FN notes).

## Session token (English)

Type **`completao`** in chat so the session scope matches **`session-mode-keywords.mdc`**. Put **only** that token on the first line of copy-paste blocks — do not append branch/version text to the same line (session taxonomy).

## Session modes (pick one)

| Mode | Goal | What the **repo scripts** actually run in one go | What still needs **you** (config / services / secrets) |
| ---- | ---- | ----------------------------------------------- | ------------------------------------------------------ |
| **Smoke-only** | LAN + clone + runtime probes + logs | **`lab-completao-orchestrate.ps1 -Privileged`** (includes preflight → may run **`lab-op-sync-and-collect.ps1`**; optional **`completaoTargetRef`** / **`-LabGitRef`** → **`lab-op-git-ensure-ref`** before smoke) | Manifest, SSH, optional **`completaoTargetRef`**, optional **`completaoHealthUrl`**, optional sudoers for **`sudo -n`** |
| **Extended** | Same as smoke + deeper validation (CLI, DBs, API, POC pytest slices) | **No single script** wraps everything — follow **slice order** in **`LAB_COMPLETAO_RUNBOOK.md`** across steps or chats | Private YAML (e.g. **`config.complete-eval.yaml`** pattern), **`lab-smoke-stack`** up where needed, env for API key / JWT / WebAuthn secrets, browser for manual FIDO2 UX |

**Honest scope:** Slice 1 (orchestrator) **does not** by itself deploy full synthetic DBs, run comparative scans, or prove JWT/WebAuthn/browser ceremonies end-to-end. Those are **documented** in **`SMOKE_*.md`**, **`LAB_EXTERNAL_CONNECTIVITY_EVAL.md`**, **`TECH_GUIDE.md`**, **`SECURITY.md`** — assistant-led **steps**, not one magic command.

## Optional checklists

### Smoke-only (minimum useful first slice)

- [ ] Manifest exists and **`sshHost`** / **`repoPaths`** are correct.
- [ ] (Recommended for comparable runs) Set **`completaoTargetRef`** (e.g. **`origin/main`** or release **`vX.Y.Z`**) and/or pass **`-LabGitRef`**; use **`-SkipGitPullOnInventoryRefresh`** when the ref is a **tag**.
- [ ] Container-only hosts have **`completaoEngineMode`:** **`container`** (or **`completaoSkipEngineImport`**) where applicable.
- [ ] (Optional) **`completaoHealthUrl`** per host if **`main.py --web`** is up and reachable from the dev PC.
- [ ] Run **`.\scripts\lab-completao-orchestrate.ps1 -Privileged`** from repo root; read **`docs/private/homelab/reports/`** logs.
- [ ] Append material findings to **`docs/private/homelab/`** (e.g. **`COMPLETAO_SESSION_YYYY-MM-DD.md`** or template **`COMPLETAO_SESSION_TEMPLATE.pt_BR.md`**).

### Extended (multi-step; same or follow-up chats)

- [ ] Smoke-only checklist **done** (or explicitly skipped with reason in private notes).
- [ ] **`lab-op-repo-status.ps1`** if clones may be behind / **`MISSING_SCRIPT`** appeared before.
- [ ] Merge **fresh telemetry** into **`LAB_SOFTWARE_INVENTORY.md`** / **`OPERATOR_SYSTEM_MAP.md`** and bump **`Lab inventory as-of`** / **`<!-- lab-op-inventory-as-of: ... -->`** (see **`docs/private.example/homelab/README.md`**).
- [ ] FS scans on Linux: **`config.lab-fs-*.example.yaml`** copies + **`main.py`** **on-host** per runbook — not from Windows unless paths are mounted.
- [ ] CLI eval from dev PC: **`LAB_EXTERNAL_CONNECTIVITY_EVAL.md`** + **private** YAML (operator-owned paths).
- [ ] API/web: process **`main.py --web`**, **`curl`** / **`completaoHealthUrl`**, browser as needed; **`SECURE_DASHBOARD_AUTH_AND_HTTPS_HOWTO.md`** for TLS/API key posture.
- [ ] On **dev PC**: **`.\scripts\smoke-maturity-assessment-poc.ps1`**, **`.\scripts\smoke-webauthn-json.ps1`** — **pytest subsets**; **not** a substitute for **`check-all.ps1`** or full FIDO2 browser proof.
- [ ] Record **evidence** (timeouts, FP/FN vs synthetic, confidence on real paths) under **`docs/private/homelab/`**; link product gaps to **`PLANS_TODO.md`** / issues when relevant.

## Before the orchestrator (automatic)

**`lab-completao-orchestrate.ps1`** runs **`lab-completao-inventory-preflight.ps1`** first (default **15-day** freshness on private **`LAB_SOFTWARE_INVENTORY.md`** + **`OPERATOR_SYSTEM_MAP.md`**; triggers **`lab-op-sync-and-collect.ps1`** when stale). **Read** those private inventory files when present so host-smoke results align with **documented** roles and versions — **`LAB_COMPLETAO_RUNBOOK.md`** (*Inventory freshness*). Opt out: **`-SkipInventoryPreflight`**.

## First command (default)

From **repository root** on Windows:

```text
.\scripts\lab-completao-orchestrate.ps1 -Privileged
```

Then read **`docs/private/homelab/reports/`** (`completao_*_allhosts.log`, per-host `*_completao_host_smoke.log`).

## Sequential slices (do not skip without cause)

Follow **`LAB_COMPLETAO_RUNBOOK.md`** — **Recommended slice order**, **Capability coverage**, **Automation reuse and documented learnings**. Extended layers (synthetic data, DBs, scans, API key, JWT, WebAuthn, maturity POC, “secure by design” checks) use **smoke runbooks** and **docs** linked from that runbook (e.g. **`SMOKE_WEBAUTHN_JSON.md`**, **`SMOKE_MATURITY_ASSESSMENT_POC.md`**, **`SECURE_DASHBOARD_AUTH_AND_HTTPS_HOWTO.md`**, **`TECH_GUIDE.md`**). **English docs + code** are the behaviour source of truth.

## Do not

- Claim the assistant **cannot** reach the lab via **SSH from this PC** when **`ssh`** works for the operator — see **`homelab-ssh-via-terminal.mdc`**.
- Ask redundant **“may I use SSH / `-Privileged`?”** or **“should I align LAB clones?”** if the operator already asked for **completão** — LAB alignment scripts target **manifest hosts only**, not the primary Windows dev PC — see **`operator-direct-execution.mdc`** and *Blast radius* above.
- Run **`git reset --hard`**, **`clean-slate`**, or history rewrite on the **canonical** clone on the **primary Windows dev PC** — **`PRIMARY_WINDOWS_WORKSTATION_PROTECTION.md`**. (Contrast: LAB **`repoPaths`** may use align scripts — that is **not** the primary dev PC.)
- Put **secrets**, **tokens**, or **LAN identifiers** in **public** GitHub; **private** notes only under **`docs/private/homelab/`**.
- Promise **browser FIDO2**, **full JWT licensing**, or **production-grade** “secure by design” **proof** from scripts alone — document **what ran** vs **`SMOKE_*.md`** / **`SECURITY.md`**.

---

## Copy-paste block A — first slice (smoke + logs)

Use in a **new chat** with **no context** (after preconditions).

**Ref vs version:** **`origin/main`** is the **branch tip** on the remote, not a semver. The **product version** string in **`pyproject.toml`** at that tip is whatever commit **`main`** points to after **`git fetch`** — confirm on the dev PC with **`git show <ref>:pyproject.toml`** (e.g. **`origin/main`**) when you need the exact value. For **routine completão**, treat the **GitHub `main` tip** as “current” unless you pin a **specific release** with **`-LabGitRef vX.Y.Z`** (or **`completaoTargetRef`** in the manifest). A **remote git tag** only applies when it exists; otherwise use **`-LabGitRef origin/main`** to pin LAB clones to the same tip as **`main`**.

**Where to set the ref:** keep **line 1** of the copy-paste block as **`completao` only**. Change **step 1** below (the **`-LabGitRef`** value), not line 1.

**`git` / `gh` sanity (dev PC before completão):** run **`git fetch origin`**, then **`git rev-parse HEAD`** and **`git rev-parse origin/main`** — they should match if your local **`main`** is synced with GitHub. **`gh repo view`** is for metadata (default branch, name); it does not replace **`git`** for commit identity. Uncommitted local edits do not change **`origin/main`**; LAB hosts track the **remote** ref, not your unstaged files.

**Scripts vs GitHub:** after workflow fixes land on **`main`**, run **`git pull`** on this dev PC clone before **`lab-completao-orchestrate.ps1`**, so the orchestrator uses the same **`scripts/*.ps1`** revision as **`origin/main`**. Chat terminal output may **truncate** on long runs; treat **`docs/private/homelab/reports/`** (`lab_op_git_ensure_ref_*.log`, `completao_*`) as ground truth. Each **`lab_op_git_ensure_ref_*.log`** repo block should end with **`LABOP_REF_OK`** or **`LABOP_REF_MISMATCH`** (or **`LABOP_REF_UNRESOLVED`**); if not, read the git/SSH lines above it in the same file.

### Block A — `-LabGitRef` examples (edit step 1 only)

| Goal | Step 1 |
| ---- | ------ |
| LAB clones = **GitHub `main` tip** (default in block below) | `.\scripts\lab-completao-orchestrate.ps1 -Privileged -LabGitRef origin/main` |
| LAB clones = **annotated/lightweight tag** `vX.Y.Z` (e.g. release smoke) | `.\scripts\lab-completao-orchestrate.ps1 -Privileged -LabGitRef vX.Y.Z -SkipGitPullOnInventoryRefresh` |
| No ref check (smoke runs whatever is checked out on LAB) | `.\scripts\lab-completao-orchestrate.ps1 -Privileged` — omit **`-LabGitRef`** (or use **`-SkipLabGitRefCheck`** if the manifest sets **`completaoTargetRef`**) |

For **tag** pins, **`-SkipGitPullOnInventoryRefresh`** avoids **`lab-op-sync-and-collect`** moving LAB clones to latest **`main`** during inventory refresh when markdown is stale — see **`LAB_COMPLETAO_RUNBOOK.md`** (*Target git ref*).

```text
completao

You are in the data-boar repo on my Windows dev PC. Read AGENTS.md (Quick index: Lab completão), then docs/ops/LAB_COMPLETAO_RUNBOOK.md, and follow .cursor/rules/lab-completao-workflow.mdc. Use the integrated terminal — same SSH reachability as my shell.

Session mode: smoke-only (see docs/ops/LAB_COMPLETAO_FRESH_AGENT_BRIEF.md).

LAB git target: match GitHub main — run orchestrator with -LabGitRef origin/main (runs lab-op-git-ensure-ref Check before host smoke). The product version at that ref is whatever **`pyproject.toml`** declares there (confirm with **`git show origin/main:pyproject.toml`**); do not assume a fixed semver unless I pinned a release tag. If ensure-ref fails, LAB clones are not at origin/main (align per LAB_COMPLETAO_RUNBOOK.md).

1) From repo root run: .\scripts\lab-completao-orchestrate.ps1 -Privileged -LabGitRef origin/main
2) Summarize docs/private/homelab/reports/ logs (no secrets in chat if sensitive).
3) Read docs/private/homelab/OPERATOR_SYSTEM_MAP.md and LAB_SOFTWARE_INVENTORY.md when present; reconcile host-smoke with documented roles (container-only manifest hosts are not “missing uv” defects).
4) Document material findings under docs/private/homelab/ (timeouts, latency, FP/FN vs synthetic, confidence on real paths). Do not expand to full CLI/DB/browser/API proof unless I ask in a follow-up.

Do not ask redundant permission for SSH or -Privileged. Do not claim the lab is unreachable from this workspace. Protect my primary Windows dev workstation per docs/ops/PRIMARY_WINDOWS_WORKSTATION_PROTECTION.md.

If something fails, print the actual error and what I must fix (e.g. sudoers, manifest, missing uv on native hosts, LAB clone behind origin/main), then stop — I will fix and ask you to retry. Do not demand bare-metal uv on container-only manifest hosts (completaoEngineMode: container).
```

---

## Copy-paste block B — after slice A (repo alignment check, read-only)

```text
completao follow-up — repo alignment

Same repo and terminal as before. Run .\scripts\lab-op-repo-status.ps1 from repo root. Summarize per-host git state vs origin/main. If MISSING_SCRIPT appeared in past completão logs, point to LAB_COMPLETAO_RUNBOOK.md (align clones). Do not run lab-op-git-align-main.ps1 unless I explicitly ask (destructive on lab clones). Document under docs/private/homelab/.
```

---

## Copy-paste block C — extended: dev-PC pytest POC smokes (no LAN secrets)

```text
completao follow-up — Windows POC pytest smokes

From repo root run: .\scripts\smoke-maturity-assessment-poc.ps1 then .\scripts\smoke-webauthn-json.ps1
Summarize pass/fail. These are pytest subsets per docs/ops/SMOKE_MATURITY_ASSESSMENT_POC.md and SMOKE_WEBAUTHN_JSON.md — not a full browser FIDO2 demo and not a substitute for .\scripts\check-all.ps1.
```

---

## Copy-paste block D — extended: CLI eval pattern (private config required)

```text
completao follow-up — CLI eval

Read docs/ops/LAB_EXTERNAL_CONNECTIVITY_EVAL.md. If I have a private config path under docs/private/homelab/, run uv run python main.py --config <path> only after read_file confirms the YAML exists; redact secrets in chat. If no config exists, stop and list what I must provide. Document findings under docs/private/homelab/.
```

---

## Copy-paste block E — evidence handoff (for documentation / next session)

```text
completao follow-up — evidence pack

Consolidate what we proved this session: commands run, log paths under docs/private/homelab/reports/, inventory as-of dates, pass/fail matrix, gaps vs LAB_COMPLETAO_RUNBOOK.md slice order. Suggest one PLANS_TODO.md row or issue title only if a product gap is confirmed — no public PII.
```

## Will a fresh agent “get it”?

**Mostly yes** for **smoke-only** if the **workspace** is this repo, **`completao`** or block **A** is used, and **preconditions** hold. **Extended** work is **deliberately** multi-step — use blocks **B–E** or new chats so scope stays clear. **No** agent can **invent** SSH keys, **LAB-ROUTER-01** API access, or **sudoers** on hosts — those stay **operator-side**.

## What you can still improve outside this file

- Keep **`manifest.json`** and **private** YAML **up to date** as the lab grows.
- After each completão, **one line** in **`PLANS_TODO.md`** or an issue when a **product gap** is confirmed — closes the loop from **session notes** to **roadmap**.
