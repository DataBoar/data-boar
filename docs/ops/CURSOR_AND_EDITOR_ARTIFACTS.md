# Cursor, VS Code, and workspace artifacts (what we track)

**Audience:** maintainers and contributors. **Not** product operator documentation.

This repository intentionally versions **some** editor and automation config under `.cursor/`, `.vscode/`, and `.github/`. Below is the **policy** after a 2026-04 audit: what is safe in `origin`, what stays gitignored, and what must **never** land in public Git.

## Tracked on purpose

| Location | Role | Secret / PII risk |
| -------- | ---- | ----------------- |
| **`.github/`** | CI workflows (`ci.yml`, CodeQL, Semgrep, Slack notify), Dependabot, issue/PR templates | **Low** if Actions use repo/org **Secrets** only in YAML **names**, not values. Pins use commit SHAs where required. |
| **`.cursor/rules/`**, **`.cursor/skills/`** | Cursor agent rules and skills (project policy) | **Low** — must follow the same rules as tracked docs (no real LAN IPs, hostnames, or credentials). |
| **`.cursor/mcp.json`** | MCP server launch (e.g. Docker gateway). May contain **placeholder** paths such as `C:\\Users\\<username>\\...` | **Medium if edited carelessly** — do not replace placeholders with a **real** Windows username or machine-specific paths in the committed file. Prefer local overrides or untracked copies. |
| **`.cursor/settings.json`** | Cursor UI (e.g. Slack plugin enabled) | **Low** — no tokens in repo. |
| **`.cursor/worktrees.json`** | Commands run when creating a **git worktree** (`setup-worktree`). | **Low** — should match the repo’s real bootstrap (**`uv sync`**, not `npm install`, for this Python/`uv` project). |
| **`.vscode/settings.json`** | Shared VS Code/Cursor defaults (non-secret only) | **Low** — see `.gitignore` comment block near `.vscode/`. |
| **`.well-known/appspecific/com.chrome.devtools.json`** | Chrome DevTools **appspecific** file (may be empty). | **Low** — no secrets; optional placeholder for tooling. |

## Gitignored (do not commit)

| Location | Reason |
| -------- | ------ |
| **`.pytest_cache/`**, **`.ruff_cache/`** | Ephemeral tool caches — **never** version. |
| **`.cursor/private/`** | Operator-only material (see root `.gitignore`). |
| **`.mcp.json`** (repo root) | Local MCP server launch (absolute paths, host-specific commands). Distinct from tracked **`.cursor/mcp.json`** placeholders. |
| **`.cursorignore`**, **`.cursorindexingignore`** | Local/editor-specific ignore for AI context (per Cursor docs). |
| **`docs/private/`** | Private notes and stacked private git — not `origin`. |

## If something sensitive appears in `.cursor/` or `.vscode/`

1. **Remove** from the last public commit (revert or `git rm --cached`) and rotate any exposed secret.
2. Put the replacement under **`docs/private/`** (stacked private git) or **local-only** untracked files.
3. Update **this file** if the policy changes.

## Related

- [CURSOR_AGENT_POLICY_HUB.md](CURSOR_AGENT_POLICY_HUB.md) — policy index.
- [PRIVATE_LOCAL_VERSIONING.md](PRIVATE_LOCAL_VERSIONING.md) — private `docs/private/` git workflow.
- Root `AGENTS.md` — agent access to `docs/private/` vs public Git.
