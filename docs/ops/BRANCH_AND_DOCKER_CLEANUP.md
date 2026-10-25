# Branch and Docker image cleanup (safe workflow)

**Português (Brasil):** [BRANCH_AND_DOCKER_CLEANUP.pt_BR.md](BRANCH_AND_DOCKER_CLEANUP.pt_BR.md)

**Purpose:** Free disk space and reduce clutter **without** losing Git history that is already on `main`, and without deleting work that is not merged. **Deleting a branch does not delete commits** that were merged into `main`—those commits remain in history. **Unmerged** branch tips are the only commits at risk if you delete a branch without merging or without pushing a backup ref.

**Repositories:** Day-to-day work targets **`DataBoar/data-boar`** (`origin`). The **`python3-lgpd-crawler-legacy-and-history-only`** remote is legacy; treat its branches separately (do not mix cleanup policies).

---

## 1. Git: refresh and see what is safe locally

From the repo root:

```powershell
# Update remote refs; drop local tracking branches whose remote was deleted
git fetch origin --prune

# See current branch
git branch --show-current

# Branches whose tips are already contained in origin/main (often safe to delete locally)
git branch --merged origin/main

# Branches that still have commits NOT in origin/main — review before deleting
git branch --no-merged origin/main
```

## Rules:

- **Do not delete** a branch listed under `--no-merged` unless you are sure the work is abandoned or saved elsewhere (e.g. another branch, a patch, or a GitHub fork).
- **Do not delete** the branch you are currently on; switch first: `git checkout main` (or another branch).
- After merges, remote branches on GitHub may still exist until you delete them (see §3).

**Example — delete one merged local branch** (after `checkout main`):

```powershell
git branch -d branch-name
```

Force delete only if Git says “not fully merged” and you **accept** losing that tip’s unique commits:

```powershell
git branch -D branch-name
```

