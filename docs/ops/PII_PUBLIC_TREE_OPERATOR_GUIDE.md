# PII public tree — operator guide (canonical)

**Português (Brasil):** [PII_PUBLIC_TREE_OPERATOR_GUIDE.pt_BR.md](PII_PUBLIC_TREE_OPERATOR_GUIDE.pt_BR.md)

**Single source of truth:** This file consolidates the former **`PII_VERIFICATION_RUNBOOK`**, **`PII_DEFINITIVE_REMEDIATION`**, and **`GITHUB_FORK_CLONE_VISIBILITY_AND_OPERATOR_AUDIT`** documents. Those paths remain as **permanent redirects** so links and ADRs stay valid; **edit procedural content only here** to avoid drift.

**Audience:** Maintainer / operator with push access to the canonical repo on GitHub (replace **`OWNER`** below with the org or user that owns the repository — e.g. `OWNER/data-boar`).

**On-demand ritual (HEAD + private seeds, token-aware):** When the team **chooses** to revisit accidental literals without waiting for the next calendar cadence, follow **[PII_REMEDIATION_RITUAL.md](PII_REMEDIATION_RITUAL.md)** ([pt-BR](PII_REMEDIATION_RITUAL.pt_BR.md)) — session keyword **`pii-remediation-ritual`**. It complements Part I below; it does **not** replace the **SAFE** checklist or **`pii-fresh-audit`** for release-grade fresh-clone proof.

---

## 0. Evidence trail (immutable — do not rewrite history)

These ADRs record **decisions and chronology**; they are not duplicated here:

| ADR | Topic |
| --- | ----- |
| [0018](../adr/ADR-0018-pii-anti-recurrence-guardrails-for-tracked-files-and-branch-history.md) | Anti-recurrence guardrails for tracked files and branch history |
| [0019](../adr/ADR-0019-pii-verification-cadence-and-manual-review-gate.md) | Verification cadence and manual review gate |
| [0020](../adr/ADR-0020-ci-full-git-history-pii-gate.md) | CI full-history `pii_history_guard` |

Assistant / Cursor rules: **`.cursor/rules/public-tracked-pii-zero-tolerance.mdc`**.

---

## Part I — Verification cadence (short / mid / long)

Operational runbook for public-repo PII/sensitive-data verification with a short, mid, and long cadence.

## Manual review gate (required)

Before marking any run as SAFE, review the local/private criteria that are intentionally not stored in tracked docs.

- [ ] I reviewed the current local criteria in `docs/private/security_audit/` (that path is **not** in a public clone; bootstrap from [`docs/private.example/security_audit/`](../private.example/security_audit/README.md) or another maintainer channel).
- [ ] I updated local allow/deny seeds (if needed) in private notes/files.
- [ ] I confirmed no new sensitive identifiers should be added to tracked guardrails.

If any item is unchecked, **do not** mark SAFE.

## Scope and intent

- This runbook covers tracked files and Git history in a **fresh clone**.
- It complements guardrails (`new-b2-verify`, `pii_history_guard.py`, `test_pii_guard.py`).
- It does not replace manual classification for contextual terms.
- `new-b2-verify.ps1` is PowerShell-only (best on primary Windows dev PC/Windows). On Linux hosts, use the manual equivalent below.

## 0) Preconditions

Run in a fresh clone:

```powershell
cd C:\temp
if (Test-Path .\teste_operator_fresh) { Remove-Item -Recurse -Force .\teste_operator_fresh }
mkdir teste_operator_fresh | Out-Null
cd .\teste_operator_fresh
git clone git@github.com:OWNER/data-boar.git
cd .\data-boar
git status
```

Expected: clean tree on `main`.

### Linux (lab-op hosts)

```bash
cd /tmp
rm -rf teste_operator_fresh
mkdir -p teste_operator_fresh
cd teste_operator_fresh
git clone git@github.com:OWNER/data-boar.git
cd data-boar
git status
```

Expected: clean tree on `main`.

### Private `security_audit` bundle (missing after clone)

`docs/private/` is **gitignored**; a normal `git clone` does **not** create `PII_LOCAL_SEEDS.txt`. If `grep` or `mapfile` fails with **No such file or directory**, seed the folder first:

