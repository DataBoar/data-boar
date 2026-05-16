---
name: token-aware-automation
description: Use when deciding how to run lint, tests, commit/PR, or Docker homelab steps. Prefer repo scripts (check-all, lint-only, quick-test, commit-or-pr, docker-lab-build, docker-hub-pull, docker-prune-local) over ad-hoc commands to save tokens and keep behaviour consistent.
---

# Token-aware automation (scripts first)

**Full script map (skills, rules, keywords, ops links):** **`docs/ops/TOKEN_AWARE_SCRIPTS_HUB.md`** · **pt-BR:** **`docs/ops/TOKEN_AWARE_SCRIPTS_HUB.pt_BR.md`**. Use it when the task is not only lint/PR/Docker (e.g. homelab, PII, talent, release) to avoid orphaned one-off rediscovery.

**Always-on habit:** **`.cursor/rules/repo-scripts-wrapper-ritual.mdc`** — agreed **`scripts/*.ps1`** and wrappers (not only **`es-find`**) are part of the default path; if one fails, tell the operator (misconfiguration) before silently switching tools.

**Fresh chat / low context:** read **`docs/ops/OPERATOR_AGENT_COLD_START_LADDER.md`** ([pt-BR](../../docs/ops/OPERATOR_AGENT_COLD_START_LADDER.pt_BR.md)) first — ordered ladder + task router; then this skill + the hub for script picks.

**Validated orchestration scripts (`lab-completao*`, hybrid variants):** when the operator signals **literal fidelity** (*as-is*), read **`docs/ops/LLM_AGENT_EDITING_CAUTION.md`** ([pt-BR](../../docs/ops/LLM_AGENT_EDITING_CAUTION.pt_BR.md)) first — vendor web LLMs and IDE agents can still drift despite **`AGENTS.md`** / rules / skills; treat **`git diff`** + **`check-all`** as the hard gate.

**Public release order (do not invert):** Before bumping **`main`** to **`-beta`** after a shipped semver, follow **`.cursor/rules/release-publish-sequencing.mdc`** (**situational** — **`release-ritual`** or **`@release-publish-sequencing.mdc`**) and **`docs/VERSIONING.md`** (*Assistant / automation*). **`docker-local-smoke-cleanup.mdc`** stays **always-on**. Session keyword **`release-ritual`** = **`read_file`** that sequencing rule + always-on smoke rule. Tag **`vX.Y.Z`** → GitHub Release → **Docker Desktop: `docker-lab-build.ps1` + smoke `docker run --rm`** → **then** Hub **`docker push`** → **`docker-prune-local.ps1`** → Hub description paste → **`PUBLISHED_SYNC`** — then a **separate** pre-release commit.

When you need to **verify lint or tests**, or when the user asks to **commit, create a description, push, or create a PR**, use the repo scripts from the project root so behaviour is consistent and token use stays low.

## Always consider adding automation after fixes

For any meaningful fix or repetitive operator flow, proactively decide whether to add/update:

- a **regression test** (`tests/`),
- a **script** (`scripts/`) that standardizes repeated steps,
- or a **pre-commit/CI hook** for lightweight, high-signal checks.

If not added, state a short reason (for example runtime too high, flaky signal, already covered elsewhere).

## Which script to use (lint and tests)