**Squash-merged PRs:** After a **squash merge** to `main`, your old branch may still exist locally with different SHAs than `main` (`git branch --merged` might not list it). If the PR is merged on GitHub and you do not need the branch, delete by name (example after PR **#93**): `git branch -D pr/docker-scout-high-slice` — see [MAINTENANCE_FRONT_OF_WORK.md](../plans/MAINTENANCE_FRONT_OF_WORK.md) § Slice S4 *Quick housekeeping*.

---

## 2. What we saw on a typical dev machine (example snapshot)

After `git fetch origin --prune`:

- **`git branch --no-merged origin/main`** showed only **`plans-done-07ab7`** — treat as **keep or review** until merged or intentionally dropped.
- Many other locals were **`--merged origin/main`** — candidates for **local** deletion once you are not using them for work.
- Several locals showed **`[origin/...: gone]`** — the GitHub branch was already removed; your local copy is stale; safe to delete locally after you no longer need the name for reference.

**Your `main` may be behind `origin/main`** if you have not pulled recently. Before cleaning, align:

```powershell
git checkout main
git pull origin main
```

---

## 3. GitHub (`data-boar`): list and remove stale remote branches

**List branches on the remote** (requires GitHub CLI `gh auth login`):

```powershell
gh api repos/DataBoar/data-boar/branches --paginate -q ".[].name"
```

**Open PRs** (do not delete branches that still have open PRs until PR is closed/merged):

```powershell
gh pr list --repo DataBoar/data-boar --state open
```

**Check whether a remote branch is fully merged into `main`** (no unique commits):

```powershell
git fetch origin
git log origin/main..origin/BRANCH-NAME
```

- **Empty output** → branch tip is reachable from `main` (safe to delete remote branch from a history perspective).
- **Non-empty** → unique commits remain; merge or cherry-pick before deleting, unless you intentionally abandon them.

**Delete a remote branch** (when you are sure):

```powershell
git push origin --delete BRANCH-NAME
```

Or use the GitHub UI: **Repository → Branches →** delete stale feature branches (prefer after PR merge).

**Dependabot branches:** Usually delete after you merge or supersede the dependency update; keep the PR/merge commit on `main` as the record.

---

## 4. Docker: retention policy for Data Boar images

**Goal:** Keep roughly **two** distinct image **digests** for this product locally, for example:

1. **`fabioleitao/data_boar:latest`** (or the semver tag you are actively using, e.g. `1.6.2`).
1. **One previous** digest (older semver tag or last local `docker build`), so you can compare or roll back quickly.

**Smoke / lab builds are not special:** Repeated smoke tests do **not** require a unique tag each time (`data_boar:smoke-93`, `data_boar:smoke-foo`, …). That pattern **wastes disk** and mental overhead. Prefer **one** overwritten tag — **`docker build -t data_boar:lab .`** (matches [HOMELAB_VALIDATION.md](HOMELAB_VALIDATION.md) step 1.3) — and delete old experimental tags when done.

Older digests can be removed locally; you can **`docker pull`** historical tags from Docker Hub when needed.

**Automation:** From repo root, **`.\scripts\docker-hub-pull.ps1`**, **`.\scripts\docker-lab-build.ps1`**, **`.\scripts\docker-prune-local.ps1 -WhatIf`** (see [scripts/docker/README.md](../../scripts/docker/README.md)).

**List local images** (Windows PowerShell):

```powershell
docker images --format "table {{.Repository}}\t{{.Tag}}\t{{.ID}}\t{{.CreatedSince}}\t{{.Size}}" | Select-String -Pattern "data_boar|fabioleitao/data_boar"
```

**Remove a specific tag** (does not remove the digest until all tags pointing to it are removed):

```powershell
docker rmi fabioleitao/data_boar:OLD_TAG
```

**Remove an image by ID** (after removing or retagging all names that reference it):

```powershell
docker rmi IMAGE_ID
```

If a container still uses the image, stop/remove the container first or use `docker rm -f CONTAINER` then retry.

**Dangling / build cache** (usually safe; reclaim space without touching tagged releases):

```powershell
docker image prune -f
docker builder prune -f
```

For a deeper cache clean (optional):

```powershell
docker builder prune -af
```

---

## 5. Order of operations (recommended)

1. `git fetch origin --prune` and `git pull` on `main`.
1. Note `git branch --no-merged origin/main` — **do not delete** without review.
1. Delete **local** merged branches you no longer need (`git branch -d …`).
1. On GitHub, delete **remote** branches that are merged and unused (or `git push origin --delete …`).
1. Docker: list images → keep **latest + one previous** digest → `docker rmi` old tags/IDs → `docker image prune` / `docker builder prune`.

---

## 6. Related docs

- [COMMIT_AND_PR.md](COMMIT_AND_PR.md) — PR workflow; **push only to `data-boar`**.
- [REMOTES_AND_ORIGIN.md](REMOTES_AND_ORIGIN.md) — `origin` vs legacy remote.
- [DOCKER_SETUP.md](../DOCKER_SETUP.md) — build and tag conventions.
- [HOMELAB_VALIDATION.md](HOMELAB_VALIDATION.md) — smoke tests after cleanup.
- [PLANS_TODO.md](../plans/PLANS_TODO.md) — Priority band A (Dependabot, Scout, tag hygiene).
- [OPERATOR_NOTIFICATION_CHANNELS.md](OPERATOR_NOTIFICATION_CHANNELS.md) — multi-channel alerts (GitHub, Slack, Telegram, Signal) for humans and CI.

---

## 7. Legacy remote only (`python3-lgpd-crawler-legacy-and-history-only`)

**Backlog / non-blocking.** Day-to-day work and pushes belong to **`DataBoar/data-boar`** (`origin`). The extra remote ([REMOTES_AND_ORIGIN.md](REMOTES_AND_ORIGIN.md)) points at an **archived** GitHub repository URL (fetch-only, `pushurl = no-push`).

### Tidy-up goals

1. **Local branches** that still track `python3-lgpd-crawler-legacy-and-history-only/*`: list with `git branch -vv | Select-String legacy` (or `grep legacy` on Unix). For each, either **delete locally** if abandoned or **repoint** the upstream to `origin` on `data-boar` if the work should continue there ([REMOTES_AND_ORIGIN.md](REMOTES_AND_ORIGIN.md) § reassign upstream).
1. **No pushes** to the legacy GitHub repo from this workspace; that policy is intentional.
1. **Old repo on GitHub** (if you still own it): optional archive, or leave read-only for history—**do not** delete if others may have fork links; prefer **archived** state + README pointing to **data-boar**.

This is **documentation and discipline**, not an app feature. Schedule a short maintenance slot after `main` is stable.

---

## Last updated

Aligned with **data-boar** workflow, optional **Docker** cleanup, and **§7** legacy-remote tidy; re-run §1–§4 whenever you want a hygiene pass.