```bash
mkdir -p docs/private/security_audit
cp docs/private.example/security_audit/PII_LOCAL_SEEDS.example.txt docs/private/security_audit/PII_LOCAL_SEEDS.txt
# Edit PII_LOCAL_SEEDS.txt with maintainer-approved literals (one per line).
```

```powershell
New-Item -ItemType Directory -Force -Path docs/private/security_audit | Out-Null
Copy-Item docs/private.example/security_audit/PII_LOCAL_SEEDS.example.txt docs/private/security_audit/PII_LOCAL_SEEDS.txt
# Edit PII_LOCAL_SEEDS.txt with maintainer-approved literals (one per line).
```

## 1) Short run (weekly / before sensitive PRs)

```powershell
.\scripts\new-b2-verify.ps1 -TargetUserSegment <USERNAME>
uv run python .\scripts\pii_history_guard.py
uv run pytest tests/test_pii_guard.py -q
# Run the UC-pattern grep from your local/private criteria bundle.
git grep -n -E "\b(192\.168\.[0-9]{1,3}\.[0-9]{1,3}|10\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}|172\.(1[6-9]|2[0-9]|3[0-1])\.[0-9]{1,3}\.[0-9]{1,3})\b" -- scripts docs tests .cursor
git grep -n -E "\b[0-9]{3}\.[0-9]{3}\.[0-9]{3}-[0-9]{2}\b" -- scripts docs tests .cursor
```

Pass condition: no relevant matches + tests pass.

### Linux (`new-b2-verify.ps1` equivalent)

```bash
TARGET_SEGMENT="<USERNAME>"
TARGET_PATH_UPPER="C:\\Users\\${TARGET_SEGMENT}"
TARGET_PATH_LOWER="c:\\users\\${TARGET_SEGMENT}"

git log --all -S "${TARGET_PATH_UPPER}" --oneline
git log --all -S "${TARGET_PATH_LOWER}" --oneline
git grep -n -i -F "${TARGET_PATH_UPPER}" $(git rev-list --all)

uv run python ./scripts/pii_history_guard.py
uv run pytest tests/test_pii_guard.py -q
# Run the UC-pattern grep from your local/private criteria bundle.
git grep -n -E "\b(192\.168\.[0-9]{1,3}\.[0-9]{1,3}|10\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}|172\.(1[6-9]|2[0-9]|3[0-1])\.[0-9]{1,3}\.[0-9]{1,3})\b" -- scripts docs tests .cursor
git grep -n -E "\b[0-9]{3}\.[0-9]{3}\.[0-9]{3}-[0-9]{2}\b" -- scripts docs tests .cursor
```

## 2) Mid run (monthly)

```powershell
git grep -n -E "linkedin\.com/in/" -- . ":(exclude)docs/private/**"
git grep -n -i -E "c:\\users\\[^\\]+|/home/[^/]+" -- . ":(exclude)docs/private/**"
```

Then classify each hit as:

- acceptable placeholder/test/example; or
- real sensitive exposure requiring immediate fix.

## 3) Long run (quarterly or post-incident)

Run full-history checks for high-risk seeds relevant to your private policy:

```powershell
git log --all -S "C:\Users\<USERNAME>" --oneline
git log --all -S "c:\users\<USERNAME>" --oneline
git log --all -S "/home/<LINUX_USER>" --oneline
git log --all -S "example.com/profile/" --oneline
# Run the UC seed check from your local/private criteria bundle.
# Optional: one pass over every line in docs/private/security_audit/PII_LOCAL_SEEDS.txt:
# .\scripts\run-pii-local-seeds-pickaxe.ps1
```

Keep any person-specific or case-specific seeds in private notes/files only.

## Context-sensitive terms (manual classification)

Some terms may be allowed only in narrow contexts (for example, career portfolio context) and not in legal/medical/private contexts.

When such terms appear:

1. classify by context;
2. document the decision in private notes;
3. fix tracked files if context is not allowed.

## Final SAFE decision

Mark SAFE only if:

- manual review gate is fully checked;
- short run passes;
- mid/long checks show no real exposure;
- contextual terms were manually classified.

