# Remotes and origin (data-boar)

**Português (Brasil):** [REMOTES_AND_ORIGIN.pt_BR.md](REMOTES_AND_ORIGIN.pt_BR.md)

This repo uses **data-boar** as the only push/PR destination. **Product name:** **Data Boar**. An optional second remote may still use a **long historical label** in `.git/config` pointing at an archived GitHub URL — that is a **Git convenience** for fetch-only history, not the public product identity.

Note: the former GitHub path `FabioLeitao/data-boar` still redirects to the canonical `DataBoar/data-boar`.

The following is stored in local `.git/config` and can be checked or changed from the terminal.

## Verify current remotes

From the repo root:

```bash
# List all remotes and their URLs (fetch + push)
git remote -v
```

You should see:

- **origin** → `git@github.com:DataBoar/data-boar.git` (fetch and push)
- **python3-lgpd-crawler-legacy-and-history-only** → `git@github.com:FabioLeitao/python3-lgpd-crawler.git` (fetch only); push URL is `no-push` so push is disabled

## Change where `origin` points (manual)

If you ever need to set or change the destination URL from the terminal:

```bash
# Set origin to data-boar (SSH)
git remote set-url origin git@github.com:DataBoar/data-boar.git

# Or with HTTPS:
# git remote set-url origin https://github.com/DataBoar/data-boar.git

# Confirm
git remote -v
```

There is no `git switch` for remotes; use `git remote set-url origin <url>` to change the destination.

## Push and PR behavior

- **Default push:** `git push` uses the **tracking remote** of the current branch. The branch you use for new work (e.g. `2026-03-14-3i1y`) is configured with `remote = origin`, so `git push` goes to **data-boar**.
- **Explicit push:** To always push a branch to data-boar regardless of its configured remote:

  `git push origin <branch-name>`

- **python3-lgpd-crawler-legacy-and-history-only:** The old python3-lgpd-crawler repo; kept for legacy history and fetch only. Do not push to it; push is disabled via `pushurl = no-push`.

## Branch upstreams

Some older branches may still have `remote = python3-lgpd-crawler-legacy-and-history-only` as their upstream (from before the switch to data-boar). That only affects `git push` / `git pull` when you are on those branches and run them without specifying the remote. To push such a branch to data-boar, use:

```bash
git push origin <branch-name>
```

To set the branch’s upstream to origin so future `git push` uses data-boar:

```bash
git branch --set-upstream-to=origin/<branch-name> <branch-name>
```

## Check if the legacy remote has commits not in data-boar

To see whether any commits were pushed only to the old repo (and are missing from data-boar):

```bash
git fetch origin
git fetch python3-lgpd-crawler-legacy-and-history-only

# Commits on old-repo main that are NOT in data-boar main
git log origin/main..python3-lgpd-crawler-legacy-and-history-only/main --oneline

# Commits on data-boar main that are NOT in old repo (expected: your newer work)
git log python3-lgpd-crawler-legacy-and-history-only/main..origin/main --oneline
```

If the first command lists commits, those exist only on the old repository. You can leave them as legacy history, or bring specific changes into data-boar (e.g. cherry-pick or merge) if needed.

**See also:** [GitLab read-only mirror of GitHub](GITLAB_GITHUB_MIRROR.md) — GitLab is **not** a second `origin` for PRs; it mirrors the canonical GitHub repo.

**Documentation index:** [README.md](../README.md) · [README.pt_BR.md](../README.pt_BR.md).
