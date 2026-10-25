# PII fresh-clone audit (Windows one-shot)

**Português (Brasil):** [PII_FRESH_CLONE_AUDIT.pt_BR.md](PII_FRESH_CLONE_AUDIT.pt_BR.md)

**Purpose:** Run the same **self-audit** commands as a **Linux `clean-slate`** round (`pii_history_guard.py --full-history` + `test_pii_guard`) on a **fresh** `git clone` under `%TEMP%`, without deleting your main working tree.

**Not:** History rewrite (`git filter-repo`, `scripts/run-pii-history-rewrite.ps1`). See **[PII_PUBLIC_TREE_OPERATOR_GUIDE.md](PII_PUBLIC_TREE_OPERATOR_GUIDE.md)** Part II.

---

## When to use

- Periodic validation that **public `main`** + full history still pass automation (ADR 0020 alignment).
- After editing PII guards, seeds policy, or replacement tables — compare intent to a **known-clean** clone.

---

## Command

```powershell
.\scripts\pii-fresh-clone-audit.ps1
```

Defaults: clones **`main`** with **full history** (required for `--full-history`), runs **`uv sync`**, then:

1. `uv run python scripts/pii_history_guard.py --full-history`
2. `uv run pytest tests/test_pii_guard.py -q`

### Optional switches

| Switch | Meaning |
| ------ | ------- |
| `-KeepClone` | Keep the temp directory under `%TEMP%` (for inspection). |
| `-IncludeTalentGuards` | Also run `tests/test_talent_public_script_placeholders.py` and `tests/test_talent_ps1_tracked_no_inline_pool.py` (see guide Section D). |
| `-SkipUvSync` | Skip `uv sync` (only sensible when reusing a kept clone manually). |
| `-RepoUrl` | Override clone URL (default: public GitHub HTTPS). |
| `-TempCloneName` | Fixed folder name under `%TEMP%` (default: timestamped `data-boar-pii-audit-*`). |

---

## Related flows

| Flow | Script / doc |
| ---- | ------------- |
| Windows **`C:\Users\...`** history grep (narrow) | **`scripts/new-b2-verify.ps1`** |
| Linux destructive reset + re-clone + seeds | **`docs/private.example/scripts/clean-slate.sh.example`** → private **`clean-slate.sh`**; **[PII_PUBLIC_TREE_OPERATOR_GUIDE.md](PII_PUBLIC_TREE_OPERATOR_GUIDE.md)** H.9 |
| Assistant / memory (no simulation) | Same guide **H.10**; **`.cursor/rules/clean-slate-pii-self-audit.mdc`** |
| Session keyword | **`pii-fresh-audit`** in **`.cursor/rules/session-mode-keywords.mdc`** |

---

## Skill

`.cursor/skills/pii-fresh-clone-audit/SKILL.md`