If any criterion fails, status is NOT SAFE and requires a surgical remediation + re-run.

---

## A. Preconditions

1. **Backup mindset:** `scripts/run-pii-history-rewrite.ps1` creates a **mirror** under the parent of the repo before rewriting. Keep it until `main` is green and you have re-cloned everywhere.
2. **Tools:** `git`, `git-filter-repo` on PATH, `uv` (for tests), network access to `origin`.
3. **Clean working tree** before a history rewrite: commit or stash all intentional changes.

---

## B. Same-day hygiene (no history rewrite)

Use when you only need to align **current tracked files** and **incremental** guard:

```powershell
cd C:\path\to\data-boar
git fetch origin
git pull origin main
uv sync
uv run pytest tests/test_pii_guard.py tests/test_talent_public_script_placeholders.py tests/test_talent_ps1_tracked_no_inline_pool.py -q
uv run python scripts/pii_history_guard.py
```

**Lab Linux** (no `uv` on PATH): `python3 -m pytest …` if pytest is installed, or install `uv` per project docs.

---

## C. Full history rewrite (destructive on remote after push)

Run **only** after merging guard + replacement rules in `main` (this repo ships `scripts/filter_repo_pii_replacements.txt`).

**Host policy:** Do **not** run this flow on the **L-series** primary dev workstation — use a **designated lab machine** (see **[PRIMARY_WINDOWS_WORKSTATION_PROTECTION.md](PRIMARY_WINDOWS_WORKSTATION_PROTECTION.md)**). The script **refuses** to start unless you set **`DATA_BOAR_ALLOW_DESTRUCTIVE_REPO_OPS=1`** for that shell session (never routine on primary Windows dev PC).

1. **Commit** all intended tracked changes (guards, replacements, docs).
2. On the agreed **non-primary-workstation** host, from PowerShell:

```powershell
$env:DATA_BOAR_ALLOW_DESTRUCTIVE_REPO_OPS = "1"
.\scripts\run-pii-history-rewrite.ps1
```

3. Inspect the reported **`data-boar-history-rewrite-*`** path. If `pytest` and `pii_history_guard --full-history` are green there, you may push (same env var):

```powershell
$env:DATA_BOAR_ALLOW_DESTRUCTIVE_REPO_OPS = "1"
.\scripts\run-pii-history-rewrite.ps1 -Push
```

4. **Immediately after any public force-push:**
   - **Delete stale remote branches** on GitHub that still point at **pre-rewrite** SHAs (or CI / `pii_history_guard --full-history` may still see old blobs).
   - **Every clone** (yours, lab, other collaborators’):

```bash
git fetch origin
git reset --hard origin/main
git fetch --prune
```

5. **Forks (e.g. collaborator):** Owner must **delete the fork** or **re-fork / reset** from current `main`. You cannot fix their object database from upstream.

---

## D. Verification matrix (after push)

| Check | Command |
| ----- | ------- |
| Index + working tree guards | `uv run pytest tests/test_pii_guard.py -q` |
| Talent script placeholders | `uv run pytest tests/test_talent_public_script_placeholders.py tests/test_talent_ps1_tracked_no_inline_pool.py -q` |
| Full history | `uv run python scripts/pii_history_guard.py --full-history` |
| Optional local seeds | Keep **private** seeds in `docs/private/security_audit/PII_LOCAL_SEEDS.txt` (not in Git). Use `git log --all -S "…"` per line only on maintainer machine — see **Part I** above. |

---

## E. Editing replacement rules

- **File:** `scripts/filter_repo_pii_replacements.txt`
- **Format:** `git filter-repo` text replacements; lines starting with `#` are comments; `regex:…==>…` for patterns.
- **After editing:** Run **Section C** again (rewrite + tests) before the next force-push.

---

## F. Related documents

- **Part III** below — fork vs clone visibility.
- **Part I** above — cadence and manual grep.
- [COMMIT_AND_PR.md](COMMIT_AND_PR.md) — no sensitive narratives in PR/commit text.
- [ADR 0020](../adr/ADR-0020-ci-full-git-history-pii-gate.md) — CI full-history gate.
- [COLLABORATION_TEAM.md](../COLLABORATION_TEAM.md) — contributor fork / PR flow ([pt-BR](../COLLABORATION_TEAM.pt_BR.md)).

