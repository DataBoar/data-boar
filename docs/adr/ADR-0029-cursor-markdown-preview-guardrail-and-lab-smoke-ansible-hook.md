# ADR 0029 — Cursor Markdown preview guardrail + lab-smoke Ansible hook

## Status

Accepted

## Context

- Operators use **Cursor** on **Windows**; Markdown **Open Preview** sometimes reverted to a **forced vertical split** after settings sync or upgrades (`markdown.preview.openPreviewToTheSide`, `workbench.editor.autoLockGroups`, or keybindings).
- **Lab smoke stack** (`deploy/lab-smoke-stack`) on Linux hubs sometimes failed after **SCP** of `init/` trees because **Docker bind mounts** could not read `docker-entrypoint-initdb.d` (permission denied).

## Decision

1. **Document** canonical user settings and optional keybindings under **`docs/ops/CURSOR_MARKDOWN_PREVIEW_SETTINGS.md`** (+ pt-BR twin).
2. **Automate verification** on the operator PC with **`scripts/check-cursor-markdown-preview-settings.ps1`** (exit codes; not CI on GitHub — paths are local).
3. Add **Cursor rule** **`.cursor/rules/cursor-markdown-preview-guardrail.mdc`** and **skill** **`.cursor/skills/cursor-markdown-preview-settings/SKILL.md`** so assistants do not regress fixes.
4. Add **Ansible playbook** **`ops/automation/ansible/playbooks/lab-smoke-stack-init-perms.yml`** and **`[lab_smoke]`** stub in **`inventory.example.ini`**; reference from **`LAB_SMOKE_MULTI_HOST.md`** (+ pt-BR).

## Consequences

- **Positive:** Reproducible checklist after Cursor updates; lab hubs can fix init perms idempotently over SSH.
- **Negative:** Another small script and docs to maintain; playbook requires a valid inventory (operator-owned).

## Related

- [ADR 0009](ADR-0009-ansible-idempotent-roles-as-single-automation-source.md) — Ansible as automation source.
- [LAB_SMOKE_MULTI_HOST.md](../ops/LAB_SMOKE_MULTI_HOST.md)
