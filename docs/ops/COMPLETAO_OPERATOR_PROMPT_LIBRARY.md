# Completão — operator prompt library (taxonomy + thin starters)

**Português (Brasil):** [COMPLETAO_OPERATOR_PROMPT_LIBRARY.pt_BR.md](COMPLETAO_OPERATOR_PROMPT_LIBRARY.pt_BR.md)

## Purpose

Separate **three layers** so you do not paste a wall of text every session:

1. **Session token (English, line 1 only):** **`completao`** — already defined in **`.cursor/rules/session-mode-keywords.mdc`** and **[`AGENTS.md`](../../AGENTS.md)**.
2. **Tier shorthand (line 2):** a **short code** this document defines — tells the assistant which slice and which script line to prefer.
3. **Heavy prose (optional):** the full **copy-paste blocks A–E** in **[`LAB_COMPLETAO_FRESH_AGENT_BRIEF.md`](LAB_COMPLETAO_FRESH_AGENT_BRIEF.md)** — use when you change contracts or need a one-off deviation.

**Automation:** from repo root, **`.\scripts\completao-chat-starter.ps1`** prints a **minimal** starter ( **`completao`** + **`tier:`** lines, sometimes **`semver:`** / **`tag:`** on the next lines) and an optional suggested command. **`.\scripts\completao-chat-starter.ps1 -Help`** lists tiers. For arbitrary releases use **`-Tier release-master -ReleaseSemver 1.7.4`** (optional **`-GitTag`** when it is not **`v` + semver**).

**Private custom prompt:** if your long narrative must mention real paths or preferences, keep a copy under **`docs/private/homelab/`** only — start from **[`../private.example/homelab/COMPLETAO_OPERATOR_PROMPT.example.md`](../private.example/homelab/COMPLETAO_OPERATOR_PROMPT.example.md)** (placeholders, safe to track).

## Tier taxonomy (line 2 after `completao`)

| Tier code | Intent | Assistant should… |
| --------- | ------ | ------------------- |
| **`tier:smoke`** | Default smoke — orchestrator only; LAB clones as checked out unless manifest sets **`completaoTargetRef`** | Run **`lab-completao-orchestrate.ps1 -Privileged`** (no **`-LabGitRef`** unless you add it in line 3). |
| **`tier:smoke-main`** | Repro smoke vs **`origin/main`** | Run **`-LabGitRef origin/main`** ( **`lab-op-git-ensure-ref`** check before smoke). |
| **`tier:smoke-tag`** | Pin to release tag **`vX.Y.Z`** | Run **`-LabGitRef vX.Y.Z -SkipGitPullOnInventoryRefresh`** — see **[`LAB_COMPLETAO_RUNBOOK.md`](LAB_COMPLETAO_RUNBOOK.md)** (*Target git ref*). |
| **`tier:followup-repo`** | After smoke — read-only repo drift | Match **[`LAB_COMPLETAO_FRESH_AGENT_BRIEF.md`](LAB_COMPLETAO_FRESH_AGENT_BRIEF.md)** block **B** ( **`lab-op-repo-status.ps1`** ). |
| **`tier:followup-poc`** | Windows pytest POC slices | Match block **C** ( **`smoke-maturity-assessment-poc.ps1`**, **`smoke-webauthn-json.ps1`** ). |
| **`tier:followup-cli`** | External eval / CLI | Match block **D** + **[`LAB_EXTERNAL_CONNECTIVITY_EVAL.md`](LAB_EXTERNAL_CONNECTIVITY_EVAL.md)**. |
| **`tier:closure-min`** | Minimum closure after a session (more than smoke, less than "full everything") | Complete the 3 key pending items: (1) repeat soup CLI scan on at least one host beyond `lab-node-02`; (2) validate API + dashboard with `GET /health` + `GET /`; (3) consolidate private session note + lessons learned for the run. |
| **`tier:coverage-plus`** | Expanded coverage (ingestions + scanner + API + dashboard + connectors) | Run `smoke` + expand host/target matrix (FS, DB, API, viable connectors), classify failures by severity, and produce a fix plan before rerun. |
| **`tier:evidence`** | Close notes for next session | Match block **E**. |
| **`tier:release-master-v1-7-3`** | **Frozen** shorthand for the **1.7.3** master checklist (same intent as **`release-master`** with **`semver:1.7.3`**) — **read** **[`COMPLETAO_MESTRE_RELEASE_CHECKLIST_PROMPT.md`](COMPLETAO_MESTRE_RELEASE_CHECKLIST_PROMPT.md)** ([pt-BR](COMPLETAO_MESTRE_RELEASE_CHECKLIST_PROMPT.pt_BR.md)) **before** running | Same as **`tier:release-master`** for 1.7.3; kept for stable transcripts |
| **`tier:release-master`** | **Parametric** SRE / release master checklist — **lines 3–4** carry **`semver:X.Y.Z`** and **`tag:vX.Y.Z`** (or non-semver tags such as **`v1.7.2-safe`** via explicit **`tag:`**). **Read** the doc **`completao-chat-starter.ps1` resolves:** prefer **`COMPLETAO_MESTRE_RELEASE_CHECKLIST_PROMPT_<semver>.md`** when that file exists, else fall back to **[`COMPLETAO_MESTRE_RELEASE_CHECKLIST_PROMPT.md`](COMPLETAO_MESTRE_RELEASE_CHECKLIST_PROMPT.md)**; add **`.pt_BR.md`** with the same basename when you archive a new pair | Run **`.\scripts\completao-chat-starter.ps1 -Tier release-master -ReleaseSemver 1.7.4`** (optional **`-GitTag …`**) to print the same lines; align outputs to **private** `homelab/reports/` per policy notes in the doc you open |

