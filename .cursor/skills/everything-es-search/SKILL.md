---
name: everything-es-search
description: Use when finding files by name/path on Windows primary dev PC via voidtools Everything (es.exe); prefer scripts/es-find.ps1 with a capped -MaxCount. On Linux lab-op SSH use find/fd, not es.
---

# Everything (`es.exe`) search — token-aware

## Prefer this skill when

- The operator is on **Windows (primary Windows dev PC)**, **Everything** is installed, and the task is **locate files by name or path** (not file contents).
- **Glob** over the repo would be **too broad**, or the target is **outside** the workspace (another drive, sync folder, large tree).

## Do not use `es` when

- The session is about **lab-op** as **Linux SSH** — run **`find` / `fd` / `locate`** on that host, or use **`lab-op.ps1`** output. **Everything does not run on Linux.**
- You need **content** inside files — use **`Grep`** or **`SemanticSearch`**.

## Default workflow

1. From the **repo root**, run **`.\scripts\es-find.ps1`** with **`-Query`** and keep **`-MaxCount`** small (default **50** unless the user asked for full lists). **This is the default path** — wrapper calls **`es.exe`** (not “ex.exe”; the binary is **`es`** / **`es.exe`**). **Do not** skip it for ad-hoc **`Get-ChildItem`** when **`es`** should work on Windows.
2. **Scope:** omit **`-Global`** to search under the **repo root** only; use **`-Global`** only when the user needs the **full indexed volume** set.
3. Use **`-ShowCommand`** to print the exact **`es.exe`** line — copy it to add **raw** CLI flags not wrapped by the script.
4. Use **`-Help`** for a short usage string embedded in the script.

## If `es` is missing or fails

- Exit code **127** means **`es.exe`** not on **PATH**. Install **voidtools Everything CLI**; ensure **Everything** is running (**IPC**). See **`docs/ops/EVERYTHING_ES_PRIMARY_WINDOWS_DEV_LAB.md`**.
- **Tell the operator** what failed (IPC, PATH, stderr) so they can fix the machine — then fall back.
- **Fallback:** **`.\scripts\es-find.ps1 -Query "..." -FallbackPowerShell`** — capped **PowerShell** filename search under the same default scope (**slower**). **Not** with **`-Regex`** or **`-Global`**.
- **Assistants (Cursor):** if **`es-find`** still cannot run, use **`Glob`** for **in-repo** names, or **`Get-ChildItem`** on a **narrow** root — **`Get-ChildItem` is allowed**; avoid **`SemanticSearch`** as a substitute for “find this **filename**”. Do not “forget” that **`es-find.ps1`** exists for the next similar task.

## primary Windows dev PC (primary dev workstation)

- **`es-find.ps1`** only queries the Everything index — **read-only**, **primary-dev-workstation-safe**.
- Do **not** confuse with **`clean-slate`** / history rewrite — **`docs/ops/PRIMARY_WINDOWS_WORKSTATION_PROTECTION.md`**.

## Token-aware habit

- Prefer **summaries** and **top N** paths in chat; avoid pasting hundreds of lines.
- For **in-repo** work, try **`Glob`** first; switch to **`es-find`** when it saves time or transcript size.

## Session keyword

- Operator may type **`es-find`** — align the session to the wrapper + **`.cursor/rules/everything-es-cli.mdc`**.

## See also

- Rule: **`.cursor/rules/everything-es-cli.mdc`**
- Guide: **`docs/ops/EVERYTHING_ES_PRIMARY_WINDOWS_DEV_LAB.md`**
- Token scripts hub: **`.cursor/skills/token-aware-automation/SKILL.md`**, **`.cursor/rules/check-all-gate.mdc`**
