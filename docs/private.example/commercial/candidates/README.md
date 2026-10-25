# Talent candidates — private layout (not in Git)

**This folder is a template.** Real dossiers, LinkedIn review notes, and **per-candidate learning roadmaps** live under **`docs/private/commercial/candidates/`** on the operator machine only.

## Bootstrap

```powershell
New-Item -ItemType Directory -Force -Path docs/private/commercial/candidates | Out-Null
```

## Suggested files per candidate (example slug `jane-doe`)

- `jane-doe/LEARNING_ROADMAP.md` — copy from **`LEARNING_ROADMAP_TEMPLATE.md`** in this folder; link PRs and optional courses; **never commit**.
- Optional: pair with EN/pt-BR dossier files if you use `scripts/candidate-dossier-scaffold.ps1` / `talent-dossier` helpers.

## Tracked guidance (public repo)

- **[docs/TALENT_POOL_LEARNING_PATHS.md](../../../TALENT_POOL_LEARNING_PATHS.md)** — role **archetypes** and optional cert/course hints; no personal data.

## Policy

- **`docs/PRIVATE_OPERATOR_NOTES.md`** — private tree rules.
- **`.cursor/rules/confidential-commercial-never-tracked.mdc`** — do not commit pricing or client-specific terms; candidate notes are still **personal** — keep them private.
