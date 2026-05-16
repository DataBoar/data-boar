# Homelab — real inventory (copy to `docs/private/homelab/`)

After copying this file to **`docs/private/homelab/README.md`**, replace placeholders. **Never commit** `docs/private/`.

## SSH — how the assistant reaches this host

The AI **cannot** open your LAN by itself. **Default:** it runs **`ssh`** from **your** Cursor terminal on the dev PC, using **your** `~/.ssh/config` (Windows OpenSSH, WSL, or Git’s `ssh`).

1. Add a **`Host`** block on the machine where Cursor’s terminal runs (usually **not** in the repo):

   ```sshconfig
   Host lab-op
     HostName <lan-hostname-or-ip>
     User <your-linux-user>
     IdentityFile ~/.ssh/id_ed25519
   ```

   Tracked runbooks use the generic alias **`lab-op`**. **`HostName`** is whatever resolves on your LAN (DNS, mDNS, or RFC1918 IP — **document IPs only under this private tree**, not in public docs). **ed25519** key-based auth is preferred.

1. In **this** private README, record **only** the alias name and role (no secrets):

| Role        | SSH `Host` alias (local to dev PC) | Notes                          |
| ----------- | ---------------------------------- | ------------------------------ |
| Lab server  | `lab-op`                           | OS / role (e.g. Docker, reports) — no vendor serials |

1. Agents **`read_file`** this README and **`AGENT_LAB_ACCESS.md`** when homelab work applies (**`@` optional**). Then use **`ssh lab-op 'command'`** from the integrated terminal.

**Do not** copy **private keys** or **passwords** into `docs/private/`. Use **key-based** login; keep passphrases in your OS keychain / agent.

**SNMP / API tokens (UniFi, etc.):** See **[CREDENTIALS_AND_LAB_SECRETS.md](CREDENTIALS_AND_LAB_SECRETS.md)** ([pt-BR](CREDENTIALS_AND_LAB_SECRETS.pt_BR.md)) — session env vars, vault, gitignored `.env`; never paste into chat. **Extra SNMP targets (switch, Linux):** [SNMP_LAB_TARGETS.md](SNMP_LAB_TARGETS.md) ([pt-BR](SNMP_LAB_TARGETS.pt_BR.md)).

**Future — syslog + detection (when lab hardware is ready):** [OBSERVABILITY_SYSLOG_DETECTION_CHECKLIST.md](OBSERVABILITY_SYSLOG_DETECTION_CHECKLIST.md) ([pt-BR](OBSERVABILITY_SYSLOG_DETECTION_CHECKLIST.pt_BR.md)) — ties to [PLAN_LAB_OP_OBSERVABILITY_STACK.md](../../plans/PLAN_LAB_OP_OBSERVABILITY_STACK.md).

**Operator — AI access, security rationale, blue-team cadence:** [OPERATOR_AI_LAB_ACCESS_AND_BLUE_TEAM_RUNBOOK.md](OPERATOR_AI_LAB_ACCESS_AND_BLUE_TEAM_RUNBOOK.md) ([pt-BR](OPERATOR_AI_LAB_ACCESS_AND_BLUE_TEAM_RUNBOOK.pt_BR.md)) — copy to `docs/private/homelab/` and add site-specific notes (no secrets in git).

**L3 / DHCP / DNS / CyberSecure (UniFi):** [LAB_NETWORK_L3_DHCP_AND_CYBERSEC.md](LAB_NETWORK_L3_DHCP_AND_CYBERSEC.md) ([pt-BR](LAB_NETWORK_L3_DHCP_AND_CYBERSEC.pt_BR.md)) — per-VLAN gateway and DNS intent, honeypot alignment, verification commands; fill the private inventory table only under `docs/private/homelab/`.

**Sequenced lab plan (firewall → access → Loki → Wazuh):** [PLAN_LAB_FIREWALL_ACCESS_AND_OBSERVABILITY.md](../../plans/PLAN_LAB_FIREWALL_ACCESS_AND_OBSERVABILITY.md) ([pt-BR](../../plans/PLAN_LAB_FIREWALL_ACCESS_AND_OBSERVABILITY.pt_BR.md)) in `docs/plans/` — sprint checklist ties to [PLAN_LAB_OP_OBSERVABILITY_STACK.md](../../plans/PLAN_LAB_OP_OBSERVABILITY_STACK.md).

