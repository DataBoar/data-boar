# Operator workflow: pace, focus, and when to split work

**Português (Brasil):** [OPERATOR_WORKFLOW_PACE_AND_FOCUS.pt_BR.md](OPERATOR_WORKFLOW_PACE_AND_FOCUS.pt_BR.md)

**Purpose:** One place to reason about **how** to move fast toward demo → beta → production **without** accidental quality regressions, and how that relates to **Corporate-Entity-C** follow-ups, **session keywords**, and **optional** parallel help. **Not** a replacement for `PLANS_TODO.md` or `TOKEN_AWARE_USAGE.md`.

---

## 1. Resuming from a pause (what to check first)

1. **Git state:** `git fetch` + `git status` — branch aligned with `main` if you are mid-merge.
1. **Open PRs:** `gh pr list --state open` — finish or close superseded PRs before starting a large new slice.
1. **CI:** Green on the PR you care about (`gh pr checks <n>` or the GitHub UI).
1. **Secrets** (e.g. Slack): Repository **Settings → Secrets and variables → Actions** — `SLACK_WEBHOOK_URL` set; then run the manual workflow **Slack operator ping** under **Actions** to confirm delivery.

The assistant does **not** reliably know yesterday’s chat or your machine’s RAM unless you paste or run commands in this session.

---

## 2. Two “subagents” (code vs docs) — does it make sense?

| Approach                                                                               | Why it can help                                                 | Why it can hurt                                                                                                                                               |
| --------                                                                               | ----------------                                                | ----------------                                                                                                                                              |
| **Single Cursor session + clear keyword** (`feature`, `docs`, `houseclean`, `backlog`) | One coherent diff, one PR narrative, `check-all` once per slice | Long sessions can mix concerns if you do not name the mode                                                                                                    |
| **Parallel Task subagents** (explore vs implement)                                     | Fast exploration of large trees; isolation for one-off searches | Two agents can propose overlapping edits; you still merge one branch                                                                                          |
| **Permanent split: “Code agent” vs “Docs agent”**                                      | Sounds tidy                                                     | **Usually worse:** duplicated context, conflicting instructions, two PRs fighting the same files; **rules/skills already encode** quality bars and doc policy |

**Practical recommendation:** keep **one** implementation thread per branch/PR. Use **keywords** to scope the **intent** of the session. Use **Task** for **read-only exploration** or **parallel research**, not as a second author on the same PR unless you explicitly coordinate (e.g. one branch docs-only, one code-only, merged in order).

**Documentation vs product code** in one release: still prefer **separate commits** (`documentation` vs `feature` grouping per `execution-priority-and-pr-batching.mdc`), not two separate “agents” with separate memories.

---

## 3. Adding more chat commands (taxonomy)

The table in **`.cursor/rules/session-mode-keywords.mdc`** is intentionally **small and English-only**. Adding many new tokens (`corporate-entity-c-slice`, `demo-prep`, …) often **increases cognitive load** and confusion (“which token today?”).

## Prefer:

- **`backlog`** + a **named item** in the message (“next Corporate-Entity-C row: secure-by-default API key”).
- **`feature`** + **`PLANS_TODO.md`** row reference.
- **`docs`** for doc-only passes.

**If** a new token is ever added, it should be **one** well-defined scope, documented in the same table, and used consistently—**not** a new synonym for an existing mode.

---

## 4. Pace: Corporate-Entity-C, critical-first, token-aware, demo → prod

- **Source of truth for backlog order:** `docs/plans/PLANS_TODO.md` and **Corporate-Entity-C mapping** in `docs/plans/Corporate-Entity-C_ANALISE_2026-03-23_EVOLUTIVA.md` (and `Corporate-Entity-C_IN_REPO_BASELINE.md` for reviewer paths).
- **Critical-first** means: **blocking security/regression issues** and **CI truth** before cosmetic refactors.
- **Token-aware** (see `TOKEN_AWARE_USAGE.md`): small, reviewable slices with tests, not cross-cutting rewrites in one PR.
- **Demo → beta → production:** align **operator** checklists (`HOMELAB_VALIDATION.md`, release notes, `VERSIONING.md`) with **what** is actually marketed in README/pitch; avoid promising features still in `Deferred` in `PLANS_TODO.md`.

---

## 5. Study, certification, and avoiding exhaustion

- **CWL / cyber study cadence** is summarized in **`study-check`** (see `session-mode-keywords.mdc`) and `docs/plans/PORTFOLIO_AND_EVIDENCE_SOURCES.md` (Section 3.x).
- **Blue team / certification** tracks are **not** a separate Cursor token today—use **`study-check`** for rhythm, and keep **personal milestones** (exam dates, modules done) in **`docs/private/`** or your calendar so the assistant can refer to them **when you paste or ask**.
- **Natural breakpoints:** after a green `check-all`, merged PR, or end of day—brief pause to switch context (study vs code) is **intentional**, not a failure of focus.

---

## 6. IDE / OOM / hardware

A **freeze or OOM** in Cursor is usually **local memory pressure** (large chat, many files, extensions). More **RAM** on the laptop helps; **smaller** chat turns, **closing** unused tabs, and **splitting** work across sessions also help. It is **not** a verdict on the project or your pace.

---

## 7. Concrete next steps (operator checklist)

