# Voidtools Everything (`es.exe`) on primary Windows dev PC — filename search (token-aware)

**Português (Brasil):** [EVERYTHING_ES_PRIMARY_WINDOWS_DEV_LAB.pt_BR.md](EVERYTHING_ES_PRIMARY_WINDOWS_DEV_LAB.pt_BR.md)

**Scope:** [Voidtools Everything](https://www.voidtools.com/) indexes file **names and paths** on **Windows**. It does **not** search **inside** file contents by default.

---

## primary Windows dev PC vs lab-op (important)

| Environment | Tool for “find by name/path” |
| ----------- | ---------------------------- |
| **L-series** (primary Windows dev PC) | **`.\scripts\es-find.ps1`** → **`es.exe`** (Everything must be running). |
| **lab-op** (Linux over **SSH**) | **No** `es.exe` — use **`find`**, **`fd`**, or **`locate`** on that host, or path hints from **`lab-op.ps1`** reports. |

Workflows that mention **lab-op** and **file search** usually mean: orchestrate on Linux; use **Everything** only when the operator is on **Windows primary dev PC** searching **local** indexed volumes (including synced drives such as pCloud when indexed).

---

## Install (once per Windows machine)

1. Install **Everything** (GUI/service) so the index stays updated.
2. Install **Everything CLI** so `es.exe` is available, for example:

   `winget install voidtools.Everything.Cli`

3. Ensure **`es`** resolves (`Get-Command es`) or set **`-EsExePath`** on the wrapper. WinGet often places a shim at `%LOCALAPPDATA%\Microsoft\WinGet\Links\es.exe`.

If you see **Everything IPC not found**, start the **Everything** application or service so `es.exe` can connect.

---

## Preferred wrapper (repo)

From the **data-boar** repo root:

```powershell
.\scripts\es-find.ps1 -Help
.\scripts\es-find.ps1 -Query "*.md" -MaxCount 40
.\scripts\es-find.ps1 -Query "PLAN_" -Global -MaxCount 25
.\scripts\es-find.ps1 -Query "foo" -SearchRoot "D:\work" -MaxCount 30
.\scripts\es-find.ps1 -Query "bar" -ShowCommand
```

- **Default scope** = this **repo root** (omit **`-Global`** for normal in-repo filename sweeps when **Glob** would be heavy).
- **`-MaxCount`** caps output — keeps transcripts **token-aware** (default **50** in the script).
- **`-ShowCommand`** prints the exact `es.exe` invocation to copy or extend with **raw** CLI flags.
- **`-FallbackPowerShell`** — if **`es.exe`** is **not** installed, run a **capped** recursive **`Get-ChildItem`** under the same **default scope** (repo root or **`-SearchRoot`**). **Slower** and more I/O than Everything. **Not** used with **`-Regex`** or **`-Global`** (those need the real CLI).

### pCloud (`P:`) and other huge sync trees

On the operator **Windows** workstation, **pCloud** is often **`P:`** (see **`AGENTS.md`** / **`docs/PRIVATE_OPERATOR_NOTES.md`**). Folders such as **`P:\Automatic Upload\...`** can hold **tens of thousands** of files — **default** = **`es-find.ps1`** / **`es.exe`** (Everything index); **`Get-ChildItem`** is **recovery** if **`es`** fails (**notify** IPC/PATH). Avoid **opening** with unbounded **`Get-ChildItem -Recurse`** from those roots alone (slow, noisy, poor token ROI).

**Prefer:**

```powershell
.\scripts\es-find.ps1 -SearchRoot "P:\Automatic Upload" -Query "*.jpg" -MaxCount 20
```

Use the **narrowest** **`-SearchRoot`** the operator confirmed. Operator notes for exact subfolders: **`docs/private/WHAT_TO_SHARE_WITH_AGENT.md`**.

---

## Fallback when `es.exe` is missing (assistants)

**Order:**

1. **`.\scripts\es-find.ps1`** ( **`es.exe`** ) — **default** on **Windows primary dev PC** for **filename/path** search when a **fast index** beats **Glob** on a **large** tree; **do not skip** for ad-hoc **`Get-ChildItem`** when **`es`** should work.
2. If **`es-find`** / **`es.exe`** fails: **notify the operator** briefly (exit code, IPC, PATH) so they can fix **Everything** or install — then same script with **`-FallbackPowerShell`**, or **Cursor `Glob`** for **in-repo** patterns, or a **narrow** **`Get-ChildItem`** path. **`Get-ChildItem`** is **recovery**, not co-equal default.
3. **Do not** use **SemanticSearch** or huge **Grep** runs as a substitute for “find this **filename**” — wrong tool, higher token cost.
4. **Linux SSH (lab-op):** **`find`** / **`fd`**, not **`es`**.

---

## Direct `es.exe` (advanced)

When the wrapper does not expose a flag you need, run **`es.exe -h`** or the same command line printed by **`-ShowCommand`**, then add options per [Voidtools CLI help](https://www.voidtools.com/support/everything/command_line_interface/). Prefer feeding the assistant **short** result lists, not thousands of paths.

---

## Token hygiene (assistants + operators)

- Prefer **`Glob`** / **`Grep`** / **`SemanticSearch`** for work **inside** the **workspace** when they are fast enough.
- Use **`es-find.ps1`** when the task is **by filename/path**, **outside** the repo, or **Glob** would be huge.
- **Never** paste long dumps of real paths into **commits, PRs, or tracked docs**; use **private** notes if you must keep evidence (**`private-pii-never-public.mdc`**).

---

## Guardrails

- **Read-only** with respect to Git and files: it **lists** paths from the index; it does **not** modify the repo.
- **primary-dev-workstation-safe** for the canonical tree: not a destructive repo operation — see **[PRIMARY_WINDOWS_WORKSTATION_PROTECTION.md](PRIMARY_WINDOWS_WORKSTATION_PROTECTION.md)**.

---

## Taxonomy

- **Session keyword (chat):** **`es-find`** — see **`.cursor/rules/session-mode-keywords.mdc`**.
- **Skill:** **`.cursor/skills/everything-es-search/SKILL.md`**
- **Rule:** **`.cursor/rules/everything-es-cli.mdc`**