**Shopping list + power (private only):** [LAB_OP_SHOPPING_LIST_COVER_NOTE.md](LAB_OP_SHOPPING_LIST_COVER_NOTE.md) — full list with indicative prices stays under **`docs/private/homelab/LAB_OP_SHOPPING_LIST_AND_POWER.md`** (gitignored). **Urgent:** meter / breaker / panel photos for safe UPS and Enel planning.

**CLI / session habit dumps (private only):** If you keep **`uptime`**, **`w`**, **`last`**, **`lastlog`**, or similar for planning or incident review, store under **`docs/private/homelab/reports/`** (or a dated `.txt`) — not in tracked docs, issues, or PRs (LAN IPs and login patterns). See **`docs/PRIVATE_OPERATOR_NOTES.md`** (EN) / **`.pt_BR.md`**.

### Windows: pCloud as `P:` (optional)

If you sync the same tree to **Linux** (`~/pCloudDrive`) and **Windows** (**`P:`**), note that here (e.g. “reports copy also under `P:\Backups\…`”). The assistant can use **`P:\…`** from the **Cursor terminal on Windows** when pCloud is mounted—still **gitignore** any paths you write in this file.

### Encrypted stacked private repo — container sync (example only)

- [lab-op-vc-container-rsync.example.sh](lab-op-vc-container-rsync.example.sh) — `rsync` template with **`REPLACE_`** placeholders; run only with volumes **unmounted**. Full rollout notes belong under **`docs/private/homelab/`** (e.g. private runbook filename pattern `LAB_OP_VERACRYPT_BW_ROLLOUT*.md`).

## Hosts

**Personas (coverage intent):** after you copy this tree, tag each row mentally with **[LAB_OP_HOST_PERSONAS.md](../../ops/LAB_OP_HOST_PERSONAS.md)** ([pt-BR](../../ops/LAB_OP_HOST_PERSONAS.pt_BR.md)) — e.g. LAB-NODE-01 **ENT-like** (Podman, thin metal), LAB-NODE-02 **PRO** (Swarm + `uv`), Pi **edge soup**, LAB-NODE-03 **bridge** (`completaoHealthUrl`, `curl`, light `--web`). Real aliases stay **only** here, not in public Markdown.

**Completão chat prompt (private long form):** copy **[COMPLETAO_OPERATOR_PROMPT.example.md](COMPLETAO_OPERATOR_PROMPT.example.md)** to **`docs/private/homelab/COMPLETAO_OPERATOR_PROMPT.md`** (or similar) and edit; the **public** taxonomy + thin starters live in **[COMPLETAO_OPERATOR_PROMPT_LIBRARY.md](../../ops/COMPLETAO_OPERATOR_PROMPT_LIBRARY.md)** ([pt-BR](../../ops/COMPLETAO_OPERATOR_PROMPT_LIBRARY.pt_BR.md)); run **`scripts/completao-chat-starter.ps1`** from the product repo root to print a minimal **`completao`** + **`tier:`** block.

**Completão data contracts (optional):** copy **[completao_data_contracts.example.yaml](completao_data_contracts.example.yaml)** to **`docs/private/homelab/completao_data_contracts.yaml`**, fill **`checks`** with **`url_from_env`** + required columns, then set root **`completaoDataContractsPath`** in **`lab-op-hosts.manifest.json`** so **`lab-completao-orchestrate.ps1`** runs **`scripts/lab_completao_data_contract_check.py`** before host smoke — see **[LAB_COMPLETAO_RUNBOOK.md](../../ops/LAB_COMPLETAO_RUNBOOK.md)** (*Data contract preflight*).

| Role | Hostname (LAN)   | OS | Notes |
| ---- | ---------------- | -- | ----- |
| …    | …                | …  | …     |

**Secondary laptop (parallel runner):** If you use a **modern business laptop** (e.g. ThinkPad LAB-NODE-01 Gen 4) for burst Docker/pytest work, record **exact MTM** (e.g. `21HE`), CPU, RAM, disk, and whether it runs **native Linux** or **Win11+WSL2** here—**never** in the public repo.

## Network

- LAB-ROUTER-01-SE: management URL (private), VLAN IDs, …
- UPS: what is plugged into the Attiv (W measured)

**Firewall deep-audit access workflow:** keep host-specific SSH/audit notes in a private file such as `LAB_OP_FIREWALL_REVIEW_<date>.pt_BR.md` (gitignored), then publish only a sanitized summary under `docs/ops/`.