---

## G. What is already in this repository (engineering closure)

The following are **in `main`** as part of the PII hygiene arc (do not redo unless you change policy):

| Item | Location / behavior |
| ---- | -------------------- |
| Index + path scan | `tests/test_pii_guard.py` — tracked files; allows `docs/private.example/` etc. per prefixes |
| Full-history scan | `scripts/pii_history_guard.py` — skips added lines under `docs/private.example/`; LinkedIn placeholder allows Markdown backtick; SSH regex ignores `user@myserver.example.com` style placeholders |
| Talent CLI placeholders | `tests/test_talent_public_script_placeholders.py`, `tests/test_talent_ps1_tracked_no_inline_pool.py` |
| `filter-repo` rules file | `scripts/filter_repo_pii_replacements.txt` — repaired and valid for `--replace-text` / `--replace-message` |
| Rewrite automation | `scripts/run-pii-history-rewrite.ps1` — optional new rewrite if rules change |
| CI | Workflows run `pii_history_guard --full-history` after tests (see ADR 0020) |
| Ops docs | This guide (single canonical copy); legacy filenames redirect here |

**Not a substitute for:** your private backups, external review (e.g. WRB), or collaborator fork deletion.

---

## H. Operator checklist — do these (assumed required until done)

Run in order where applicable. **No step below is optional** if you want organizational closure, not only “green tests on one laptop.”

### H.1 Full gate on your Windows dev PC (canonical)

```powershell
cd C:\path\to\data-boar
git fetch origin
git pull origin main
.\scripts\check-all.ps1
```

If anything fails, fix or open a scoped PR before declaring release hygiene complete.

### H.2 Confirm CI on GitHub

1. Open `https://github.com/OWNER/data-boar/actions`
2. Confirm the latest workflow run on **`main`** is **green** (all jobs).

### H.3 Lab and secondary clones (machines you control)

On **each** host where `data-boar` is cloned (secondary **lab-op** machines, workstations, or SBCs you control — **real names only** in **`docs/private/homelab/`**, not in public runbooks):

```bash
cd ~/Projects/dev/data-boar   # or your actual path
git fetch origin
git reset --hard origin/main
git fetch --prune
```

Then run the **same** guards as **Section D** using `python3` if `uv` is missing:

```bash
python3 scripts/pii_history_guard.py --full-history
```

Install `uv` on those hosts when practical so `check-all` or equivalent matches Windows.

### H.4 Collaborator fork (known public fork)

1. List forks:

```bash
gh api repos/OWNER/data-boar/forks --paginate --jq '.[] | {owner: .owner.login, full_name, pushed_at, updated_at}'
```

2. **You** message the fork owner: upstream history was rewritten / guards updated; they must **delete the fork** or **re-sync** from current `main` (see **Part III** and [COLLABORATION_TEAM.md](../COLLABORATION_TEAM.md)).

3. You **cannot** delete their fork from your account.

### H.5 GitHub UI sweep (issues, PRs, discussions)

Automation does **not** rewrite issue/PR bodies. **Manually** search the repo on GitHub for patterns you care about (names, paths, case keywords) and redact or open a follow-up issue. Keep **no** sensitive narrative in public issue text going forward ([COMMIT_AND_PR.md](COMMIT_AND_PR.md)).

### H.6 External review (WRB or similar)

- Use **tracked** runbooks and product docs as evidence.
- Do **not** paste dossier content, private seeds, or LAN details into public issues or review forms.

### H.7 Private backups and application state

- Compare **your** offline backups to current behavior **outside** this repo; no assistant or CI can audit disks you do not attach here.

### H.8 Temporary clone directories (hygiene)

- Remove any **temporary** clone dirs you created for fork inspection (e.g. under `%TEMP%` / `/tmp`) when disk hygiene matters.

### H.9 Optional: `clean-slate.sh` on lab (repeat rounds until guards match intent)

