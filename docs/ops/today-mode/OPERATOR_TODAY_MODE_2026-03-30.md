# Operator “today mode” — 2026-03-30 (no carryover block)

**Português (Brasil):** [OPERATOR_TODAY_MODE_2026-03-30.pt_BR.md](OPERATOR_TODAY_MODE_2026-03-30.pt_BR.md)

**Purpose:** A **focused day** without a **Block 0 carryover** sweep — you asked to omit carryon. Start directly on **repo hygiene + merge discipline**. Use **`today-mode 2026-03-30`** in chat. Day boundaries: **`carryover-sweep`** (morning, optional) · **`eod-sync`** (evening) — **`scripts/operator-day-ritual.ps1`**, **`.cursor/rules/session-mode-keywords.mdc`**.

**Note:** If you *do* want a carryover pass later, run **`carryover-sweep`** separately or open **[OPERATOR_TODAY_MODE_2026-03-29.md](OPERATOR_TODAY_MODE_2026-03-29.md)** — it is **not** part of this checklist.

**Publish truth (verified 2026-03-30):** **`pyproject.toml`** on `main` is **1.6.7**, matching **GitHub Release Latest [`v1.6.7`](https://github.com/FabioLeitao/data-boar/releases/tag/v1.6.7)** (published **2026-03-26**) and **Docker Hub** **`fabioleitao/data_boar:1.6.7`** + **`latest`**. The next **public** version after meaningful new commits → **`1.6.8`** (bump + release notes), not a **re-publish** of **1.6.7**.

---

## Block A — Working tree → coherent commits / PR(s) (≈ 60–120 min)

- Run **`git status -sb`** and **`.\scripts\preview-commit.ps1`** (or **`commit-or-pr.ps1 -Action Preview`**) so scope matches intent.
- **Batch by theme** (per **`.cursor/rules/execution-priority-and-pr-batching.mdc`**): e.g. **documentation** (inspirations hub, engineering craft table + deep analysis, compliance samples, ADRs, ops index) vs **workflow/rules** (`.cursor`) — avoid one giant mixed PR unless you explicitly want it.
- After edits: **`.\scripts\lint-only.ps1`** for doc-only slices, or **`.\scripts\check-all.ps1`** before merge when code/tests touched.

---

## Block B — Dependabot / deps (≈ 30–45 min)

- Open PRs (as of last **`eod-sync`**): **#134** (pypdf / uv), **#143** (pip minor-patch group), **#144** (starlette) — verify **`gh pr checks`** green, then **`.\scripts\pr-merge-when-green.ps1 -PrNumber <N>`** when safe, or triage/dismiss per **`SECURITY.md`** / Dependabot hygiene.
- After merges: **`git checkout main && git pull`**, refresh **`uv lock`** / **`requirements.txt`** if the PR didn’t already.

---

## Block C — Optional thin follow-ups (≈ 30 min, pick one)

- **Supply chain sanity:** confirm **`uv.lock`** still has **no `litellm`** after any dep refresh; optional one-line note in **`SECURITY.md`** / private journal pointing to the Mar 2026 PyPI **`litellm`** incident if you want a durable reminder (not required).
- **Inspirations:** skim **[ENGINEERING_CRAFT_INSPIRATION_ANALYSIS.md](../ENGINEERING_CRAFT_INSPIRATION_ANALYSIS.md)** — add one **cluster** bullet only if a new pattern emerged.

---

## Stop condition

Day is “done” when: **tree is either clean on `main`** or **intentional WIP** is committed on a branch; **Dependabot PRs triaged** (merged, closed, or explicit next date); and **no silent** mix of unrelated subjects in a single commit without intent.

---

## Chat shorthand

**`today-mode 2026-03-30`** or open this file.
