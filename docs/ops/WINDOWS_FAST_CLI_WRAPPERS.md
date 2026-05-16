# Windows primary dev PC — fast CLI wrappers (`repo-*` scripts)

**Português (Brasil):** [WINDOWS_FAST_CLI_WRAPPERS.pt_BR.md](WINDOWS_FAST_CLI_WRAPPERS.pt_BR.md)

## Purpose

On the **operator Windows workstation**, assistants should prefer **small repo wrappers** under **`scripts/`** that call **fast native tools** (`rg`, Git **`tail`**, **`bat`**, **`es-find.ps1`**) before falling back to slower PowerShell-only patterns (`Get-ChildItem -Recurse`, unbounded scans). This reduces **toil**, **tokens**, and **wall-clock** time.

**Rule:** **`.cursor/rules/repo-scripts-wrapper-ritual.mdc`** (always) — skim **`TOKEN_AWARE_SCRIPTS_HUB.md`** before reinventing shell.

## Scripts (this slice)

| Script | Prefers | Fallback | Notes |
| ------ | ------- | -------- | ----- |
| **`scripts/repo-grep.ps1`** | **`rg`** (ripgrep), optional **`baregrep.exe`** with **`-PreferBareGrep`** | **`Select-String`** (capped file scan) | Skips unrelated **`grep.exe`** (e.g. FPC toolchain) for recursive safety. Default **`-MaxOutputLines`** caps transcript size. **`baregrep.exe`** is also searched under **`%USERPROFILE%\Downloads`** (portable drop; not winget). |
| **`scripts/repo-tail.ps1`** | Git **`usr\bin\tail.exe`** when present | **`Get-Content -Tail`** | **BareTail** is a **GUI** log viewer — **not** invoked for automation; if **`baretail.exe`** / typo **`baretai.exe`** exists under **`Downloads`**, the script prints a **one-line hint** so the operator knows why the fast path is Git **`tail`**. |
| **`scripts/repo-view.ps1`** | **`bat`** / **`batcat`** with pager off + line range | **`Get-Content -TotalCount`** | Resolves **`bat`** / **`batcat`** on **`PATH`**, WinGet Links, cargo, or **`%USERPROFILE%\Downloads`**. Good for **syntax-highlighted** previews without dumping huge files. |

**Filename / path index (not file contents):** keep using **`scripts/es-find.ps1`** → **`es.exe`** — see **`EVERYTHING_ES_PRIMARY_WINDOWS_DEV_LAB.md`**. There is no **`locate(1)`** on Windows; **`es`** is the fast analogue for **names/paths**.

## Install hints (operator machine)

- **Ripgrep:** `winget install BurntSushi.ripgrep.MSVC` (or another `rg` distribution) so **`repo-grep.ps1`** hits the fast path. Prefer **`rg`** over random **`grep.exe`** installs (toolchain collisions); see script comments.
- **Git for Windows:** ships **`tail.exe`** and **`less.exe`** under **`Program Files\Git\usr\bin\`** — enables **`repo-tail.ps1`** fast path; **`less`** is for **interactive** paging (assistants still cap output with **`repo-view.ps1`** / **`Get-Content`** for transcripts).
- **`bat`:** often via **WinGet** (`sharkdp.bat`) or **cargo**; **`repo-view.ps1`** also checks **`Downloads`** for portable **`bat.exe`** / **`batcat.exe`**.
- **BareGrep / BareTail (Bare Metal Software):** optional **GUI** tools; **`baregrep.exe`** is often a **portable** drop under **`%USERPROFILE%\Downloads`** (not winget). **`repo-grep.ps1`** can invoke it with **`-PreferBareGrep`** (may show a **splash**). **`baretail.exe`** is **not** scripted for tail automation — use **Git `tail.exe`** or **`Get-Content -Tail`**; the wrapper **hints** if it sees a **`Downloads`** copy so nothing feels “forgotten.”

## Assistant behaviour (toil reduction)

1. **Try the wrapper first** when it fits the task (search, tail, preview, filename index).
2. **If the fast tool is missing or fails:** use the **documented fallback** inside the script so the operator still gets an **answer** under time pressure.
3. **Tell the operator** when the failure looks **environmental** (binary missing, **EULA** gate, service stopped, installer needs a click) — **one short line** — so they can fix PATH, install **`rg`**, accept **Sysinternals** terms, start **Everything**, etc. Do **not** silently “forget” the wrapper exists.
4. **Defer deep debugging** when the fallback answer is enough for the moment; loop back to fix flags or script edge cases when calm.

## References

- **`docs/ops/TOKEN_AWARE_SCRIPTS_HUB.md`**
- **`docs/ops/EVERYTHING_ES_PRIMARY_WINDOWS_DEV_LAB.md`**
- **ADR 0023** — Everything / **`es-find.ps1`** first with fallback
- **`.cursor/rules/repo-scripts-wrapper-ritual.mdc`**