**Canonical script (operator private tree):** `docs/private/scripts/clean-slate.sh` with **`docs/private/scripts/README.pt_BR.md`** — install to **`~/clean-slate.sh`** on each Linux lab machine you control. **Tracked template (no secrets):** `docs/private.example/scripts/clean-slate.sh.example` and **`docs/private.example/scripts/README.md`**.

**Naming:** Public GitHub docs use the SSH example alias **`lab-op`**. **Real** machine names on your LAN belong **only** in **`docs/private/`** (see **`PRIVATE_OPERATOR_NOTES.md`** and **`docs/private/homelab/`**), not in tracked product runbooks.

Do **not** use this destructive flow on the **L-series** primary dev workstation — only on **lab hosts** you control for that purpose (**[PRIMARY_WINDOWS_WORKSTATION_PROTECTION.md](PRIMARY_WINDOWS_WORKSTATION_PROTECTION.md)**).

If you use `~/clean-slate.sh` on a Linux lab host:

1. **Before:** ensure **`docs/private/security_audit/PII_LOCAL_SEEDS.txt`** in your workspace is current (or set **`PII_SEEDS_FROM_SCP`** in the environment so the template can **`scp`** canonical seeds from another lab host after clone when the stacked private tree is missing). The script refreshes **`~/.config/PII/PII_LOCAL_SEEDS.txt`** from the workspace path when present.
2. **Run** `~/clean-slate.sh` — it is **destructive** (removes the local `data-boar` tree and re-clones). Only when you accept full re-download and full-history guard cost.
3. **After each run**, from the fresh clone: `python3 scripts/pii_history_guard.py --full-history` (and your usual **`git grep`** / seed checks per **Section D**).
4. **Repeat** on **every** lab host that keeps a clone, and **re-run** whenever **`PII_LOCAL_SEEDS`** or public **`main`** changes, until guards stop failing — one green pass is not always enough.

**Remediation:** Leaks in **public** history require **redaction / filter-repo** and collaborator follow-up (other sections); `clean-slate.sh` validates **fresh** clones, not third-party mirrors.

### H.10 `clean-slate` and assistants: memory hook (self-audit, not simulation)

**Why this subsection exists:** Operators and assistants should **not** confuse (a) **chat narration** (“I ran clean-slate N times”) with (b) a **real** destructive reset + re-clone on disk. The **audit** value of `clean-slate` is: a **known-clean working tree** that matches `origin/main` after a full download — then guards tell you if policy matches reality.

| Question | Answer |
| -------- | ------ |
| **Where is the script?** | **Tracked template:** [`docs/private.example/scripts/clean-slate.sh.example`](../private.example/scripts/clean-slate.sh.example). **Operator copy (private git, not on GitHub):** `docs/private/scripts/clean-slate.sh`. **Narrative:** [`docs/private.example/scripts/README.md`](../private.example/scripts/README.md). |
| **Linux lab usage** | Install to `~/clean-slate.sh` per **H.9**. Ensures `docs/private/security_audit/PII_LOCAL_SEEDS.txt` (or `PII_SEEDS_FROM_SCP`) before run. |
| **Windows equivalent** | **`scripts/pii-fresh-clone-audit.ps1`** — full clone under `%TEMP%`, then **`uv sync`**, **`pii_history_guard.py --full-history`**, **`pytest tests/test_pii_guard.py`** (see **[PII_FRESH_CLONE_AUDIT.md](PII_FRESH_CLONE_AUDIT.md)**). Manual path: empty dir + `git clone` + same commands as **Section D**. Session keyword: **`pii-fresh-audit`**. |
| **What it validates** | **Fresh clone + guards** — good signal that **current** `main` and history (as fetched) pass automation. |
| **What it does *not* do** | Does **not** remove sensitive blobs already pushed (use **Part II** / `run-pii-history-rewrite.ps1`). Does **not** replace CI — CI already runs full-history guard on push. |

**How many times to run:** Repeat on each controlled host after **guard rules**, **seeds**, or **replacement tables** change, until outcomes match **intent** (same spirit as H.9 step 4). That loop is **legitimate**; “simulating” clean-slate in chat without running commands is **not**.