## Security posture (optional but recommended)

Maintain **`LAB_SECURITY_POSTURE.md`** next to this README (copy from a filled `docs/private/homelab/` tree or create empty from scratch): WAN/NAT assumptions, **`sshd -T`** / **UFW** / **Fail2ban** / **`nft list ruleset`** snapshots per host, and a short **improvement backlog**. Tracked index: **`docs/ops/OPERATOR_LAB_DOCUMENT_MAP.md`** (LAB‑PB vs LAB‑OP).

## Inventory “as-of” lines (`LAB_SOFTWARE_INVENTORY`, `OPERATOR_SYSTEM_MAP`)

When you merge **`homelab-host-report`** output into those files, put a **single canonical date** near the **top** of each (or a shared HTML comment in one file you always touch):

- `**Lab inventory as-of:** YYYY-MM-DD`
- or `<!-- lab-op-inventory-as-of: YYYY-MM-DD -->`
- Portuguese: `**Inventário LAB-OP as-of:** YYYY-MM-DD`

**`scripts/lab-completao-inventory-preflight.ps1`** (and **`lab-completao-orchestrate.ps1`** before host smoke) uses that date if present; otherwise **file LastWriteTime**. Default staleness threshold: **15 days** — see **`docs/ops/LAB_COMPLETAO_RUNBOOK.md`** (*Inventory freshness*).

## LAB-OP manifest (`lab-op-hosts.manifest.json`)

Copy **`lab-op-hosts.manifest.example.json`** to **`docs/private/homelab/lab-op-hosts.manifest.json`** and set **`sshHost`** / **`repoPaths`**. Optional **root** key **`completaoTargetRef`** (e.g. **`origin/main`** or a release tag **`vX.Y.Z`**) makes **`lab-completao-orchestrate.ps1`** verify each LAB clone matches that ref **before** host smoke — see **`docs/ops/LAB_COMPLETAO_RUNBOOK.md`** (*Target git ref for reproducible completão*). When pinning a **tag**, pass **`-SkipGitPullOnInventoryRefresh`** on the orchestrator so **`lab-op-sync-and-collect`** does not **`git pull`** clones to **`main`** first during inventory refresh.

## LAB-OP doc language pairs (policy)

- **[I18N_LAB_OP.md](I18N_LAB_OP.md)** · [pt-BR](I18N_LAB_OP.pt_BR.md) — when to use **`File.md`** vs **`File.pt_BR.md`** under your private `homelab/` tree (gitignored).

## Operator re-teach template (EN + pt-BR)

Tracked **placeholders** (copy structure into private `homelab/`, then fill with **your** facts — **never** commit `docs/private/`):

- **[OPERATOR_RETEACH.md](OPERATOR_RETEACH.md)** (English)
- **[OPERATOR_RETEACH.pt_BR.md](OPERATOR_RETEACH.pt_BR.md)** (Brazilian Portuguese)

Your private tree may keep **one** file (e.g. only pt-BR) or **both**; either way, follow **`.cursor/rules/docs-pt-br-locale.mdc`** for Portuguese prose. **`*.pt_BR.md`** under **`docs/private/`** is included in **`tests/test_docs_pt_br_locale.py`** when the folder exists (same idea as markdown lint). Store **`homelab-host-report`** output under **`reports/`** as **`<HOST>_<YYYYMMDD_HHMM>_homelab_host_report.log`** (see **[reports/README.md](reports/README.md)**; include **WSL** under a distinct **HOST** name) for merge into **`LAB_SOFTWARE_INVENTORY.md`**. From Windows: **`scripts/collect-homelab-report-remote.ps1`**. For **POST /scan** + poll **`/status`**, use **`scripts/poll_dashboard_scan.py`** (`--base` / `DATA_BOAR_BASE`), not a hardcoded host script.

## Validation log

- YYYY-MM-DD: host X — §1.1–1.2 pass/fail — …

## Solar (optional)

- Inverter model, app name, Bitwarden item for API ref — or use `solar.md` next to this file.

## ISO inventory (optional)

- Copy or maintain **`iso-inventory.md`** here — list of `.iso` / `.img` under `~/Downloads/iso` (or your path). **Gitignored** if under `docs/private/homelab/` in the repo clone. Optional: `sha256sum` lines for integrity after pCloud sync.
