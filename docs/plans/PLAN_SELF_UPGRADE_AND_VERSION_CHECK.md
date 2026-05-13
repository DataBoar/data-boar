# Plan: Version check and self-upgrade (with container-aware behaviour)

**Status:** Deferred
**Date:** 2026-03-15
**Authors:** Fabio Leitao
**Priority:** H3

**Related:** [PLAN_BUILD_IDENTITY_RELEASE_INTEGRITY.md](PLAN_BUILD_IDENTITY_RELEASE_INTEGRITY.md) — **local** build string (`release` vs `dev`, optional manifest) shown at startup and in the dashboard; this plan focuses on **remote** “latest” and **upgrade** paths.

**Synced with:** [PLANS_TODO.md](PLANS_TODO.md) (central to-do list)

## When implementing steps: update docs and tests; then update PLANS_TODO.md and this file.

This plan adds a way for the app to **check for a stable new release** (GitHub), optionally **self-upgrade** when run on bare metal or in a venv, and when running inside **Docker or Kubernetes** to **inform the operator** with upgrade instructions and release notes instead of modifying the container. It ensures **no loss of scan data, reports, or heatmaps**; **no downgrades** unless explicitly forced; and an **audit trail** of upgrades (who, when, from/to version, config scope) similar to the existing wipe log.

---

## Goals

- **Version check:** Allow the app to verify if a stable new release is available (GitHub: releases or a well-known scheme).
- **Triggers:** Scheduled (cron or internal scheduler), API route (e.g. GET /check-update, optional POST /upgrade with confirmation), and CLI args (e.g. `--check-update`, `--upgrade`).
- **Self-upgrade (non-container):** When not in Docker/Kubernetes, allow upgrading to the new version (or an intermediate version if needed), preserving config, regex/ML/DL overrides, credentials and secrets, and data (SQLite, reports, heatmaps). Behaviour similar to a safe “apt full-upgrade” or Windows update: backup settings, apply new code, restore settings, restart.
- **Container-aware:** When the app detects it is running inside Docker or Kubernetes, **do not** attempt in-place self-upgrade. Instead: report that a newer version is available, show a short description of important changes (from release notes), and give the operator **Docker or Kubernetes commands** to pull and replace the running image (per [docs/deploy/DEPLOY.md](deploy/DEPLOY.md) and Docker Hub).
- **No regressions:** Upgrades must not break the app; settings and data must be preserved. **Downgrades are disallowed** unless the operator uses a **`--force`** (or similar) flag, due to the risk of reintroducing bugs and regressions.
- **Data and audit:** Do **not** cause loss of previous scan sessions, reports, or heatmaps (a separate `--reset-data` already exists for intentional wipe). Protect collected data; keep trends and evolution. Maintain an **upgrade audit log** (who asked for upgrade, when, initial version, resulting version, important config summary, mapped targets) analogous to `data_wipe_log`.

---

## Current state

