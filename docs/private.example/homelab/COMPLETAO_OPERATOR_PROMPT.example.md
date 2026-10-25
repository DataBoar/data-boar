# Completão — prompt longo do operador (exemplo → copiar para `docs/private/homelab/`)

**Do not commit real paths, hostnames, or secrets.** Copy this file to **`docs/private/homelab/COMPLETAO_OPERATOR_PROMPT.md`** (or similar) and edit. The **public** taxonomy and thin starters live in **`docs/ops/COMPLETAO_OPERATOR_PROMPT_LIBRARY.md`**.

## How to use with taxonomy

1. **Line 1 in chat:** `completao` (English token only).
2. **Line 2:** a **`tier:…`** line from the library (e.g. **`tier:smoke-main`**). For the **full SRE master checklist** (phases 0–4) archived in-repo: **frozen 1.7.3** → **`tier:release-master-v1-7-3`**; **other releases** → **`tier:release-master`** with **`semver:`** / **`tag:`** on the next lines (print via **`.\scripts\completao-chat-starter.ps1 -Tier release-master -ReleaseSemver X.Y.Z`**). Read the resolved **`COMPLETAO_MESTRE_RELEASE_CHECKLIST_PROMPT*.md`** under **[`../../ops/`](../../ops/)** before executing.
3. **Optional:** paste a **short** paragraph below from *this* private file — only when the default assistant behaviour is not enough.

## Replaceable private notes (examples — redact before any public paste)

- **Manifest path:** `docs/private/homelab/lab-op-hosts.manifest.json`
- **Default orchestrator flags I want:** `-Privileged` + optional **`-LabGitRef`** / **`-SkipInventoryPreflight`**
- **Hosts I treat as container-only:** (aliases only — no LAN IPs here)
- **Session notes template:** `COMPLETAO_SESSION_TEMPLATE.pt_BR.md`

## Full narrative block (optional — edit freely in private copy)

```text
(Private operator prose goes here — reminders, host-specific caveats, tmux session names, etc.)
```

When the narrative stabilises, consider folding **durable** rules back into **`LAB_COMPLETAO_RUNBOOK.md`** or **`LAB_OP_HOST_PERSONAS.md`** (public-safe) and keep only **volatile** reminders in this private file.
