# Cursor — ecosystem onboarding (map, not territory)

> Built off-band (Claude Code + operator Obsidian vault). **Cursor does not know this by default** — paste or `@` this file in fresh chats. For **detail**, read the vault (`~/Projects/dev/obsidian-vault/databoar-commercial/`), starting with **`_NORTE_mapa-do-todo-e-sequencia.md`**, **CHIRP** pattern (HUB/subject → source). Vault recall via its `.cursorrules`.

## The house

**Data Boar** = the org/house + umbrella mascot. The ecosystem = a **bestiary** of products sharing DNA (local · air-gapped · deterministic · TUI "dashBOARd-like" · one golden JWT · zero-LLM-on-data).

## Real repos (what exists TODAY)

| Repo | Visibility | Role |
| ---- | ---------- | ---- |
| **`data-boar`** | public (BSD-3) | Core: PII scanner LGPD/GDPR. **Claude = RO auditor**; **Cursor = writes / PR / merge**. |
| **`data-boar-design-system`** | private | Six TUIs (License Studio, Data Boar, Carrion Crow, Resolute Rikki, Quirky Quati, Maestro) + design language. |
| **`maestro`** | private | E2E orchestrator (spinout from data-boar; 2 PRs to reconcile). |
| **`license-studio`** | private | Ed25519 issuer (Go). |

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
