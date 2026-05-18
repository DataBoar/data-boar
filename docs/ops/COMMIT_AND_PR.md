# Commit and PR workflow (Agent Review Panel–style)

**Português (Brasil):** [COMMIT_AND_PR.pt_BR.md](COMMIT_AND_PR.pt_BR.md)

When you ask the agent to **preview**, **commit locally**, or **create a PR** with a short description and bullet points, it uses the same flow as the old Cursor “Agent Review Panel”: review changes, optionally select files, then choose commit or open PR in the browser with the form pre-filled. Before pushing, it **fetches** and **rebase-pulls** if the branch is behind the remote so your preferred workflow (linear history, no accidental overwrites) is preserved.

**Optional — noisy IDE or two Git roots:** Run **`.\scripts\safe-workspace-snapshot.ps1`** before Preview when you want a read-only transcript of **`git status`** (repo root and, if present, nested **`docs/private/.git`**) and an optional quick guard-test pass. Use **`-SkipTests`** for status only. This **does not** replace **`check-all`** before merge. Session keyword **`safe-commit`** is defined in **`.cursor/rules/session-mode-keywords.mdc`**.

## What the agent does when you ask

- **“Preview”** or **“Show me what would be committed”**:
- Lists the files that would be included (excluding `audit_results.db`).
- Shows a short diff summary (`git diff --stat`).
- Shows the **proposed commit title and bullet-point body** (from the agent or your message).
- **Does not stage or commit.** You can then say “Commit locally” or “Create PR” to proceed.

- **“Commit locally”** (optionally: “… with message: …”):
- Stages all changed files **except** `audit_results.db`.
- Builds a **short title** and **bullet-point body** from the changes (or uses what you said).
- Requires a matching **Preview stamp** from `-Action Preview` (same branch + file scope), then runs `git commit -m "<title>" -m "<body>"` on the current branch.

- **“Create a PR”** (optionally: “… with description: …” or “… on branch X”):
- If you have **uncommitted changes**: stages (optionally only `-IncludeFiles`), commits with the given title/body.
- If you have **no uncommitted changes but have local commits not yet pushed**: does not create a new commit; uses those existing local commits for the PR.
- **Before pushing:** runs **`git fetch origin`** and, if your branch is **behind** the remote, runs **`git pull --rebase origin <branch>`** so your local commits sit on top of the latest remote (avoids divergent history and failed pushes). If rebase hits conflicts, the script exits and asks you to resolve and run `git rebase --continue` or `git rebase --abort`.
- Uses the same **Preview stamp guard** as Commit (run Preview first); bypass only if intentional via `-SkipPreviewGuard`.
- If you asked for a specific branch (e.g. “on branch `feature/xyz`”), creates or checks out that branch before committing (when there are changes).
- **Pushes** the current branch to `origin` via your existing SSH credentials (all local commits are included).
- **Opens the PR in your default browser** with the title and description **pre-filled**:
- Uses **`gh pr create --title ... --body-file ... --base <default> --web`** so the GitHub “New pull request” form opens with title and body already set; you review and click “Create pull request.”
- If `gh` is not available: opens the GitHub **compare** page so you can create the PR there in your logged-in session.

## Selecting which files to include

You can limit the commit/PR to specific files with **`-IncludeFiles`** (comma-separated or array). The script then stages only those paths (and their children if you pass a directory).

- **Preview first:** run with `-Action Preview` to see all candidate files and the proposed title/body.
- **Then either:** run again with `-Action Commit` or `-Action PR` and, if you want to include only some files, add:

  `-IncludeFiles "path1","path2"` (e.g. `-IncludeFiles "README.md","api/routes.py"`).

## Document progress locally (before PR, release, or publish)

**Why:** Uncommitted work that sits for days becomes **hard to review**, easy to **lose**, and painful to **rebase or merge** when you finally open a PR or ship. Regular **local commits** on a **feature branch** record intent and shrink conflict surfaces.

| Situation                        | What to do                                                                                                                                                                                                                 |
| ---------                        | ----------                                                                                                                                                                                                                 |
| **One important change**         | Commit when it’s complete and gated (e.g. `check-all` or `lint-only` for docs-only).                                                                                                                                       |
| **Many small edits, same theme** | One commit for the whole “train of thought”, *or* a few commits split by sub-theme (`test:`, `docs:`, `feat:`)—each message should read clearly in `git log`.                                                              |
| **Long session ending**          | Prefer committing coherent work rather than a dirty tree; if you must stop mid-theme, use **one** clearly labeled commit (e.g. states what’s left) **on a branch**—agree with the operator; never pollute `main` casually. |
| **Branch alive several days**    | **`git fetch`** and merge or rebase **`origin/main`** into your branch often so you don’t stack a wall of conflicts at PR time.                                                                                            |

