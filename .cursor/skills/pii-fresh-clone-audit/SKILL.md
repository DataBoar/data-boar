---
name: pii-fresh-clone-audit
description: Run or guide the Windows fresh-clone PII self-audit (pii-fresh-clone-audit.ps1) vs clean-slate.sh on Linux; no chat simulation.
---

# PII fresh-clone audit (skill)

## When to use

- Operator types **`pii-fresh-audit`** (session keyword) or asks for a **clean-slate-style** check on **Windows** without deleting their main working tree.
- After changing **`pii_history_guard.py`**, **`test_pii_guard.py`**, or PII-related rules — validate on a **fresh** public clone.

## What to run

From the **repo root** (operator machine, integrated terminal):

```powershell
.\scripts\pii-fresh-clone-audit.ps1
```

Optional:

- **`-KeepClone`** — leave the temp clone under `%TEMP%` for manual inspection; next run can **`cd`** there and use **`-SkipUvSync`** only if reusing that path intentionally.
- **`-IncludeTalentGuards`** — adds talent placeholder pytest files listed in **`docs/ops/PII_FRESH_CLONE_AUDIT.md`**.

## Guardrails

- **Do not** narrate success without a real terminal run (see **`docs/ops/PII_PUBLIC_TREE_OPERATOR_GUIDE.md`** H.10).
- **primary-dev-workstation-safe:** This script only clones/removes under **`%TEMP%`** — it does **not** delete the canonical working tree. **`clean-slate.sh`** and **`run-pii-history-rewrite.ps1`** are **not** primary Windows dev PC flows — **`docs/ops/PRIMARY_WINDOWS_WORKSTATION_PROTECTION.md`**.
- This script is **not** **`git filter-repo`** / **`run-pii-history-rewrite.ps1`** — it does not rewrite history.
- **Full clone** (not shallow): **`pii_history_guard.py --full-history`** needs complete Git history.

## Linux lab

Use **`docs/private.example/scripts/clean-slate.sh.example`** copied to private **`clean-slate.sh`** for destructive reset + seeds — see guide H.9.

## Related scripts

- **`scripts/new-b2-verify.ps1`** — Windows username path segment checks in history (narrow scope).
- **`scripts/safe-workspace-snapshot.ps1`** — quick guard snapshot on current tree, not a fresh clone.

## References

- **`docs/ops/PII_FRESH_CLONE_AUDIT.md`** (quick start)
- **`docs/ops/PII_PUBLIC_TREE_OPERATOR_GUIDE.md`** H.9–H.10
- **`.cursor/rules/clean-slate-pii-self-audit.mdc`**
