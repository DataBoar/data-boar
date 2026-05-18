# GitHub issues: canonical work item vs duplicate (echo) closure

**Português (Brasil):** [GITHUB_ISSUE_CANONICAL_AND_DUPLICATE_CLOSE.pt_BR.md](GITHUB_ISSUE_CANONICAL_AND_DUPLICATE_CLOSE.pt_BR.md)

**Purpose:** When several issues describe the same slice (accidental duplicates, “echo” filings, or audit bots opening overlapping tickets), keep **one canonical issue** for tracking, ship **thin PRs** that reference it, and **close duplicates only after** merge and green CI — with **evidence** on the duplicate thread.

**Alignment:** [COMMIT_AND_PR.md](COMMIT_AND_PR.md), [CONTRIBUTING.md](../../CONTRIBUTING.md), [PLANS_TODO.md](../plans/PLANS_TODO.md) (issue sweep note), **`.cursor/rules/git-pr-sync-before-advice.mdc`**, **`.cursor/rules/execution-priority-and-pr-batching.mdc`**, **`.cursor/rules/agent-autonomous-merge-and-lab-ops.mdc`**.

## 1. Pick the canonical issue

- Prefer the issue that best matches **scope** and has the **lowest number** if two titles are truly the same work — unless the newer issue **supersedes** scope (then treat the newer analysis as canonical and close the older as duplicate or not planned with rationale).
- Record the decision in **`PLANS_TODO.md`** only when it affects sequencing (one line is enough); do not paste long narratives into tracked plans.

## 2. Work and PR

- Branch + commits: **one subject cluster per commit** when practical; reference the **canonical** issue in PR title or body (`Closes #NNN` / `Fixes #NNN` for the canonical `NNN`).
- Run **`check-all`** (or **`lint-only`** for docs-only) before push; see **COMMIT_AND_PR.md**.

## 3. Gate before closing anything

Do **not** close issues based on “looks done locally” alone.

1. **`git push`** and PR **open** (or update).
2. **`gh pr checks <PR>`** green **and** branch protection satisfied (same intent as **`pr-merge-when-green.ps1`**).
3. **Merge** to `main` when appropriate (human or scripted merge per project rules).

## 4. Close the canonical issue

- If the PR body used **`Closes #NNN`**, GitHub may already close **`NNN`** on merge — verify with **`gh issue view NNN`**.
- If it stayed open: **`gh issue close NNN -r completed -c "Shipped in https://github.com/OWNER/REPO/pull/PRNO (merge …)."`** (adjust URL and add commit SHA if useful).

## 5. Close duplicate / echo issues (after you are satisfied they match)

Only after step **3** (merge + green checks on the integrating PR):

1. Confirm the duplicate is **the same slice** as the canonical (title + body); if not, do **not** use duplicate closure — triage separately.
2. Close with GitHub’s duplicate link and an **evidence comment** (PR URL; optional commit SHA):

   ```bash
   gh issue close DUPLICATE --duplicate-of CANONICAL \
     --comment "Resolved via https://github.com/OWNER/REPO/pull/PRNO — same scope as #CANONICAL."
   ```

   **`gh`** maps **`--duplicate-of`** to GitHub’s duplicate relationship; the **`--comment`** leaves a public audit trail.

3. If you are **not** satisfied it is the same: close as **`not planned`** or leave open with a comment — do **not** mark **`duplicate-of`** incorrectly.

## 6. What not to do

- Do not bulk-close issues without **PR merge + green CI** evidence for the fix that applies to the canonical item.
- Do not put secrets, private hostnames, or unrelated PII in closing comments — **PR link + issue cross-reference** is enough.

## 7. Quick reference (copy-paste)

Replace `OWNER`, `REPO`, numbers, and URLs:

```bash
gh pr checks <PR-NUMBER>
# after merge
gh issue view <CANONICAL>
gh issue close <DUPLICATE> --duplicate-of <CANONICAL> --comment "Resolved via https://github.com/OWNER/REPO/pull/<PR-NUMBER> — same scope as #<CANONICAL>."
```