| Goal                       | Script                                                                          | When it saves tokens                                      |
| ------                     | --------                                                                        | ----------------------                                    |
| Full gate before commit/PR | `.\scripts\check-all.ps1` (Windows) or `./scripts/check-all.sh` (Linux / macOS)  | Single command = one round-trip                           |
| Tests only (no pre-commit) | `.\scripts\check-all.ps1 -SkipPreCommit` or `./scripts/check-all.sh --skip-pre-commit` | Skips Ruff/markdown when you only care about tests        |
| Lint/format only           | `.\scripts\lint-only.ps1` or `./scripts/lint-only.sh`                           | No pytest when you only changed docs, templates, or style |
| One test file or keyword   | `.\scripts\quick-test.ps1 -Path tests/test_foo.py` or `-Keyword "content_type"` · `./scripts/quick-test.sh --path …` / `--keyword …` | Fewer tests = faster feedback and fewer tokens            |
| Pre-commit + pytest (thin) | `.\scripts\pre-commit-and-tests.ps1` or `./scripts/pre-commit-and-tests.sh`     | Same as **`check-all`** minus gatekeeper + **plans-stats**; keep **`.ps1`** / **`.sh`** in sync per **`docs/ops/SCRIPTS_CROSS_PLATFORM_PAIRING.md`** |
| PII fresh-clone self-audit (Windows; not full `check-all`) | `.\scripts\pii-fresh-clone-audit.ps1` (optional `-IncludeTalentGuards`) | Temp **full** clone + `pii_history_guard --full-history` + `test_pii_guard` (**primary-dev-workstation-safe**). See **`docs/ops/PII_FRESH_CLONE_AUDIT.md`**, **`docs/ops/PRIMARY_WINDOWS_WORKSTATION_PROTECTION.md`**; session **`pii-fresh-audit`**. |
| Windows: find files by **name/path** (not content) | `.\scripts\es-find.ps1 -Query "*.md" -MaxCount 40` (or `-Help`; if **`es.exe`** / IPC fails: **tell the operator**, then **`-FallbackPowerShell`** or scoped **`Get-ChildItem`**) | **Default** = **`es.exe` via `es-find.ps1`** (**read-only**, **primary-dev-workstation-safe**). **`Get-ChildItem`** = **recovery** after **`es`** fails — avoid unbounded **`-Recurse`** from huge **`P:\`** roots as the opening move. Default scope = repo root; `-Global` for full index. **Not** on **Linux lab-op**. **`everything-es-cli.mdc`**. **`docs/ops/EVERYTHING_ES_PRIMARY_WINDOWS_DEV_LAB.md`**; session **`es-find`**. Skill **`everything-es-search`**. |

## Docker homelab (Windows, optional — token-efficient)

When the session touches **Dockerfile**, **image publish**, **Scout**, **homelab disk**, or **local smoke/A/B**, prefer these **repo scripts** from the project root instead of inventing many `docker build -t data_boar:smoke-…` commands or long `docker rmi` explorations. Same outcome, **shorter transcripts**, predictable tags.

| Goal                                                                                             | Script                                           | When it saves tokens                                                                      |
| ------                                                                                           | --------                                         | ----------------------                                                                    |
| Build / refresh **local lab** image (`data_boar:lab`, optional `lab-prev`, optional `-TagSmoke`) | `.\scripts\docker-lab-build.ps1`                 | One command vs multi-step build/tag instructions                                          |
| Pull **Hub** `latest` + **semver from pyproject** + **previous patch**                           | `.\scripts\docker-hub-pull.ps1`                  | One command vs three pulls + version lookup                                               |
| Drop stray local tags (keep allowlist)                                                           | `.\scripts\docker-prune-local.ps1 -WhatIf` first | Lists targets without deleting; avoids huge `docker images` + manual reasoning every time |

**Opportunistic use:** After merging Dockerfile changes, after push to Docker Hub, when the user mentions **full disks** or **too many `data_boar` tags**, or when **HOMELAB_VALIDATION** / **–1b Scout** steps are relevant — suggest or run **`-WhatIf`** first for prune. Details: **`scripts/docker/README.md`**. Container/image policy: **`.cursor/skills/docker-smoke-container-hygiene/SKILL.md`**.

## Commit, push, and PR (use automation)

When the user asks to **commit**, **write a description**, **push to GitHub**, or **create a PR**, use the commit-or-pr workflow instead of raw `git add` / `git commit` / `git push`:

| Goal                                             | Script                                                                                                                                       | Notes                                                                                                                      |
| ------                                           | --------                                                                                                                                     | --------                                                                                                                   |
| See what would be committed (no commit)          | `.\scripts\preview-commit.ps1` or `.\scripts\commit-or-pr.ps1 -Action Preview`                                                               | Run first to list files and propose title/body.                                                                            |
| Commit locally with title and body               | `.\scripts\commit-or-pr.ps1 -Action Commit -Title "Short title" -Body "Bullet1`nBullet2"`                                                    | Body: use `` `n `` for newlines in PowerShell.                                                                             |
| Create PR (commit if needed, push, open browser) | `.\scripts\commit-or-pr.ps1 -Action PR -Title "..." -Body "..." -RunTests`                                                                   | Prefer `-RunTests` so tests run before push.                                                                               |
| Create PR with body from file (avoids escaping)  | `.\scripts\create-pr.ps1 -Title "Title" -BodyFilePath path\to\body.txt`                                                                      | Write body to a temp file, then pass path; no here-string in shell.                                                        |
| One-off PR with predefined message               | Create a small .ps1 that sets `$Title` and `$Body` (here-string) and calls `commit-or-pr.ps1 -Action PR -Title $Title -Body $Body -RunTests` | Same pattern as `scripts/do_pr.ps1`; avoids CLI escaping.                                                                  |
| Merge PR after CI green + mergeable              | `.\scripts\pr-merge-when-green.ps1 -PrNumber <N>`                                                                                            | Verifies `gh pr checks`; optional `-RunLocalCheckAll`. See **`.cursor/rules/agent-autonomous-merge-and-lab-ops.mdc`**.     |
| LAB-OP: pull repos + host report on many hosts   | `.\scripts\lab-op-sync-and-collect.ps1` (needs private manifest)                                                                             | **`docs/private.example/homelab/lab-op-hosts.manifest.example.json`** → `docs/private/homelab/lab-op-hosts.manifest.json`. |
| Maestro **-Deep** turn + **`Get-LabStatus`** loop + **`-Collect`** | `.\scripts\maestro-deep-rc-monitor-collect.ps1` (optional **`-SkipMonitor`**, **`-SkipCollect`**, **`-ClearHostEachLoop`**) | Private **`docs/private/homelab/data/inventory.json`**; hub **`docs/ops/TOKEN_AWARE_SCRIPTS_HUB.md`** §3; **`scripts/maestro/Maestro.ps1`**. |

