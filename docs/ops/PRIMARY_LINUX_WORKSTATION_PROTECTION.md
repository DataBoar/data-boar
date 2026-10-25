# Primary Linux dev workstation protection (no destructive repo ops here)

**Português (Brasil):** [PRIMARY_LINUX_WORKSTATION_PROTECTION.pt_BR.md](PRIMARY_LINUX_WORKSTATION_PROTECTION.pt_BR.md)

**primary Linux dev workstation** (LMDE 7) is the operator’s **primary dev workstation** **while the former Windows laptop is under Lenovo repair** (hardware failure **2026-06-07**; service reference **E0482B2DMD**). It hosts the **canonical** `data-boar` clone, local evidence, and **Git history continuity**. This is a **temporary** role until the Windows primary returns — see [ADR 0068](../adr/ADR-0068-primary-linux-dev-workstation-temporary.md) (*Reversion when Windows primary returns*).

**Canonical clone path (operator default):** `~/Projects/dev/data-boar` — treat as **`DATA_BOAR_ROOT`**. Do **not** embed real home paths in tracked commits; keep machine-specific paths in **`docs/private/`** only.

**Contrast:** **LAB-OP** manifest SSH hosts are **not** this tree — `git reset --hard`, `lab-op-git-align-main`, and similar **only** apply on those remote **`repoPaths`**, not on the Cursor workspace on the Linux primary dev workstation — see **`docs/ops/LAB_COMPLETAO_RUNBOOK.md`** (*Blast radius*).

When the Windows primary dev workstation returns from repair, resume **`docs/ops/PRIMARY_WINDOWS_WORKSTATION_PROTECTION.md`** and **`.cursor/rules/primary-windows-workstation-protected-no-destructive-repo-ops.mdc`** for that machine; Linux primary may remain a lab-op node but **ceases** to be the sole canonical clone unless the operator explicitly repoints again.

---

## Goals

- **Zero** accidental **full-tree delete**, **clean-slate-class reset**, or **history rewrite** on the machine where day-to-day work lives today.
- **Destructive rehearsals** (fresh destructive clone, `git filter-repo`, force-push rehearsals) happen only on **other** lab hosts — or in **isolated directories under `/tmp/`** — not by default on the Linux primary dev workstation.

---

## Forbidden on the Linux primary dev workstation (canonical clone)

| Class | Examples |
| ----- | -------- |
| **Destructive clean-slate** | Private **`clean-slate.sh`** / template flows that **`rm -rf`** **`DATA_BOAR_ROOT`** and re-clone (see **`docs/ops/PII_PUBLIC_TREE_OPERATOR_GUIDE.md`** H.9). |
| **History rewrite without guard** | **`scripts/run-pii-history-rewrite.ps1`** — blocked unless **`DATA_BOAR_ALLOW_DESTRUCTIVE_REPO_OPS=1`**; **do not** set this on the Linux primary dev workstation for routine work. |
| **Destructive Git on the canonical clone** | **`git reset --hard`**, **`git clean -fdx`**, branch **force** moves, or any operation that **throws away** unmerged work in **`~/Projects/dev/data-boar`** — use **`git pull`**, **`git merge`**, **`git stash`**, or a **new branch** instead. |
| **Fake narratives** | Claiming in chat that a destructive reset “ran” without real commands on an agreed host — see **`clean-slate-pii-self-audit.mdc`**. |

---

## Allowed on the Linux primary dev workstation (safe for canonical tree)

| Action | Notes |
| ------ | ----- |
| **Guards on current tree** | `uv run python scripts/pii_history_guard.py`, `uv run pytest tests/test_pii_guard.py`, **`./scripts/check-all.sh`** |
| **Temp-only fresh clone audits** | Empty dir under **`/tmp/`** + `git clone` + same guards — **never** delete **`DATA_BOAR_ROOT`**. Windows equivalents (`pii-fresh-clone-audit.ps1`) use **`%TEMP%`** only. |
| **Normal Git** | `git fetch`, `git pull`, merge/rebase, stash, feature branches |
| **Pre-commit + PR gate** | One-time **`uv run pre-commit install`** per clone; **`./scripts/check-all.sh`** before every PR (see **`docs/ops/COMMIT_AND_PR.md`**) |
| **Read-only filename / path search** | See **File search (Linux)** below — **not** Voidtools **`es.exe`**. |
| **Remote agent tmux (Cursor + Claude)** | **`./scripts/primary-linux-agent-sessions.sh start`** — worker + `/rc` sessions; **`install-systemd`** + **`loginctl enable-linger`** for boot/logout survival |

---

## File search (Linux — replaces Windows Everything / `es-find`)

On **primary Linux dev workstation**, **`scripts/es-find.ps1`** and **`es.exe`** do **not** apply. Use native tools instead (session keyword **`es-find`** remains **Windows-only** per **`.cursor/rules/session-mode-keywords.mdc`**).

| Tool | Typical use |
| ---- | ----------- |
| **`find`** | Scoped directory walks; last resort when index tools are stale or path is outside `updatedb` coverage. |
| **`fd`** | Fast filename search with sensible defaults; prefer over unbounded **`find`** from `$HOME` or huge sync trees. |
| **`locate` / `plocate`** | Indexed basename/path lookup — **plocate 1.1.23** on primary Linux dev workstation; ensure **`updatedb`** / **`plocate-build`** is current before trusting results. |
| **`git grep`** | Content search in **tracked** files at **`HEAD`** or in history (`git log -S`, pickaxe flows). |
| **`grep -r`** | Content search in working tree or agreed roots (including **`docs/private/`** on disk — redact in public output). |

**Assistants on the Linux primary dev workstation:** prefer **`Glob`** / **`Grep`** inside the repo workspace when fast; use **`find`**, **`fd`**, or **`plocate`** for paths outside the workspace or huge trees. **Do not** tell the operator to install Everything on Linux.

**Cross-reference:** [ADR 0023](../adr/ADR-0023-windows-primary-dev-filename-search-everything-es-first-with-fallback.md) (Windows **`es.exe`** first); [ADR 0068](../adr/ADR-0068-primary-linux-dev-workstation-temporary.md) (Linux primary temporary + Linux tool mapping).

---

## Where to run destructive-class flows

1. **Designated lab host** (SSH **lab-op**): operator runs **`clean-slate`** / rewrite rehearsals there, or uses a **new empty directory** + clone on that machine.
2. **Opt-in env** (rewrite script only): **`DATA_BOAR_ALLOW_DESTRUCTIVE_REPO_OPS=1`** — document in **private** notes that this is **never** enabled on the Linux primary dev workstation for routine use.

---

## Assistant rule

**`.cursor/rules/primary-linux-workstation-protected-no-destructive-repo-ops.mdc`** (`alwaysApply: true`).

**Windows (when primary returns):** **`.cursor/rules/primary-windows-workstation-protected-no-destructive-repo-ops.mdc`** + **`docs/ops/PRIMARY_WINDOWS_WORKSTATION_PROTECTION.md`**.
