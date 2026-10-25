# primary Windows dev PC workstation protection (no destructive repo ops here)

**Português (Brasil):** [PRIMARY_WINDOWS_WORKSTATION_PROTECTION.pt_BR.md](PRIMARY_WINDOWS_WORKSTATION_PROTECTION.pt_BR.md)

**L-series** names a **role**: the operator’s **primary Windows dev PC** where the **canonical** `data-boar` clone, local evidence, and **Git history continuity** must be preserved. It is **not** a hostname to embed in commits or public docs. **Hardware anchor:** the operator’s main dev laptop is typically a ThinkPad **L-series** (or similar); **never** treat **LAB-OP** alignment scripts (`lab-op-git-align-main`, `lab-op-git-ensure-ref` **Reset**, etc.) as applying to **this** machine’s canonical tree — those scripts target **manifest SSH hosts**, not the Cursor workspace on the primary dev PC.

---

## Goals

- **Zero** accidental **full-tree delete**, **clean-slate-class reset**, or **history rewrite** on the machine where day-to-day work lives.
- **Destructive rehearsals** (fresh destructive clone, `git filter-repo`, force-push rehearsals) happen only on **other** lab hosts — or in **isolated directories** — per operator choice, not by default on primary Windows dev PC.

---

## Forbidden on primary Windows dev PC

| Class | Examples |
| ----- | -------- |
| **Destructive clean-slate** | Private **`clean-slate.sh`** / template flows that **`rm -rf`** the main working tree and re-clone (see **PII_PUBLIC_TREE_OPERATOR_GUIDE.md** H.9). Includes **WSL** if it targets the **same canonical tree**. |
| **History rewrite without guard** | **`scripts/run-pii-history-rewrite.ps1`** — blocked unless **`DATA_BOAR_ALLOW_DESTRUCTIVE_REPO_OPS=1`** is set; **do not** set this on primary Windows dev PC for normal work. |
| **Destructive Git on the canonical clone** | **`git reset --hard`**, **`git clean -fdx`**, branch **force** moves, or any operation that **throws away** unmerged work in the **main** working tree on the primary Windows dev PC — use normal **`git pull`**, **`git merge`**, **`git stash`**, or **new branch** instead. (Contrast: **LAB-OP** hosts in **`lab-op-hosts.manifest.json`** may use hard reset / align scripts **on those hosts only** — see **`LAB_COMPLETAO_RUNBOOK.md`** *Blast radius*.) |
| **Fake narratives** | Claiming in chat that a destructive reset “ran” without real commands on an agreed host — see **`clean-slate-pii-self-audit.mdc`**. |

---

## Allowed on primary Windows dev PC (safe for canonical tree)

| Action | Notes |
| ------ | ----- |
| **Guards on current tree** | `uv run python scripts/pii_history_guard.py`, `pytest tests/test_pii_guard.py`, `.\scripts\check-all.ps1` |
| **Temp-only fresh clone audits** | **`scripts/pii-fresh-clone-audit.ps1`**, **`scripts/new-b2-verify.ps1`** — work under **`%TEMP%`** (or explicit temp path); they **do not** delete the main repo folder. |
| **Everything / `es.exe`** | **`scripts/es-find.ps1`** — read-only filename search; **`docs/ops/EVERYTHING_ES_PRIMARY_WINDOWS_DEV_LAB.md`**; session **`es-find`**; **`.cursor/rules/everything-es-cli.mdc`**. |

---

## Where to run destructive-class flows

1. **Designated lab host** (e.g. **lab-op** SSH session): operator runs **`clean-slate`** / rewrite rehearsals there, or uses a **new empty directory** + clone on that machine.
2. **Opt-in env** (rewrite script only): **`DATA_BOAR_ALLOW_DESTRUCTIVE_REPO_OPS=1`** — document in **private** notes that this is **never** enabled on primary Windows dev PC for routine use; only for an explicit, separate machine used for remediation.

---

## Assistant rule

**`.cursor/rules/primary-windows-workstation-protected-no-destructive-repo-ops.mdc`** (`alwaysApply: true`).