**Syntax:** line 2 is exactly one tier line, e.g. **`tier:smoke-main`**. For **`tier:release-master`**, lines **3–4** are **`semver:…`** and **`tag:…`** (printed by **`completao-chat-starter.ps1`**). Optional later lines: extra constraints (**`token-aware`**, **`short`**, one-off flags). Do **not** append branch/version on **line 1** — taxonomy is **`session-mode-keywords.mdc`**.

## Thin starter (example paste)

```text
completao

tier:smoke-main
```

Then run from repo root (assistant or you):

```powershell
.\scripts\lab-completao-orchestrate.ps1 -Privileged -LabGitRef origin/main
```

The assistant still follows **`lab-completao-workflow.mdc`**, reads **`docs/private/homelab/reports/`** when present, and does **not** ask redundant SSH/**`-Privileged`** permission.

## Gradual sequence (v1.7.3) for "real completão"

Use this progression when you want broad fault discovery without always pasting a huge prompt:

1. **Baseline (repro smoke):**

```text
completao

tier:smoke-tag
semver:1.7.3
tag:v1.7.3
```

1. **Minimum closure (3 pending items):**

```text
completao

tier:closure-min
```

1. **Expanded coverage (ingestion/digestion/report/API/dashboard/connectors):**

```text
completao

tier:coverage-plus
token-aware
```

1. **Final rerun:** repeat the corrected slice (usually `tier:coverage-plus`) to confirm fixes and refresh lessons learned.

> **Final rerun "without args"?** It can be args-light when you want the exact same slice, but safest is to keep the tier explicit.

## Executable matrix (completao + args)

| Short trigger | Expected behavior | Learnings captured in the report |
| --- | --- | --- |
| `completao` + `tier:smoke` | Base multi-host smoke via `lab-completao-orchestrate.ps1 -Privileged` | Reachability issues, broken environments, sudoers/dependency gaps |
| `completao` + `tier:smoke-main` | Same smoke with LAB clones aligned to `origin/main` | Reproducibility against canonical branch, repo drift signal |
| `completao` + `tier:smoke-tag` + `tag:vX.Y.Z` | Release-pinned smoke run | Version-specific regressions and release behavior differences |
| `completao` + `tier:closure-min` | Minimum closure: extra-host soup CLI + API/dashboard (`/health` and `/`) + private notes | Cross-host differences, real config/precedence traps, immediate lessons |
| `completao` + `tier:coverage-plus` | Expanded host/target matrix (FS/DB/API/connectors), severity map, rerun plan | Layered failures (script/product/API/connector/docs/dashboard) and improvement priorities |
| `completao` + `tier:followup-repo` | LAB clone drift audit | Baseline trustworthiness for subsequent cycles |
| `completao` + `tier:followup-poc` | POC slices (`smoke-maturity`, `smoke-webauthn`) | Non-functional feature breakage and security-contract drift |
| `completao` + `tier:followup-cli` | CLI/external connectivity-focused evaluation | Ingestion/connectivity gaps and operational UX weaknesses |
| `completao` + `tier:evidence` | Evidence and lessons consolidation in `docs/private/homelab/` | Comparable history across runs and actionable backlog |

**Is it worth the investment?** Yes: lower cognitive load and repeatable completão runs. Practical default: `tier:closure-min` for day-to-day, `tier:coverage-plus` for structural fault hunting.

## Common failure dictionary (prompt engineering)

**Goal:** Before proposing fixes, classify the signal so autonomous assistants (Cursor, Gemini, and similar) **do not** confuse layers. When in doubt, state **both** hypotheses and what evidence would disambiguate.

### Timeout (network / transport)

- **Typical signals:** `Connection timed out`, `ConnectTimeout`, `ETIMEDOUT`, `timed out`, hung commands with no useful stderr until killed, `ssh` appears stuck, `fping` / `ping` loss, `Invoke-WebRequest` timeout, database client waiting on the server until timeout.
- **What it is *not* (usually):** a password prompt, `Permission denied (publickey)`, or a Python traceback pointing at a specific line of **your** repo on the dev PC before remote I/O was attempted.
- **First-response bias:** check **reachability** (host up, correct jump host / VLAN, orchestrator IP not blocked by fail2ban), then **latency** (slow paths may need higher `ConnectTimeout` or tool-specific timeouts), then compare **`lab_result.json`** `connectivity_status` and `performance_metrics` across runs (see **[`LAB_COMPLETAO_RUNBOOK.md`](LAB_COMPLETAO_RUNBOOK.md)** — *Agent-readable run summary*).

### Auth (credentials / identity / trust)

- **Typical signals:** `Permission denied (publickey)`, `Authentication failed`, `Host key verification failed`, `Permission denied (password)` when interactive, HTTP **401** / **403**, `sudo: a password is required` or `sudo: no tty` when you expected `sudo -n`, TLS / certificate trust failures on HTTPS.
- **What it is *not* (usually):** a silent stall with no auth message (timeout family); a `SyntaxError` in a local manifest file before any network call completes meaningfully.
- **First-response bias:** fix **keys** / agent (`ssh-add -l`), **known_hosts**, vault-backed secrets, narrow **sudoers** on the lab host (templates stay **private** — never paste real sudoers into public Git), and manifest **aliases** matching `~/.ssh/config`.

### Parser / contract (code / schema / config shape)

- **Typical signals:** `JSONDecodeError`, YAML scanner errors, `unexpected token`, `SyntaxError`, `jq: parse error`, SQL **invalid column name** after connect succeeds, orchestrator throwing because a **referenced** private contract file is missing or malformed.
- **What it is *not* (usually):** SSH failing immediately with publickey (auth family); a pure network hang with no parser frame.
- **First-response bias:** validate the **artifact** (JSON / YAML / SQL contract), **pin refs** when comparing runs, re-run the smallest failing command in isolation, and combine **`lab_result.json`** diffs with the per-host `*_completao_host_smoke.log` for that `sshHost`.

### Optional chat tag (after `tier:…`)

Example:

```text
failure-class:timeout
```

Use **`timeout`**, **`auth`**, **`parser`**, or **`unknown`** when you want the assistant to **lead** with the matching playbook instead of guessing.

## Interpretation taxonomy (severity by context, not only “green / red”)

**Goal:** Move assistants from “it matched a CPF pattern” to “what does this match *mean* for risk and response?” — closer to how consulting and assurance teams read findings.

1. **Same token, different blast radius:** A national-ID pattern in an **append-only application log** (transient, rotated, least-privilege readers) is **not** the same severity class as the same pattern in a **`users` / `customers` / PII registry` table** export, a **ticket dump**, or a **long-lived backup** shipped off-site. Prefer documenting **location class** (log stream vs authoritative identity store vs marketing spreadsheet vs ticket attachment) before arguing priority.
2. **Volume and retention:** High-cardinality hits in **ephemeral** buffers vs low-cardinality hits in **durable** stores change retention and legal-process posture even when the regex is identical.
3. **Controller vs processor narrative:** When the finding is in **operator-controlled lab fixtures** vs **customer-representative samples**, the remediation story differs (purge lab corpus vs re-scope production connector). Tie back to **[`LAB_COMPLETAO_RUNBOOK.md`](LAB_COMPLETAO_RUNBOOK.md)** capability matrix and **private** session notes — never invent client facts.
4. **Map to exit semantics:** After classifying context, align operational follow-up with **`DATA_BOAR_COMPLETAO_EXIT_v1`** in the runbook (infra vs data-contract vs reserved compliance code **3**) so release gates and **`COMPLETAO_MESTRE_RELEASE_CHECKLIST_PROMPT.md`** stay machine-readable.

## When to use the full blocks A–E

Use **[`LAB_COMPLETAO_FRESH_AGENT_BRIEF.md`](LAB_COMPLETAO_FRESH_AGENT_BRIEF.md)** verbatim blocks when:

- You change **manifest** semantics, **sudoers** paths, or **blast-radius** wording.
- You need a **one-off** instruction (single host, skip inventory, etc.).
- You are onboarding a **human** who does not yet trust the thin tier line.

## Cross-links

- **Master release checklist prompt (1.7.3 archive + parametric tier):** [COMPLETAO_MESTRE_RELEASE_CHECKLIST_PROMPT.md](COMPLETAO_MESTRE_RELEASE_CHECKLIST_PROMPT.md) ([pt-BR](COMPLETAO_MESTRE_RELEASE_CHECKLIST_PROMPT.pt_BR.md)); future semver-specific copies: **`COMPLETAO_MESTRE_RELEASE_CHECKLIST_PROMPT_<semver>.md`** (see **`completao-chat-starter.ps1 -Tier release-master`**)
- **Cold-start ladder:** [OPERATOR_AGENT_COLD_START_LADDER.md](OPERATOR_AGENT_COLD_START_LADDER.md) ([pt-BR](OPERATOR_AGENT_COLD_START_LADDER.pt_BR.md))
- **Personas (ENT / PRO / edge / bridge):** [LAB_OP_HOST_PERSONAS.md](LAB_OP_HOST_PERSONAS.md) ([pt-BR](LAB_OP_HOST_PERSONAS.pt_BR.md))
- **Runbook (includes `lab_result.json`, audit trail, exit code contract):** [LAB_COMPLETAO_RUNBOOK.md](LAB_COMPLETAO_RUNBOOK.md) ([pt-BR](LAB_COMPLETAO_RUNBOOK.pt_BR.md))
- **Script map:** [TOKEN_AWARE_SCRIPTS_HUB.md](TOKEN_AWARE_SCRIPTS_HUB.md) ([pt-BR](TOKEN_AWARE_SCRIPTS_HUB.pt_BR.md))