This complements **PR batching**: many **local** commits can still ship as **one PR**. Rules: **`.cursor/rules/execution-priority-and-pr-batching.mdc`**, **`.cursor/rules/git-pr-sync-before-advice.mdc`**.

## Multiple local commits, one thematic PR (history-friendly)

**Yes — this is supported and often ideal.** You can make **several small local commits** on the same branch (each with a clear Conventional Commit–style message), **without pushing**, then run **Create PR** once: the push includes **all unpushed commits**, and the PR shows a **readable history** on the branch. That matches **AGENTS.md** (commit grouping + PR batching): keep **coherent slices** separate (`docs` vs `feature` vs `workflow`) when it helps reviewers and `git log`.

- **When to batch:** End of a sprint — group related commits into **one PR** with a summary description, or **split** into two PRs if one slice is risky and another is docs-only.
- **Merge strategy on GitHub:** **Merge commit** preserves per-commit history on `main`; **squash** collapses the PR to one commit — choose per team preference; this repo does not mandate one style in docs.

### Large GitHub issues: keep PRs separable (example: [#86](https://github.com/FabioLeitao/data-boar/issues/86))

**Recommendation:** Work that targets **[#86](https://github.com/FabioLeitao/data-boar/issues/86)** (dashboard **session** / **passwordless** / **RBAC** per [PLAN_DASHBOARD_REPORTS_ACCESS_CONTROL.md](../plans/PLAN_DASHBOARD_REPORTS_ACCESS_CONTROL.md)) should usually live in its **own branch and PR**. Avoid mixing it with unrelated dashboard slices (for example **maturity self-assessment** questionnaire features) in the same PR unless you **explicitly** want one combined review — smaller PRs are easier to revert and match the plan’s phased delivery.

### Thin slices, priority bands, and when to ping the operator

For **assistant- and maintainer-agreed** behaviour when burning down GitHub issues in **small PRs**: read **[THIN_SLICE_AGENT_PRIORITY_HANDOFF.md](THIN_SLICE_AGENT_PRIORITY_HANDOFF.md)** ([pt-BR](THIN_SLICE_AGENT_PRIORITY_HANDOFF.pt_BR.md)). Summary: stay inside the **same priority band** (`P0`→`P3`); if a slice is blocked, **write a resume pointer** and continue **another same-band** item; **do not** start **lower-band** work while **higher-band** items are still actionable without a handoff — **stop and ping the operator** instead.

## Doing it yourself

### Preview: file list vs commit message

**`-Action Preview` without `-Title` / `-Body`** only guarantees an accurate **list of files** and **`git diff --stat`**. The script **does not infer** a commit message from your changes.

- **Before (confusing):** the script used **hardcoded example** defaults (e.g. “Update: security and docs” / CSP bullets) so Preview looked like a real proposal — it was not.
- **Now:** if you omit `-Title`, Preview prints a **yellow NOTE** and shows “(not set)”. You must pass **`-Title`** and usually **`-Body`** for **Commit** or **PR** (Commit **fails** without a title).

### Commands

From the repo root (PowerShell):

```powershell
# Preview only (no commit) – see files; message is NOT auto-generated (see note above)
.\scripts\preview-commit.ps1
# Optional: preview the exact title/body you will use for Commit/PR
.\scripts\commit-or-pr.ps1 -Action Preview -Title "Your title" -Body "Bullet one`nBullet two"

# Commit only (example: FN reduction + commit-or-pr script)
$body = @"

- MEDIUM threshold: sensitivity_detection.medium_confidence_threshold (loader + detector + engine)
- Suggested review: core/suggested_review, SQL persist_low_id_like_for_review, Excel sheet
- commit-or-pr: empty default title; Preview NOTE; PR when already pushed requires -Title
- Docs: SENSITIVITY_DETECTION, USAGE, TECH_GUIDE, PLANS_TODO, COMMIT_AND_PR; detection merge fix in loader

"@
.\scripts\commit-or-pr.ps1 -Action Commit -Title "feat: FN reduction slice + commit-or-pr message clarity" -Body $body

# Create PR on current branch (commit, push, open PR in default browser for approval)
.\scripts\commit-or-pr.ps1 -Action PR -Title "Your short title" -Body "Bullet one`nBullet two"

# Create PR but include only selected files
.\scripts\commit-or-pr.ps1 -Action PR -IncludeFiles "README.md","scripts/commit-or-pr.ps1" -Title "Your title" -Body "Bullets..."

# Create PR on a new or existing branch
.\scripts\commit-or-pr.ps1 -Action PR -Branch "feature/my-change" -Title "Your title" -Body "Bullets..."

# Create PR and run the test suite before pushing (no push if tests fail)
.\scripts\commit-or-pr.ps1 -Action PR -Title "Your title" -Body "Bullets..." -RunTests
# Create PR and include version readiness smoke gate (optional, recommended for all-greens/pre-publish)
.\scripts\commit-or-pr.ps1 -Action PR -Title "Your title" -Body "Bullets..." -RunTests -RunVersionSmoke

# Ensure gh default repository from origin (optional manual preflight)
.\scripts\gh-ensure-default.ps1

# Create PR with body from a file (avoids escaping multi-line body in the shell)
.\scripts\create-pr.ps1 -Title "Your title" -BodyFilePath "path\to\body.txt"
.\scripts\create-pr.ps1 -Title "Your title" -BodyFilePath $env:TEMP\pr-body.txt -RunTests
```

- **Push** uses your normal Git remote and SSH keys. PR **always pushes the current branch to origin** so the central repo (data-boar) has the full progress and history.
- **Browser**: With `gh` installed and authenticated, the PR form opens with title and description filled in; you only need to confirm and click “Create pull request.”

## Which repository to use (data-boar only)

- **`origin`** points to **FabioLeitao/data-boar** — this is the **only** repo you push to and open PRs in. All new work and branding live here.
- A **second remote** (optional), kept for **legacy history and fetch only** — often named with a `*-legacy-and-history-only` suffix pointing at the archived GitHub URL. Do **not** push to it; push is disabled so accidental pushes fail safely. Details: [BRANCH_AND_DOCKER_CLEANUP.md](BRANCH_AND_DOCKER_CLEANUP.md) §7.
- When you open the PR in the browser (compare page or `gh pr create --web`), ensure:
- **Base repository:** `FabioLeitao/data-boar`
- **Base branch:** `main`
- **Compare/head:** your branch (e.g. `2026-03-14-3i1y`) in **data-boar**
- If GitHub suggests “you may need to fork,” it usually means the **base** dropdown is set to another repo (e.g. the old one). Change the base to **data-boar** and base branch to **main** so the PR is “same repo” and no fork is needed.

## Requirements

- **Git** and (for PR) **SSH** or HTTPS push to GitHub.
- **GitHub CLI (`gh`)** and `gh auth login` for the best experience: PR form opens pre-filled in your browser. If `gh` is missing, the script still opens the compare page so you can create the PR manually.
- **`uv` preferred for test parity:** `commit-or-pr.ps1 -RunTests` runs `uv run pytest -v -W error` when `uv` is available (same dependency/interpreter strategy as CI and `check-all`); it falls back to `python -m pytest` only when `uv` is unavailable.
- `commit-or-pr.ps1 -Action PR` now auto-runs a lightweight default-repo check for `gh` (derived from `origin`) to avoid `gh pr checks` / `gh pr create` failures caused by missing `gh` default repository.

## Notes

- The script **respects `.gitignore`**: it uses `git check-ignore` so only non-ignored paths are ever staged or committed (e.g. `audit_results.db`, `*.db-journal`, `.env.local`, reports/heatmaps, `__pycache__`, etc. are never included).
- The agent does **not** have access to your credentials; it runs `git` and `gh` in your environment, so your SSH and `gh auth` are used.

## Commit and PR text: no sensitive third-party narratives

GitHub stores titles and bodies for the long term. To stay aligned with **LGPD/GDPR** expectations and commercial trust in a privacy-oriented product:

- Use **short, technical** Conventional Commit subjects and PR descriptions. Do **not** put **candidate names**, **client identifiers**, **legal/whistleblowing** context, or **talent-pool** breadcrumbs in public commit or PR text.
- Keep operational detail in **gitignored** notes under `docs/private/` (or other channels your team agrees on).
- CI guards scan **tracked** files (`tests/test_pii_guard.py`, talent-related tests); they do **not** edit old commits. For history review or remediation, see [PII_PUBLIC_TREE_OPERATOR_GUIDE.md](PII_PUBLIC_TREE_OPERATOR_GUIDE.md) ([pt-BR](PII_PUBLIC_TREE_OPERATOR_GUIDE.pt_BR.md)). Policy index: [CONTRIBUTING.md](../../CONTRIBUTING.md) → *Public repo: third-party identifiers and Git history*.

## Complete workflow: check, pre-commit, commit, describe, and safe synced PR

When you want to **check**, run **pre-commit**, **commit**, **describe**, and create a **safe, synced PR** using repo scripts (best for saving tokens and one source of truth), use these **concrete actions in order** from the repo root (PowerShell):

| Step   | Goal                                                                                                                               | Command                                                                                        |
| ------ | ------                                                                                                                             | --------                                                                                       |
| 0      | **Optional:** open Dependabot PRs + Docker Scout quickview (read-only; needs `gh`, optional Docker)                                | `.\scripts\maintenance-check.ps1`                                                              |
| 0a     | **Optional:** PR hygiene reminder + quick open-PR checks (`gh` preflight + checks per open PR)                                     | `.\scripts\pr-hygiene-remind.ps1` or `.\scripts\pr-hygiene-remind.ps1 -RunQuickChecks`         |
| 1      | **Check + pre-commit** (Ruff lint, format, markdown, full pytest in one run)                                                       | `.\scripts\check-all.ps1`                                                                      |
| 1b     | **Optional version readiness smoke** (all-greens / pre-publish moments)                                                            | `.\scripts\check-all.ps1 -IncludeVersionSmoke`                                                 |
| 2      | **Preview** (see what would be committed; no stage, no commit)                                                                     | `.\scripts\preview-commit.ps1`                                                                 |
| 3      | **Propose** a short commit title and bullet-point PR body from the file list and context                                           | (you or the agent suggest title and body)                                                      |
| 4      | **Commit + describe + safe synced PR** (commit with title/body, run tests again, fetch+rebase if behind, push, open PR in browser) | `.\scripts\commit-or-pr.ps1 -Action PR -Title "Your title" -Body "Bullet1`nBullet2" -RunTests` |

For a **long PR body**, use:

- `.\scripts\create-pr.ps1 -Title "Your title" -BodyFilePath path\to\body.txt` (optionally add `-RunTests`; it defaults to on), or
- A one-off `.ps1` that sets `$Title` and `$Body` (e.g. here-string) and calls `commit-or-pr.ps1 -Action PR -Title $Title -Body $Body -RunTests`.

**Why this order:** One full gate before committing; one preview to confirm scope; one PR step that re-runs tests and syncs (fetch + rebase if behind) before push, so the PR is safe and synced. No ad-hoc `git add`/`git commit`/`git push` or raw `pytest`/`ruff` in between when these scripts cover the need.

### Merge after CI is green (maintainer / agent)

When **`gh pr checks <N>`** passes and the PR is **mergeable** (no conflicts), use **`.\scripts\pr-merge-when-green.ps1 -PrNumber <N>`** from the repo root (`gh` authenticated). Optional: **`-RunLocalCheckAll`** for a local **`check-all`** before merge. See **`.cursor/rules/agent-autonomous-merge-and-lab-ops.mdc`**.

### Canonical issue vs duplicate (“echo”) closure

When two or more issues track the same slice, pick **one canonical** issue, ship PRs that reference it, merge after **green CI**, then close **duplicates** with **`gh issue close … --duplicate-of …`** and an evidence comment. Full operator steps: [GITHUB_ISSUE_CANONICAL_AND_DUPLICATE_CLOSE.md](GITHUB_ISSUE_CANONICAL_AND_DUPLICATE_CLOSE.md) ([pt-BR](GITHUB_ISSUE_CANONICAL_AND_DUPLICATE_CLOSE.pt_BR.md)).

### GitHub auto-merge (optional)

**Default recommendation:** keep **auto-merge disabled** for normal feature/workflow PRs. Prefer an **explicit** merge after green checks and a conscious decision (human or **`pr-merge-when-green.ps1`**), so you avoid surprise merges and keep control aligned with a low-ceremony but deliberate workflow.

**When it can help:** mechanical, low-risk PRs (e.g. **Dependabot** after triage) where you still require **branch protection / checks** — enable **per PR** in the GitHub UI if you want the merge to happen automatically once CI passes.

## Conventional Commits: types and scopes (homelab / ops fronts)

Use **`type(scope):` short subject** (see root **`AGENTS.md`** for the canonical list). **Types:** `feat`, `fix`, `refactor`, `docs`, `chore`, `ci`, `test`, … — dependency-only work → **`chore(deps):`**. **Scopes** that match common “fronts” include **`homelab`**, **`ops`**, **`workflow`**, **`private-layout`**, **`plans`**, **`cursor`**, **`detector`**, **`report`**, **`api`**, **`docker`** — full table and examples in **`AGENTS.md`**.

**Documentation index** (all topics, both languages): [README.md](../README.md) · [README.pt_BR.md](../README.pt_BR.md).

**Docker image:** PR-friendly order for **merge → version bump → build → Docker Hub** (and Scout): [DOCKER_IMAGE_RELEASE_ORDER.md](DOCKER_IMAGE_RELEASE_ORDER.md).