## Complete workflow: check → pre-commit → commit → describe → safe synced PR

When the user wants to **check, pre-commit, commit, describe, and create a safe synced PR**, use these **concrete actions in order** (script-only, token-optimal):

| Step   | Action                                                                                            | Script / command                                                                          |
| ------ | --------                                                                                          | ------------------                                                                        |
| 1      | **Check + pre-commit** (lint, format, markdown, tests in one run)                                 | `.\scripts\check-all.ps1`                                                                 |
| 2      | **Preview** (see what would be committed; no commit)                                              | `.\scripts\preview-commit.ps1`                                                            |
| 3      | **Propose** title and body from the file list and context                                         | (you suggest a short title and bullet-point body)                                         |
| 4      | **Commit + describe + safe synced PR** (commit, run tests, fetch/rebase if behind, push, open PR) | `.\scripts\commit-or-pr.ps1 -Action PR -Title "Title" -Body "Bullet1`nBullet2" -RunTests` |

For a **long PR body**, use one of:

- `.\scripts\create-pr.ps1 -Title "Title" -BodyFilePath path\to\body.txt` (body in file)
- A one-off .ps1 that sets `$Title` and `$Body` (here-string) and calls `commit-or-pr.ps1 -Action PR -Title $Title -Body $Body -RunTests`

**Why this order:** One full gate (`check-all.ps1`) before any commit; one preview to avoid wrong scope; one PR action that re-runs tests and syncs (fetch+rebase) before push. No ad-hoc `git`/`pytest`/`ruff` in between.

Workflow that saves tokens (shorter form):

1. **Preview:** run `.\scripts\preview-commit.ps1` (or `commit-or-pr.ps1 -Action Preview`) to see changed files and diff summary.
1. **Propose:** from the file list and context, suggest a short title and bullet-point body.
1. **Commit or PR:** run `commit-or-pr.ps1 -Action Commit` (or `-Action PR -RunTests`) with that title and body. For a multi-line body without escaping issues, use `create-pr.ps1 -Title "..." -BodyFilePath (temp file)` or a one-off .ps1 with a here-string for `$Body`.

## Local commits to document progress (before PR / release)

- **Commit locally** on a **feature branch** when a checkpoint is done: one **important** change, *or* a **coherent batch** of edits (same “train of thought”). Prefer **not** leaving a huge **uncommitted** tree for days—it complicates review, risks loss, and causes **rebase/merge pain** at PR time.
- **Split or batch:** one commit per batch is fine; or several commits by sub-theme (`docs`, `test`, `feat`) with clear messages—see **AGENTS.md** and **`.cursor/rules/execution-priority-and-pr-batching.mdc`**.
- **Stay synced:** `git fetch` and merge/rebase **`origin/main`** into long-lived branches regularly (**.cursor/rules/git-pr-sync-before-advice.mdc**).
- **Scripts:** `preview-commit.ps1` → `commit-or-pr.ps1 -Action Commit` for local-only; **one PR** can still include **many** local commits. Ops narrative: **`docs/ops/COMMIT_AND_PR.md`**.

## Rules of thumb

