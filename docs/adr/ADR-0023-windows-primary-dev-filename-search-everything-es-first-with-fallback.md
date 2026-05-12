# ADR 0023: Windows primary dev PC filename search — Everything (`es.exe`) first, capped PowerShell fallback

**Status:** Accepted
**Date:** 2026-04-09

## Context

Contributors and Cursor sessions often need **find files by name or path** on the primary Windows dev workstation. Alternatives:

| Approach | Pros | Cons |
| -------- | ---- | ---- |
| **Voidtools Everything** via **`es.exe`** (CLI) | Fast index, low transcript noise when scoped | Requires Everything service; Windows-only |
| **Cursor `Glob`** | Workspace-native, no install | Can be heavy on huge trees or outside repo |
| **`Get-ChildItem -Recurse`** | No dependency | Slow, high I/O, expensive in tokens if misused |
| **`SemanticSearch` / `Grep`** | Good for content | Wrong tool for filename-only discovery |

The repo already ships **`scripts/es-find.ps1`** as the token-aware wrapper (default **`-MaxCount`**, optional **`-SearchRoot`**, **`-Global`**). A **fallback** was added for machines where **`es.exe`** is not installed.

## Decision

1. **On Windows primary dev PC**, for **filename/path** discovery (not file content), **prefer** **`.\scripts\es-find.ps1`**, which invokes **`es.exe`**, over ad-hoc recursive directory walks.
2. **If `es.exe` is missing** (exit **127**), the same script may be run with **`-FallbackPowerShell`** to run a **capped** `Get-ChildItem`-style search under the default scope (repo root or **`-SearchRoot`**). **Do not** use **`-FallbackPowerShell`** with **`-Regex`** or **`-Global`** (those require the real CLI).
3. **Assistants** follow **`.cursor/rules/everything-es-cli.mdc`** (always applied): try **`es-find`** first; then **`-FallbackPowerShell`** or **`Glob`**; avoid using **SemanticSearch** as a substitute for “find this filename”.
4. **Linux lab-op over SSH** does **not** use **`es.exe`**; use **`find`**, **`fd`**, or **`locate`** on the host.
5. **Operational docs** remain the source for install and IPC troubleshooting: **`docs/ops/EVERYTHING_ES_PRIMARY_WINDOWS_DEV_LAB.md`** (and pt-BR pair). Session keyword **`es-find`** in **`.cursor/rules/session-mode-keywords.mdc`**.

## Consequences

- **Positive:** Predictable, low-token habit for operators and agents; single script to extend (`-ShowCommand` exposes raw **`es`** line).
- **Negative:** Everything must be installed and running on primary Windows dev PC for the fast path; fallback is slower.
- **Watch:** Do not paste long path lists into **public** commits or issues; treat like any filesystem listing (**`private-pii-never-public.mdc`**).

## Amendment (2026-04-23) — pCloud `P:` and huge sync trees

This ADR already preferred **`es-find.ps1`** for **filename** discovery. **Clarification:** on the operator **Windows** workstation, **pCloud** is commonly **`P:\`** with subtrees (**e.g. auto-upload mirrors**) that contain **tens of thousands** of objects.

- **Assistants** must **not** open investigations with unbounded **`Get-ChildItem -Recurse`** from **`P:\`** or other known-massive sync roots.
- **Do** use **`.\scripts\es-find.ps1 -SearchRoot "<narrow folder>" -Query "<pattern>" -MaxCount N`** (Everything index, low **N** unless the operator asked for exhaustive output).
- **Companion rule (always applied):** **`.cursor/rules/windows-pcloud-drive-search-discipline.mdc`**.

## Amendment (2026-04-08) — `Get-ChildItem` is allowed; notify on `es` failure

**`Get-ChildItem`** (including **`-Recurse`** under a **scoped** root) was **never** meant to be “forbidden.” The **default** on Windows for **filename/path** discovery remains **`.\scripts\es-find.ps1`** → **`es.exe`** (or wrappers that already call **`es`**); that default is **not** demoted. **`Get-ChildItem`** is **recovery** when **`es`** / IPC / PATH fails — **assistants tell the operator** in one line what broke, then **`-FallbackPowerShell`**, **`Glob`**, or native **`Get-ChildItem`**. Assistants should **not forget** existing **`scripts/`** wrappers (**token-aware** discipline).

## References

- **`scripts/es-find.ps1`**
- **`.cursor/rules/everything-es-cli.mdc`**, **`.cursor/rules/windows-pcloud-drive-search-discipline.mdc`**, **`.cursor/skills/everything-es-search/SKILL.md`**
- **`docs/ops/EVERYTHING_ES_PRIMARY_WINDOWS_DEV_LAB.md`**
- **`docs/ops/TOKEN_AWARE_SCRIPTS_HUB.md`**