1. **PR hygiene:** List open PRs; merge or close superseded ones **after** `check-all` / CI green on the branch you care about.
1. **Slack:** With `SLACK_WEBHOOK_URL` set, run **Actions → Slack operator ping (manual)** once; confirm the message in `#data-boar-ops` (or your channel).
1. **Corporate-Entity-C loop:** Reply to Corporate-Entity-C with **evidence** (paths in `Corporate-Entity-C_IN_REPO_BASELINE.md`); pick **one** next row from the evolution table (e.g. product naming or secure-default API decision) as a **scoped** `feature` or `backlog` slice.
1. **Demo readiness:** Re-read `PLANS_TODO.md` “Selected / In progress” and `SPRINTS_AND_MILESTONES.md`; one **homelab** run through `HOMELAB_VALIDATION.md` before calling a build “demo-ready”.
1. **Next session:** Start with **`pmo-view`** or paste **`PLANS_TODO.md`** section so the assistant anchors on the **same** priority.

---

## 7.1 Git commits, PRs, and merges vs office hours (maintainer discretion)

**Not a rule for contributors** — this paragraph points to an **operator-only** note under gitignored `docs/private/` for maintainers who want to **reduce** public GitHub activity during local business hours (home office) without banning local work.

- **Canonical detail (private):** `docs/private/OPERATOR_GIT_PR_RHYTHM_OFFICE_HOURS.pt_BR.md` — when to batch vs ship immediately; **critical-first** and **security** exceptions; commit message hygiene as “digital breadcrumbs.”
- **Summary:** Prefer fewer pushes/merges during weekday **office hours** in **America/Sao_Paulo** when the work is **not** urgent; **do** commit/push/merge **immediately** for **priority-band critical** items, **security/CVE**, broken **CI on `main`**, or similar — with a **clear Conventional Commit** subject/body explaining urgency.
- **Assistants:** Read the **private** file for the current **mode**. When it indicates **sabbatical / between jobs**, **do not** apply batch/defer for office hours by default. When **employed** mode is active there, **apply** this by default when suggesting **push / PR / merge** timing — batch or defer non-critical work to **off-hours**; **do not** nudge for noisy public Git activity during business hours unless the **§7.1** exceptions apply or the operator asks otherwise in-session.

**Tracked stub:** `docs/private.example/OPERATOR_GIT_PR_RHYTHM_OFFICE_HOURS.example.md`.

---

## 8. Recent progress recap (`git`, token-aware)

When you want a **compact** sense of **pace** (what landed on **`origin/main`**) without rereading entire plan tables:

1. From repo root: **`.\scripts\git-progress-recap.ps1`** — default **last 3 calendar days** on **`origin/main`**; use **`-Days 7`** or **`-Days 14`** to widen the window; **`-MaxPerDay`** caps lines per day if a merge burst was huge; **`-NoFetch`** if you are offline.
1. Output is **grouped by date** with **one line per commit** (`hash` + subject) so you can see **busy vs quiet** days and **themes** from Conventional Commit prefixes (`feat`, `docs`, `chore`, …).
1. This **does not** replace **`PLANS_TODO.md`**, **`today-mode`**, or **`carryover-sweep` / `eod-sync`** — use it as a **cheap narrative** before a day plan or retro.

**Chat habit (optional):** paste the script output into Cursor when aligning on “what happened this week” — fewer tokens than dumping raw `git log`. No new English session token is required; natural language (“**progress recap 7 days**”) is enough.

---

## 9. Slack AFK + CI failure (channel B)

When you are **away from the desk**, **GitHub mobile (channel A)** plus **Slack (channel B)** give redundancy: CI failures and manual pings reach you without staying in Cursor.

- **Setup:** [OPERATOR_NOTIFICATION_CHANNELS.md](OPERATOR_NOTIFICATION_CHANNELS.md) §4.1 — `SLACK_WEBHOOK_URL` in repo secrets; **Actions → Slack operator ping (manual)** for smoke test; **Slack CI failure notify** posts when workflow **CI** completes with **failure** (same secret).
- **Product / scan-complete:** optional reuse of the webhook in app config per USAGE — separate from Actions.
- **Completion checklist:** secret set → manual ping succeeded → confirm one intentional CI failure path if you want to validate the notify workflow (or trust the workflow YAML + secret).

---

## 10. GitHub auto-merge (recommendation)

**Default: keep auto-merge off** for this repo’s usual flow. Prefer **explicit** merge when checks are green and you (or the agent via **`pr-merge-when-green.ps1`**) have confirmed **mergeable** + **no regression doubt** — matches deliberate, low-ceremony delivery without surprise merges.

**When auto-merge can help:** low-risk, mechanical PRs (e.g. **Dependabot** bumps you already triage) where you still want **required checks** to pass first — optional per-PR in GitHub UI, not a global habit.

**Why not blanket auto-merge:** feature PRs benefit from a **human or scripted last look**; auto-merge can merge before you notice **semantic** risk that CI did not catch.

---

## 11. Session keywords and “subagents” (where it is documented)

- **English tokens** (`feature`, `docs`, `backlog`, `study-check`, `pmo-view`, …): **`.cursor/rules/session-mode-keywords.mdc`** (canonical table).
- **Splitting code vs docs vs Task exploration:** this file §2 and [TOKEN_AWARE_USAGE.md](../plans/TOKEN_AWARE_USAGE.md).

---

## 12. Related docs

- [COMMIT_AND_PR.md](COMMIT_AND_PR.md) — PR batching, merge, auto-merge note.
- [TOKEN_AWARE_USAGE.md](../plans/TOKEN_AWARE_USAGE.md) — token-aware slices.
- [Corporate-Entity-C_ANALISE_2026-03-23_EVOLUTIVA.md](../plans/Corporate-Entity-C_ANALISE_2026-03-23_EVOLUTIVA.md) — prioritized themes.
- [OPERATOR_NOTIFICATION_CHANNELS.md](OPERATOR_NOTIFICATION_CHANNELS.md) — Slack + GitHub channel A.