- **After code change:** `.\scripts\check-all.ps1 -SkipPreCommit` (or full `check-all.ps1` before commit).
- **After docs/template/style change:** `.\scripts\lint-only.ps1`; run full check-all before pushing.
- **After adding, renaming, or archiving a `PLAN_*.md`:** `python scripts/plans_hub_sync.py --write` and commit **`docs/plans/PLANS_HUB.md`**; if **`PLANS_TODO.md`** dashboard rows changed, also `python scripts/plans-stats.py --write`. Pre-commit includes **`plans-hub-check`**.
- **Iterating on one area:** `.\scripts\quick-test.ps1 -Keyword "content_type"` (or `-Path tests/test_file_scan_use_content_type_flag.py`); run full check-all when the slice is done.
- **GitHub Actions YAML (Slack, `ci.yml`, Semgrep, pins):** `.\scripts\quick-test.ps1 -Path tests/test_github_workflows.py` — same tests run inside full **`check-all`** / **`ci.yml`**; update **`tests/test_github_workflows.py`** when workflow shape intentionally changes (see **`docs/ops/OPERATOR_NOTIFICATION_CHANNELS.md`** §4.1.1 if Slack CI failure notify is in play).
- **User asks to commit / push / create PR:** use `preview-commit.ps1` then `commit-or-pr.ps1` (or `create-pr.ps1` for PR with body file); do not use ad-hoc `git add`/`git commit`/`git push` when the script covers the need.

## Critical-first + PR batching (workflow policy)

- If a **critical blocker** exists (broken script flow, sync/merge confusion, failing safety gate), prioritize that first and stabilize to local commits before resuming feature work.
- If no critical blocker exists, prioritize product slices by `docs/plans/PLANS_TODO.md` taxonomy, with token-aware bias (low cost / high gain).
- **Active sprint theme:** Chunk the **current** milestone/Kanban row—do **not** jump to unrelated low-token work every session unless the **operator** reprioritises. See **`.cursor/rules/execution-priority-and-pr-batching.mdc`** §3 and **`docs/plans/TOKEN_AWARE_USAGE.md`** §2.
- Do **not** force a PR on every commit. Keep coherent local commits, then open one PR when the slice is reviewable and useful.
- Micro-PRs are for truly tiny, complete, low-risk changes only.

## Commit grouping for low cognitive load (feature vs workflow vs documentation)

When a "next step" includes multiple phases, classify each planned change before committing:

| Type            | Includes                                                  | Keep with docs?                                                                                     |
| ------          | ----------                                                | -----------------                                                                                   |
| `feature`       | Product behavior, detector/report logic, config semantics | Yes, when docs are needed to explain behavior/config at that checkpoint (`feature + documentation`) |
| `workflow`      | Scripts, branch/PR guardrails, CI/process automation      | Yes, when docs are needed for contributor/operator usage (`workflow + documentation`)               |
| `documentation` | Pure explanatory text with no behavior/process change     | Prefer standalone docs commit                                                                       |

Rules:

1. Avoid mixing `feature + workflow` in one commit/PR unless explicitly requested for urgent recovery.
1. Prefer one coherent commit per type/track, not one commit per tiny file.
1. For larger slices, keep commits ordered by narrative: core change first, required docs second, optional polish last.
1. Before opening PR, verify commit list reads clearly as a story for a new reviewer.

Quick checklist before PR:

- "Can each commit be explained in one sentence?"
- "Would reverting one commit break an unrelated concern?"
- "Did we keep docs attached only where they are required for that change?"

### Conventional commit types (subject line)

See **`AGENTS.md`** for types and the **scope table** (`homelab`, `ops`, `workflow`, `private-layout`, `plans`, `cursor`, `detector`, …). **`chore(deps):`** for dependency-only bumps. Full list: `feat`, `fix`, **`fix(security):`** or top-level **`security:`**, **`refactor`**, `docs`, `chore`, `ci`, optional scopes. If a slice mixes unrelated feature work and a bugfix, use **two commits** (or PRs), not one ambiguous combo.

Avoid running raw `pytest`, `ruff`, `pre-commit`, or manual git commit/push when a script already does the same thing; the scripts are the single source of behaviour and keep sessions token-efficient. For **Docker** homelab hygiene, avoid long custom `docker build`/`rmi` sequences when **`docker-lab-build.ps1`**, **`docker-hub-pull.ps1`**, or **`docker-prune-local.ps1`** cover the need.

## PR state / number freshness (before merge advice or sharing links)

The assistant **does not** have live GitHub state between messages. Before advising **merge**, **post-merge next steps**, or pasting a **PR URL/number** (especially right after `gh pr create`):

1. Run **`git fetch origin`**, and on **`main`**: **`git pull origin main`** (or show `git status -sb`), **or**
1. Run **`gh pr view <n> --json state,mergedAt,url`** or **`gh pr list --head <branch>`**.

After **`gh pr create`**, run **`gh pr view --json number,state,url`** before sharing the link so you cite the **new** PR, not a previously merged one. GitHub may lag briefly after merge — re-query if needed.

**Project rule:** `.cursor/rules/git-pr-sync-before-advice.mdc` (always apply). **Human-readable:** `CONTRIBUTING.md` § *PR state and agent advice*, **`AGENTS.md`**.
