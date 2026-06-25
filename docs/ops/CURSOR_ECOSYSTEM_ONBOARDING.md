# Cursor — ecosystem onboarding (map, not territory)

> Built off-band (Claude Code + operator Obsidian vault). **Cursor does not know this by default** — paste or `@` this file in fresh chats. For **detail**, read the vault (`~/Projects/dev/obsidian-vault/databoar-commercial/`), starting with **`_NORTE_mapa-do-todo-e-sequencia.md`**, **CHIRP** pattern (HUB/subject → source). Vault recall via its `.cursorrules`.

## Pre-context — two NEW private repos (paste before spinout work)

**Cursor has no session context for these until you clone/read them.** They were scaffolded **off-band** (not by a prior Cursor turn in this repo).

| Repo | Clone | Canonical code today | Verify before migrate |
| ---- | ----- | -------------------- | --------------------- |
| **`FabioLeitao/maestro`** | `gh repo clone FabioLeitao/maestro` (private) | **Still** `data-boar/scripts/maestro*` (this repo — you know this tree) | `gh pr list -R FabioLeitao/maestro` — **2 open PRs** to `main` as of operator onboarding (re-check HEAD; may drift) |
| **`FabioLeitao/license-studio`** | `gh repo clone FabioLeitao/license-studio` (private) | **Spun out 2026-06-25** — was `data-boar/tools/license-studio`; client enforcement stays in `core/licensing/` | `docs/ops/LICENSE_STUDIO_SPINOUT.md` |

**Rules:**

- **Verify everything against HEAD** — descriptions in vault/relay may be stale vs live Git.
- **Do not migrate sensitive code** without operator confirmation and diff.
- **OPSEC:** relay **off-band via operator (copy-paste), zero trace** in public GitHub issues — correct for private repos.

**Operator workstation note:** clones may already exist under `~/Projects/dev/maestro` and `~/Projects/dev/license-studio` — still **`read_file` / `git log`** there; do not assume chat memory.

## The house

**Data Boar** = the org/house + umbrella mascot. The ecosystem = a **bestiary** of products sharing DNA (local · air-gapped · deterministic · TUI "dashBOARd-like" · one golden JWT · zero-LLM-on-data).

## Real repos (what exists TODAY)

| Repo | Visibility | Role |
| ---- | ---------- | ---- |
| **`data-boar`** | public (BSD-3) | Core: PII scanner LGPD/GDPR. **Claude = RO auditor**; **Cursor = writes / PR / merge**. |
| **`data-boar-design-system`** | private | Six TUIs (License Studio, Data Boar, Carrion Crow, Resolute Rikki, Quirky Quati, Maestro) + design language. |
| **`maestro`** | private | E2E orchestrator spinout; **`.ps1` canonical still in `data-boar/scripts/maestro*`**; private repo = governance/CI/ADRs — **re-check open PRs** (`gh pr list -R FabioLeitao/maestro`) |
| **`license-studio`** | private | Ed25519 issuer (Go); **canonical repo** `FabioLeitao/license-studio` (spun out of public tree 2026-06-25) |

**Ten NEW private scaffolds** (seeds, born-with-rigor UMADR+CI; **concept-only — do not pretend they have product code**):

`observant-otter` (chaos) · `mimic-octopus` (service-virt) · `loaded-llama` (corpus) · `burrowing-badger` (secrets) · `tidy-tortoise` (hardening) · `picket-prairie-dog` (egress) · `building-beaver` (SBOM) · `sweeping-squirrel` (retention) · `ptbr-nlp-ner-rag` · `polyglot-file-detector`

## Bestials with locked roles

🐗 Data Boar (PII core) · 🐦‍⬛ Carrion Crow (deterministic RCA) · 🦝 Quirky Quati (context-bundler) · 🦔 Polyglot Pangolin (JVM-upgrade) · 🛡️ Resolute Rikki (autonomy governance) · 🎼 Maestro (orchestrator) · 🔑 License Studio (issuer).

## Contracts Cursor MUST respect

- **Data Boar:** Claude proposes via issue; **you** commit / PR / merge (split-by-subject commits · local `check-all` · green CI · branch protection).
- **UMADR everywhere:** `docs/adr/` (Proposed / Accepted / Duplicate / Obsolete / Quarantined). No `PLAN_*.md` = vaporware.
- **Constitution:** zero-leak **PII/PHI/PCI** · zero-exfil · air-gapped · deterministic > LLM. If it looks sensitive → stop and escalate.
- **OPSEC:** no private secrets in public issues; private coordination = off-band via operator.

## Agent roles (this repo)

Full contract: **`.cursor/rules/agent-roles-executor-vs-auditor.mdc`** · **`CLAUDE.md`**.

## Where to go next

| Need | Read |
| ---- | ---- |
| This map (tracked) | This file |
| Policy hub | **`docs/ops/CURSOR_AGENT_POLICY_HUB.md`** |
| Cold start ladder | **`docs/ops/OPERATOR_AGENT_COLD_START_LADDER.md`** |
| Bird's eye + sequence | Vault **`databoar-commercial/_NORTE_mapa-do-todo-e-sequencia.md`** |
| CHIRP detail on any topic | Vault HUB → linked source (operator-local) |

This brief is the **map**, not the territory.