- **Version:** From `pyproject.toml` and `core/about.py` (major.minor.build, e.g. 1.5.2). Single source of truth: package metadata.
- **Wipe:** `--reset-data` wipes SQLite sessions/findings/failures and deletes report/heatmap files; **data_wipe_log** records reason and timestamp. Upgrade must **never** call wipe logic unless the user explicitly runs `--reset-data`.
- **Config:** Loaded from YAML/JSON; paths for `regex_overrides_file`, `ml_patterns_file`, `dl_patterns_file`; config can contain credentials (see [PLAN_SECRETS_VAULT.md](PLAN_SECRETS_VAULT.md)).
- **Deploy:** Docker Hub `fabioleitao/data_boar:latest` and version tags (e.g. `1.5.1`); Kubernetes uses same image. Upgrading in containers is “pull new image and replace container/pod”.
- **Releases:** GitHub repo (e.g. FabioLeitao/data-boar); releases/tags and [GitHub Releases](https://github.com/FabioLeitao/data-boar/releases) page. Release notes in `docs/releases/*.md`.

---

## 1. Version source (stable release detection)

**Recommended scheme:** Use **GitHub Releases API** as the source of “stable” version.

- **Endpoint:** `GET <https://api.github.com/repos/FabioLeitao/data-boar/releases/lates>t` (or a specific repo URL from config/env so forks can point to their own repo). Response includes `tag_name` (e.g. `v1.5.2` or `1.5.2`) and `body` (release notes).
- **Alternative:** A well-known file in the repo (e.g. `VERSION` or `docs/STABLE_VERSION`) that contains the current stable version string; the app would fetch the raw file from the default branch (e.g. `<https://raw.githubusercontent.com/FabioLeitao/data-boar/main/VERSIO>N`). Prefer **Releases API** so we get tags and notes in one call.
- **Version comparison:** Parse current (from `core/about.py`) and latest (from API or file) as `major.minor.build`; “newer” means strictly greater (no downgrade unless `--force`).
- **Stability:** Consider only **latest** release as “stable” (GitHub “latest” release), or allow config to pin to a specific version channel (e.g. “only notify for 1.x”) in a later iteration.

| #   | To-do                                                                                                                                                                                                                  | Status    |
| --- | -----                                                                                                                                                                                                                  | ------    |
| 1.1 | Define repo URL for version check (config or env, e.g. `upgrade.repo_url` or `GITHUB_REPO`; default FabioLeitao/data-boar).                                                                                            | ⬜ Pending |
| 1.2 | Implement version fetch: call GitHub Releases API (or fetch well-known file), parse latest tag/version, compare with current from `core/about.py`. Handle network errors and rate limits (cache result for N minutes). | ⬜ Pending |
| 1.3 | Expose “current” and “latest” (if newer) and “release notes” (short excerpt, e.g. first 500 chars of body) for CLI and API.                                                                                            | ⬜ Pending |

---

## 2. Triggers: CLI, API, and optional schedule

| #   | To-do                                                                                                                                                                                                                                                                                                                                                                                                                       | Status    |
| --- | -----                                                                                                                                                                                                                                                                                                                                                                                                                       | ------    |
| 2.1 | **CLI:** Add `--check-update`: only check and print whether a newer version exists; if yes, print version and short release notes; if in container, print Docker/Kubernetes upgrade commands (see section 4). Exit 0; do not upgrade.                                                                                                                                                                                       | ⬜ Pending |
| 2.2 | **CLI:** Add `--upgrade`: check for newer version; if not in container, proceed with self-upgrade (see section 3); if in container, print message and container upgrade commands and exit without changing the image. Require confirmation (e.g. “Type 'yes' to upgrade”) unless `--yes`/non-interactive. **No downgrade** unless `--force` is also passed.                                                                 | ⬜ Pending |
| 2.3 | **API:** Add GET `/check-update` (or `/version/check`): returns JSON `{ "current": "1.5.2", "latest": "1.5.3", "update_available": true, "release_notes_excerpt": "...", "in_container": true, "container_upgrade_commands": { "docker": "...", "kubernetes": "..." } }`. No side effects; cache result for a few minutes.                                                                                                  | ⬜ Pending |
| 2.4 | **API:** Optional POST `/upgrade` (or `/version/upgrade`): when **not** in container, trigger self-upgrade flow (backup, upgrade, restore, then ask operator to restart process or return “upgrade prepared, please restart”); when in container, return 400 or 409 with message and container commands. Require API key if `require_api_key` is true. **No downgrade** unless a query/body flag like `force=true` is sent. | ⬜ Pending |
| 2.5 | **Schedule:** Optional: document how to call `--check-update` or GET `/check-update` from cron or a task runner; or add an optional in-process “check every N hours” and expose result on dashboard. No automatic upgrade without explicit user/operator action.                                                                                                                                                            | ⬜ Pending |

---

## 3. Self-upgrade (bare metal / venv only)

When the app runs **outside** Docker/Kubernetes (e.g. direct Python, venv, system install):

| #   | To-do                                                                                                                                                                                                                                                                                                                                                                                                                                                              | Status    |
| --- | -----                                                                                                                                                                                                                                                                                                                                                                                                                                                              | ------    |
| 3.1 | **Backup:** Before upgrading, write a **temporary backup** of: current config file (full path from CONFIG_PATH or --config); contents (or paths) of `regex_overrides_file`, `ml_patterns_file`, `dl_patterns_file` if present; and a small **upgrade manifest** (current version, timestamp, config path, sqlite_path, report.output_dir, list of target names/types—no secrets). Store in a temp dir or a known location (e.g. `./.upgrade_backup_<timestamp>/`). | ⬜ Pending |
| 3.2 | **Upgrade method:** Prefer **git pull + reinstall** when running from a git clone (detect `.git`); otherwise **download release artifact** (e.g. source tarball from GitHub release) and reinstall with `uv sync` or `pip install -e .` from the extracted dir. Target the **latest** release version (or next stable); no downgrade unless `--force`.                                                                                                             | ⬜ Pending |
| 3.3 | **Restore:** After new code is in place, ensure config path and override file paths still point to the same content (or copy from backup if paths changed). Do **not** overwrite SQLite or report/output dirs; they remain untouched. Credentials and secrets in config (or vault) are preserved by backup/restore of config.                                                                                                                                      | ⬜ Pending |
| 3.4 | **Audit log:** Add an **upgrade log** table (e.g. `upgrade_log`) or reuse/extend a generic “maintenance log”: columns such as `upgraded_at`, `from_version`, `to_version`, `reason` (e.g. “CLI --upgrade”), `config_path`, `targets_summary` (e.g. count and types), `backup_path`. Same idea as `data_wipe_log`: immutable record of who asked for what when and what the state was.                                                                              | ⬜ Pending |
| 3.5 | **Restart:** After upgrade, the process may need to restart to load new code. Document: “Upgrade complete; please restart the API/CLI (e.g. restart systemd service or run main.py again).” Do not kill the process from inside the upgrade step unless design explicitly requires it (e.g. optional “restart now” flag).                                                                                                                                          | ⬜ Pending |

---

## 4. Container detection and operator instructions (Docker / Kubernetes)

When the app detects it is running inside Docker or Kubernetes, **do not** perform in-place self-upgrade.

| #   | To-do                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   | Status                                   |           |
| --- | -----                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   | ------                                   |           |
| 4.1 | **Detection:** Consider “in container” if: `/.dockerenv` exists, or `KUBERNETES_SERVICE_HOST` is set, or a well-known env (e.g. `KUBERNETES_SERVICE_HOST`, `CONTAINER`) is present. Expose `in_container: true/false` and optionally `runtime: "docker"                                                                                                                                                                                                                                                 | "kubernetes"` in version-check response. | ⬜ Pending |
| 4.2 | **Message and release notes:** When update is available and in container, return (CLI and API) a short message: “A newer version X.Y.Z is available. You are running in Docker/Kubernetes; please upgrade the image instead of in-place upgrade.” Include a **short description of important changes** (e.g. first 500–1000 chars of release notes from GitHub, or link to release notes).                                                                                                              | ⬜ Pending                                |           |
| 4.3 | **Docker commands:** Document and return in API/CLI: `docker pull fabioleitao/data_boar:latest` (or version tag); then “Stop and remove the current container, then run a new container with the same volume mounts and env (e.g. CONFIG_PATH, /data).” Example: `docker stop <name>; docker rm <name>; docker run -d -p 8088:8088 -v "$(pwd)/data:/data" -e CONFIG_PATH=/data/config.yaml fabioleitao/data_boar:latest`. Image name can come from config or default per [DEPLOY.md](deploy/DEPLOY.md). | ⬜ Pending                                |           |
| 4.4 | **Kubernetes commands:** Document and return: “Update the image in your Deployment (e.g. `kubectl set image deployment/<name> <container>=fabioleitao/data_boar:latest`) or edit the manifest and apply; then rollout (e.g. `kubectl rollout restart deployment/<name>`). Ensure persistent volume for /data (config, SQLite, reports) is unchanged.”                                                                                                                                                   | ⬜ Pending                                |           |

---

## 5. Downgrade and force flag

| #   | To-do                                                                                                                                                                                                                                        | Status    |
| --- | -----                                                                                                                                                                                                                                        | ------    |
| 5.1 | **Default: no downgrade.** When “latest” is **lower** than current version (or equal), do not offer upgrade and do not run upgrade. Return “You are already on the latest (or newer) version.”                                               | ⬜ Pending |
| 5.2 | **Force flag:** CLI: `--upgrade --force` allows downgrade (e.g. to latest release even if it is lower). API: `POST /upgrade?force=true` (or body). Document risk: “Downgrading may reintroduce bugs and regressions; use only if necessary.” | ⬜ Pending |

---

## 6. Data and config protection

| #   | To-do                                                                                                                                                                                                                                                                                                                    | Status    |
| --- | -----                                                                                                                                                                                                                                                                                                                    | ------    |
| 6.1 | **No data loss:** Upgrade logic must **never** call `wipe_all_data` or delete SQLite, reports, or heatmaps. The only way to wipe remains `--reset-data` (and any future explicit wipe API). Preserve `sqlite_path`, `report.output_dir`, and all files under them (except what the user explicitly deletes via wipe).    | ⬜ Pending |
| 6.2 | **Config and overrides:** Backup and restore ensure that `config.yaml` (and paths to `regex_overrides_file`, `ml_patterns_file`, `dl_patterns_file`) and their contents (or references) are reapplied after upgrade so that “look and feel,” capabilities, credentials and secrets, and mapped targets remain effective. | ⬜ Pending |
| 6.3 | **Audit trail:** Upgrade log records: who triggered (CLI user, API caller if identifiable), when, from_version, to_version, config_path, optional targets_summary (e.g. “3 database, 2 filesystem”), backup_path. Keeps an audit trail of upgrades alongside wipe log.                                                   | ⬜ Pending |

---

## 7. Testing and documentation

| #   | To-do                                                                                                                                                                                                                                                                                                              | Status    |
| --- | -----                                                                                                                                                                                                                                                                                                              | ------    |
| 7.1 | **Tests:** Unit tests for version comparison (newer, equal, older); for “in container” detection (mock env/filesystem); for backup manifest content (no secrets in manifest). Integration test: mock GitHub API response and assert /check-update and --check-update output.                                       | ⬜ Pending |
| 7.2 | **Docs:** Update USAGE (EN and pt-BR) with `--check-update`, `--upgrade`, `--force`; GET `/check-update` and optional POST `/upgrade`; container behaviour and Docker/Kubernetes commands. Update DEPLOY.md to reference “upgrade” section. Add short “Version check and upgrade” section to README or TECH_GUIDE. | ⬜ Pending |
| 7.3 | **Release notes:** When publishing a release, ensure GitHub Release has tag and body so the version-check flow can show useful excerpt to operators.                                                                                                                                                               | ⬜ Pending |

---

## 8. Order of execution (recommended)

1. **Version source and comparison** (1.1–1.3).
1. **Container detection and “no upgrade in container”** (4.1–4.4) so CLI/API can return correct message and commands.
1. **CLI --check-update and --upgrade** (2.1, 2.2) and **API GET /check-update** (2.3).
1. **Backup and upgrade log** (3.1, 3.4, 6.1–6.3).
1. **Self-upgrade steps** (3.2, 3.3, 3.5) and **no downgrade / --force** (5.1, 5.2).
1. **Optional POST /upgrade** (2.4) and **schedule** (2.5).
1. **Tests and docs** (7.1–7.3).

---

## Alternatives or simplifications

- **No self-upgrade in first iteration:** Only implement version check and container instructions; operators always upgrade manually (pip/uv/git or container pull). Reduces risk and complexity.
- **Well-known file instead of API:** If GitHub API rate limits or auth are a concern, use a static file (e.g. `VERSION` or `docs/STABLE_VERSION`) on the default branch; no release notes excerpt unless we add a second file (e.g. `LATEST_RELEASE_NOTES.txt`).
- **Upgrade log in same DB:** Reuse or extend a single “maintenance_events” table (wipe, upgrade) with an `event_type` column instead of a separate upgrade_log table, so one place to query “what happened when.”

---

## 9. Alternative delivery: package-manager and signed artifacts (winget-like, .deb, apt)

### 9.1 Does it make sense? Does it fit our goals?

- **Yes.** A **.deb package** installable via **apt** and **dpkg** gives operators a familiar, auditable upgrade path: `apt update && apt upgrade data-boar` (or a dedicated package name). Version check can still use GitHub Releases (or a simple file in our repo); the *delivery* mechanism becomes apt instead of (or in addition to) pip/uv/git/tarball.
- **Winget-like UX:** Same idea as winget: one place to check for updates, one command to upgrade, with optional automatic checks. Our existing version-check and self-upgrade design (sections 1–7) already supports "check then upgrade"; adding .deb is another *source* for the upgraded bits (like "download tarball" vs "apt install").

### 9.2 Safety and signing

- **Own apt repository:** We can host a small apt repo (e.g. on GitHub Pages, or a minimal server) with a **signed** package list and .deb files. **Signing .deb** (e.g. with GPG) and publishing the public key lets `apt` verify integrity and origin; this is standard and safe.
- **HTTPS:** Serve the repo over HTTPS so transport is protected. No need to ship private keys; only the public key is distributed (e.g. in docs or a one-line setup script).

### 9.3 Not shipping readable .py (bytecode / compiled artifact)

- **Goal:** Avoid distributing plain `.py` source in the installed artifact so that the deployed app is not trivially human-readable. Options:
- **.pyc (bytecode):** Package only `.pyc` (and necessary resources) in the .deb. Python can run from bytecode. **Caveat:** .pyc is reversible (decompilers exist); it reduces casual reading and keeps source out of the default install path, but is not strong obfuscation.
- **Other abstraction:** PyInstaller/cx_Freeze produce a single executable or a tree of .pyc + runtime; we could build such an artifact and then package *that* in the .deb so the installed filesystem has no raw .py. Same caveat: determined users can still inspect.
- **Fits our goals:** Yes—we can document that "the .deb install does not include plain .py source, only bytecode (or a built artifact)" for deployments that prefer not to expose source. Fits compliance and "controlled distribution" narrative; no change to open-source repo (source stays on GitHub).

### 9.4 Where it sits in the plan and sequence

- **Fits in this plan:** Version check & self-upgrade already defines *how* we check and *how* we upgrade (backup, replace code, restore, audit). Adding .deb is an **alternative delivery mechanism**: "upgrade" can mean "apt upgrade" when the app was installed from our apt repo. Version-check logic (GitHub API or well-known file) and container-aware behaviour stay the same.
- **Token-aware / complexity–gain:** This is **higher complexity** (packaging, repo hosting, GPG, possibly CI to build .deb and publish). **High gain** for Linux/enterprise and for a "winget-like" story. So: **do core version check and self-upgrade first** (sections 1–7); then consider this as an **optional Phase 9** (or a separate "Delivery: .deb/apt" slice) when capacity allows, after the main upgrade flow is in place.

### 9.5 Name availability and dependencies

- **Package name:** Ensure the **deb package name is available** (e.g. `data-boar`): check that it is not already taken in Debian/Ubuntu official repos or in other well-known third-party repos we might conflict with. If we host our own repo only, we control the name; still document the chosen name and any naming rationale (e.g. matches Docker image, no clash with existing packages).
- **Dependencies in the .deb:** The package can **declare dependencies** (e.g. Python 3.12+, `libpq5`, `libffi8`, etc.) so that `apt install data-boar` (or `apt upgrade data-boar`) pulls in required system libs. Optionally we can also bundle or depend on a fixed set of Python deps (e.g. via a virtualenv inside the package or declared as deb deps) for **easy deployment** in one step without separate pip/uv installs.

### 9.6 To-dos (optional phase; implement after sections 1–7)

| #   | To-do                                                                                                                                                                                                                                                                                                                                                                                                                       | Status    |
| --- | -----                                                                                                                                                                                                                                                                                                                                                                                                                       | ------    |
| 9.1 | **.deb packaging:** Define package name (e.g. `data-boar`); **confirm name is available** (not taken in Debian/Ubuntu or conflicting repos). Define dependencies (system and optionally Python) for easy deployment, install layout (e.g. `/usr/lib/data-boar` or FHS), and build .deb (e.g. with `dpkg-deb` / `dh` or a small script). Prefer shipping bytecode (.pyc) or a built artifact only—no raw .py in the package. | ⬜ Pending |
| 9.2 | **Apt repository:** Host an apt repo (e.g. GitHub Pages or minimal server) with `dists/` and `pool/` (or flat structure); provide `Release` and `Packages` (and optionally `Packages.gz`). Document how to add the repo (e.g. `deb <https://.../data-boar> stable main`).                                                                                                                                                   | ⬜ Pending |
| 9.3 | **Signing:** Sign the `Release` file (and optionally .deb) with GPG; publish the public key and document one-line setup (add repo + apt-key or signed-by). Ensure apt verification works on a clean Debian/Ubuntu system.                                                                                                                                                                                                   | ⬜ Pending |
| 9.4 | **Version check and upgrade UX:** When version check runs and a newer release is available, if the app was installed from .deb, show message: "Run `sudo apt update && sudo apt upgrade data-boar` (or equivalent)." Optionally detect install method (e.g. presence of a marker file or package database) to tailor the message.                                                                                           | ⬜ Pending |
| 9.5 | **Docs and tests:** Document the .deb install path, repo URL, and signing in USAGE and DEPLOY; add a short "Package-manager install (apt)" section. Add CI or release-step to build and publish .deb when we cut a release.                                                                                                                                                                                                 | ⬜ Pending |

---

*Last updated: plan created; section 9 added for optional .deb/apt/signing/bytecode. Update this doc when completing steps or when version/upgrade behaviour changes.*
