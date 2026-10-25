# PII remediation ritual — public tree (on-demand)

**Português (Brasil):** [PII_REMEDIATION_RITUAL.pt_BR.md](PII_REMEDIATION_RITUAL.pt_BR.md)

This document is the **on-demand ritual** for the **maintainer / operator** when you decide the team must **revisit accidental personal or sensitive literals** in the **tracked** tree and related **Git history** hygiene—not a calendar cron. **Hope is not a plan:** combine **fast guards**, **cheap greps**, **private seed lists**, and **explicit classification** so distraction does not re-open the same class of leak.

**Canonical cadence and SAFE gate:** [PII_PUBLIC_TREE_OPERATOR_GUIDE.md](PII_PUBLIC_TREE_OPERATOR_GUIDE.md) (Parts I–III: short / mid / long runs, fork visibility, history rewrite kit). This ritual **narrows** how to execute a focused pass **without burning tokens** on duplicate work.

**Session keyword (English token):** type **`pii-remediation-ritual`** in chat so the assistant scopes the session to this flow (same convention as **`pii-fresh-audit`**, **`private-stack-sync`**—see **`.cursor/rules/session-mode-keywords.mdc`** and **`AGENTS.md`**).

---

## When to run (judgment, not automation)

Trigger examples:

- After a **dense doc or script** session where real paths, mailbox literals, or third-party names could have slipped in.
- Before a **high-visibility** merge (partner review, press, new collaborator with clone-only access).
- When **`tests/test_pii_guard.py`** or **`pii_history_guard.py`** starts failing on `main`.
- When your **private seed file** changes and you want a **HEAD inventory** before relying on history-only pickaxe.

**Not** a substitute for **`pii-fresh-audit`** (full temp clone + history guards)—use that for **release-grade** confidence on Windows; use **this ritual** for **surgical HEAD work + classification** plus pointers to long-run tools.

---

## Private bundle (source of truth for “what to hunt”)

Bootstrap from **[`docs/private.example/security_audit/README.md`](../private.example/security_audit/README.md)**:

| Artifact | Role |
| -------- | ---- |
| **`docs/private/security_audit/PII_LOCAL_SEEDS.txt`** | One literal per line for **`git grep -F`** (HEAD) and **`git log -S`** (history). Gitignored from GitHub. |
| **`docs/private/security_audit/PII_CONTEXT_DECISIONS_LOG.pt_BR.md`** (or equivalent) | **ACEITÁVEL** vs **VAZAMENTO** per seed/context—prevents re-debating the same hit every session. |

**Rule of thumb:** public **upstream identity** (canonical GitHub org/repo URLs) may be **ACEITÁVEL** as product truth; **mailbox literals**, **home path segments**, **employer-internal URLs**, and **non-public collaborator names** in operator docs are almost always **VAZAMENTO** until moved to placeholders or **`docs/private/`**.

---

## Token-aware execution order (cheapest signal first)

Run from the **repo root** on the machine that holds the clone you are fixing (usually the **primary Windows dev PC** for PowerShell helpers).

1. **Fast CI-aligned guard (seconds):**

   ```bash
   uv run pytest tests/test_pii_guard.py tests/test_talent_ps1_tracked_no_inline_pool.py tests/test_talent_public_script_placeholders.py -q
   ```

   Catches **tracked** literals and patterns defined in code—**not** your full private seed list.

2. **HEAD scan with private seeds (minutes):** For each non-comment line in **`PII_LOCAL_SEEDS.txt`**, run **`git grep -n -F "<line>" HEAD`** (or a small local loop). Classify each hit using the **decisions log**; edit **tracked** files only after classification. **Note:** **`scripts/run-pii-local-seeds-pickaxe.ps1`** runs **`git log --all -S`** per seed (history), not **HEAD**—use it for **pickaxe inventory**, not as the only HEAD check.

3. **History inventory (optional, heavier):** `.\scripts\run-pii-local-seeds-pickaxe.ps1` (add **`-Limit N`** for smoke). Use results to decide whether **`git filter-repo`** / **`scripts/run-pii-history-rewrite.ps1`** is in scope—**never** on the **canonical L-series clone** without the operator’s explicit plan; see **`docs/ops/PRIMARY_WINDOWS_WORKSTATION_PROTECTION.md`**.

4. **Fresh clone + full history gate (release-grade, Windows):** Session keyword **`pii-fresh-audit`** → **`scripts/pii-fresh-clone-audit.ps1`** per **`docs/ops/PII_FRESH_CLONE_AUDIT.md`**.

5. **Username path segment check:** **`scripts/new-b2-verify.ps1`** (optional **`-TargetUserSegment`**) clones to **`%TEMP%`** and, for **non–allowlisted** segments, runs **`git log -S`** plus **batched `git grep`** (UTF-8 temp files, no massive console stdout). Omit the segment or pass **`fabio`** to skip maintainer public-identity path probes per **`PII_CONTEXT_DECISIONS_LOG`**. Use **`-MaxRefsToScan N`** on enormous histories.

**Lab-op:** optional **`ssh`** to a Linux host for **`clean-slate.sh`** / **`pii_history_guard.py`** per **[PII_PUBLIC_TREE_OPERATOR_GUIDE.md](PII_PUBLIC_TREE_OPERATOR_GUIDE.md)** §H—**`docs/private/`** on the lab clone is still the place for **real seeds**; there is **no** substitute for copying **`PII_LOCAL_SEEDS.txt`** onto that host.

---

## Prevent new leaks (defaults the team relies on)

- **Rules:** **`.cursor/rules/public-tracked-pii-zero-tolerance.mdc`**, **`private-pii-never-public.mdc`**, **`clean-slate-pii-self-audit.mdc`**.
- **Contributor policy:** **`CONTRIBUTING.md`** → *Public repo: third-party identifiers and Git history*; talent pool stays in **gitignored** JSON merged at runtime (**`scripts/talent.ps1`**).
- **Pre-merge:** **`.\scripts\check-all.ps1`** (includes guards that apply to the repo); use **`safe-commit`** only as a **snapshot**, not as the full gate.
- **Automation default:** when a mistake class repeats, **add a test or script** (narrow, fast) instead of hoping the next author remembers—see **`AGENTS.md`** (*Proactive anti-regression automation*).

---

## After edits

- Re-run step **1** (pytest guards) at minimum.
- **`git status`**: confirm **`docs/private/`** and **`.env`** are **not** staged.
- Update the **private** decisions log with date + seed + classification so the next ritual is cheaper.

---

## Related links

- [PII_PUBLIC_TREE_OPERATOR_GUIDE.md](PII_PUBLIC_TREE_OPERATOR_GUIDE.md) — cadence, SAFE checklist, Linux **`clean-slate`**, history rewrite warnings.
- [PII_FRESH_CLONE_AUDIT.md](PII_FRESH_CLONE_AUDIT.md) — Windows one-shot fresh clone audit.
- [PRIMARY_WINDOWS_WORKSTATION_PROTECTION.md](PRIMARY_WINDOWS_WORKSTATION_PROTECTION.md) — what **not** to run on the canonical dev clone.
- [TOKEN_AWARE_SCRIPTS_HUB.md](TOKEN_AWARE_SCRIPTS_HUB.md) — prefer repo scripts over ad-hoc shell; deeper narrative in [TOKEN_AWARE_USAGE.md](../plans/TOKEN_AWARE_USAGE.md).
- [CURSOR_AGENT_POLICY_HUB.md](CURSOR_AGENT_POLICY_HUB.md) — quick index for agents (PII row).
