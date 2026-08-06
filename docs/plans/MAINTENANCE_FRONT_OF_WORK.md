# Maintenance: single front of work (after spring clean)

**Intent:** After a burst of parallel branches and PRs, keep **one active development front** when possible: one open PR per coherent slice, merge, then start the next. Side work is allowed when the priority matrix demands it (e.g. security, CI), but each side track should close with merge or explicit supersede.

**Related:** `AGENTS.md` (dangling open PR guard), `docs/plans/PLANS_TODO.md` (recommended sequence), [PYTHON_UPGRADE_PLAYBOOK.md](PYTHON_UPGRADE_PLAYBOOK.md).

---

## Slice S1 — CI matches supported Python minors (done in same PR as this doc update)

- **Goal:** Run `pytest` on **Python 3.12 and 3.13** in GitHub Actions (`fail-fast: false`), aligned with `CONTRIBUTING.md` / `SECURITY.md` support claims.
- **Type:** `workflow` + `documentation` (CI YAML + `docs/TESTING*.md`).
- **Supersedes:** Open PR #79 (`pr/ci-python-313-matrix-playbook`) once this lands — close #79 with a comment pointing to the replacement PR; delete remote branch `pr/ci-python-313-matrix-playbook`.
- **Extras (logical):** Lint/audit/Sonar stay on a single Python (3.12) to limit minutes unless we later widen intentionally.

---

## Slice S2 — Prune merged remote heads

- **Goal:** Remove `origin/*` branch tips whose PRs are merged and whose commits are already on `main` (no resumable delta).
- **Type:** `workflow` (repo hygiene only).
- **Safety:** Do not delete branches that still have unique commits vs `main` without explicit review.

---

## Slice S3 — Legacy `origin/feature/*` and `origin/commit` ✅ completed

- **Goal:** Classify each: archive, resume as a new branch from `main`, or delete if fully superseded.
- **Outcome (verified):** Tips of `origin/commit`, `origin/feature/agent-review-style-pr-automation`, `origin/feature/agent-review-style-pr-automation-2`, and `origin/feature/release-1.4.0-completed-plans` were **already ancestors of `main`** (no commits ahead). **No resumable work** — safe disposal only.
- **Action taken:** Remote branches **deleted** on `origin` after `git merge-base --is-ancestor` + `rev-list --count main..branch` = 0.
- **If similar branches reappear:** Re-run the same checks before delete; do not prune if `aheadOfMain > 0` without review.

---

## Slice S4 — Optional maintenance aligned to `PLANS_TODO.md`

Pick **one** per session when CI is green:

| Track                          | Aligns to                                       | Notes                                                                                                                                                                                                                                                                                           |
| -----                          | ---------                                       | -----                                                                                                                                                                                                                                                                                           |
| `pr/docker-scout-high-slice`   | Order **–1b** (Docker Hub Scout)                | **Merged** (PR **#93**).                                                                                                                                                                                                                                                                        |
| **Docker base 3.13**           | Order **–1b**                                   | **Merged** — PR [**#99**](https://github.com/DataBoar/data-boar/pull/99) (`python:3.13-slim`). **Operator:** publish from `main`, then Scout — see [DOCKER_IMAGE_RELEASE_ORDER.md](../ops/DOCKER_IMAGE_RELEASE_ORDER.md).                                                                    |
| `pr/deps-security-refresh`     | Dependabot / security hygiene (**A1** / **–1**) | **Merged** — PR [**#101**](https://github.com/DataBoar/data-boar/pull/101). **Open alerts:** pyOpenSSL **#9/#10** blocked by Snowflake connector pin — see [DEPENDABOT_PYOPENSSL_SNOWFLAKE.md](../ops/DEPENDABOT_PYOPENSSL_SNOWFLAKE.md); bump connector when PyPI allows **pyopenssl>=26**. |
| `pr/api-report-path-hardening` | Security / API hardening                        | **Merged** — PR [**#98**](https://github.com/DataBoar/data-boar/pull/98).                                                                                                                                                                                                                    |

Do **not** stack these in one PR unless they are truly the same incident (e.g. one Scout round-trip).

### S4 progress (rolling)

| Sub-track                         | Status                                                                                                                                                                                                             |
| ---------                         | ------                                                                                                                                                                                                             |
| **–1b** Dockerfile / Scout        | **Merged** — PR **#93** + PR **#99** (3.13-slim base). **Operator:** `docker-lab-build` → `docker-hub-publish` → `docker-prune-local` (see [DOCKER_IMAGE_RELEASE_ORDER.md](../ops/DOCKER_IMAGE_RELEASE_ORDER.md)). |
| **A1** `pr/deps-security-refresh` | **#101 merged.** Remaining: **pyOpenSSL** alerts — wait for **`snowflake-connector-python`** release (or dismiss with doc link); then `uv lock` + export + `check-all`.                                            |
| API report paths                  | **Merged** — PR **#98**. Follow-up: [API_REPORT_PATH_CODEQL_FOLLOWUP.md](API_REPORT_PATH_CODEQL_FOLLOWUP.md).                                                                                                      |
| **–1L** second environment        | **When ready** — [HOMELAB_VALIDATION.md](../ops/HOMELAB_VALIDATION.md); not a blocker for merge/publish on `main`.                                                                                                 |

### Quick housekeeping (local branches after a merged maintenance PR)

GitHub **squash** merges often leave a **local** branch (e.g. `pr/docker-scout-high-slice`) with commits that no longer match `main`’s history, even though the work is on `main`. Safe cleanup when the PR is merged and you do not need the branch name:

```powershell
git checkout main
git pull origin main
git branch -D pr/docker-scout-high-slice
```

Use **`-D`** only when you accept dropping that local ref; **do not** delete branches with **unmerged** unique work (see [BRANCH_AND_DOCKER_CLEANUP.md](../ops/BRANCH_AND_DOCKER_CLEANUP.md) §1). Remote branch `origin/pr/docker-scout-high-slice` was removed after PR **#93** merged.

---

## Operating rule (minimal open fronts)

1. `gh pr list --state open` before starting a new slice.
1. Prefer **merge or close** existing open PRs before opening another **workflow** PR.
1. Product features (`feat/*`) follow `PLANS_TODO.md` after maintenance gates are green.

*Last updated: **#98**–**#101** on `main`; **A1** — pyOpenSSL/Snowflake triage doc; publish + Scout per [DOCKER_IMAGE_RELEASE_ORDER.md](../ops/DOCKER_IMAGE_RELEASE_ORDER.md); **–1L** when second env is ready.*