**Assistant default:** When asked whether PII work is “enough,” run **`uv run python scripts/pii_history_guard.py --full-history`** and **`uv run pytest tests/test_pii_guard.py`** on the **actual** workspace when possible; **then** remind the operator that a **fresh clone** (Windows: **`pii-fresh-clone-audit.ps1`** or manual clone; Linux: **`clean-slate.sh`**) is the stronger periodic check for long-lived trees.

---

## I. Cannot be completed without you (hard limits)

| Limit | Why |
| ----- | --- |
| Delete or reset **someone else’s fork** | GitHub permissions |
| **List of all `git clone` users** | Not exposed by GitHub for public repos |
| Prove **Wayback** / search cache / third-party mirror is clean | Out of repo scope |
| **WRB** outcome | Human process |
| Verify **private backup** bytes | Physical / vault access |
| **Any lab host** when offline | Network / power |
| **Legal / HR** narrative | Not in this runbook |

---

## Part III — GitHub fork visibility vs `git clone` visibility

**Purpose:** What GitHub exposes about forks vs anonymous clones; pair with **Part II** for cleanup.

## 1. Forks — **auditable**

GitHub exposes **public forks** of a public repository. You can list them.

**GitHub CLI** (authenticated):

```bash
gh api repos/OWNER/data-boar/forks --paginate --jq '.[] | {owner: .owner.login, full_name, pushed_at, updated_at}'
```

**Browser:** open the repo → **Insights** → **Network** (fork graph), or the **Forks** count on the repo home page.

**Who may hold a full copy:** each fork owner’s GitHub fork object database (until they delete the fork or reset it to match your current `main`).

**Your minimal action:** identify each fork; contact the owner if an outdated fork still carries pre-remediation history; they must delete or re-fork / hard-reset from your `main` — you cannot delete someone else’s fork from your account.

---

## 2. `git clone` — **not** a per-user audit trail on GitHub

For a **public** repository, GitHub **does not** publish:

- a list of GitHub users who ran `git clone`
- IP addresses of anonymous `git clone` operations
- machine-by-machine inventory of clones

**Why:** `git clone` against `https://github.com/...` or `git@github.com:...` does not register a stable “clone registry” you can download as the repo owner.

**What exists for owners (limited):**

- **Insights → Traffic** (repo settings): **clone** counts are **aggregate** (e.g. clones per day), not “who.” Availability depends on GitHub product and your role on the repo.
- **Stars / watchers** show **accounts** that interacted in those ways — not equivalent to clones.

**Who may hold a full copy:** anyone who ever cloned while the old history was on `origin` (any machine worldwide, any mirror). You will **not** get a complete list from GitHub.

**Your minimal action:** treat “unknown clones” as **out of scope** for exhaustive audit; focus on **forks you can see**, **collaborators you know**, and **machines you control** (see §4).

---

## 3. Mirrors and CI

- **Third-party mirrors** (if any) are outside GitHub’s fork list.
- **GitHub Actions** checkouts are ephemeral; they do not replace “who has a local clone.”
- **Long-lived caches** elsewhere (corporate proxy, personal backup) are not visible from GitHub.

---

## 4. Minimal checklist — **only what you must do on your side**

| Step | Action |
| ---- | ------ |
| 1 | Run **`gh api .../forks`** (or use the web UI) and **record** every fork `full_name` and `pushed_at`. |
| 2 | For each fork that still matters: **message the owner** — align with current `main` or delete the fork (you cannot do this for them). |
| 3 | **Inventory your own devices** where you (or people you trust) cloned the repo: dev PC, laptops, lab hosts — **list in your private notes**, not in this public doc. On each: `git fetch origin && git reset --hard origin/main` when you intend to match GitHub. |
| 4 | **Optional:** open **Insights → Traffic** on GitHub (if available) for **trend** awareness only — not a list of cloners. |
| 5 | Accept that **anonymous clones** of a public repo **cannot** be fully audited; risk reduction is **history rewrite on canonical repo + forks you control + known machines**. |

---

## Part III continued — Related within this guide

- **Part II** — force-push, `filter-repo`, clone reset.
- **Part I** — local seeds and grep cadence (private files).
