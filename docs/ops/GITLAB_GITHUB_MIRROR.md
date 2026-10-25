# GitLab mirror of GitHub (read-only mirror, single source of truth)

**Português (Brasil):** [GITLAB_GITHUB_MIRROR.pt_BR.md](GITLAB_GITHUB_MIRROR.pt_BR.md)

## 1. What this is for

- **GitHub** remains the **only** place where humans open PRs and merge (canonical history).
- **GitLab** holds a **read-only mirror** of the same Git repository (same commits and tags).
- **Goals:** extra redundancy, optional **second CI** on GitLab, visibility on another host — **without** two diverging histories.

**Non-goals:** duplicating Issues, Discussions, or PR workflows on GitLab unless you explicitly want that later.

---

## 2. Prerequisites

| Item        | Notes                                                                                                                           |
| ----        | -----                                                                                                                           |
| GitHub repo | Exists; you have **Admin** (or enough rights to add secrets / webhooks if needed).                                              |
| GitLab      | Empty or disposable project under your account/group (e.g. **data-boar**), same default branch name as GitHub (usually `main`). |
| Decision    | Pick **one** sync method below (A or B). Do **not** configure both to push in opposite directions.                              |

---

## 3. Option A — GitLab pulls from GitHub (recommended for “fire and forget”)

GitLab periodically (or on trigger) **fetches** from GitHub. No push from developers to GitLab.

### 3.1 Manual steps (GitLab UI)

1. Open the **GitLab project** (empty repo, same branch name as GitHub).
1. Go to **Settings → Repository → Mirroring repositories** (exact path may vary slightly by GitLab version).
1. **Add new mirror:**
   - **Git repository URL:** HTTPS URL of the GitHub repo, e.g. `<https://github.com/><org>/<repo>.git`
   - **Mirror direction:** **Pull**
   - **Authentication:** use a **GitHub Personal Access Token (classic)** with **`repo`** scope (read-only is enough for **public** repos; **private** repos need access).
1. Save. Use **“Update now”** / **“Sync”** once to test.
1. Set **mirror interval** if offered (e.g. every few minutes) or rely on manual sync + optional webhook (GitHub → GitLab) depending on your GitLab tier.

### 3.2 GitHub token (for private repos)

1. GitHub → **Settings → Developer settings → Personal access tokens**.
1. Create a token with at least **`repo`** (read) for that repository.
1. **Never** commit the token. Paste it only into GitLab’s mirror credential field or GitHub Actions secrets.

### 3.3 Lock GitLab against human pushes (strongly recommended)

1. **Settings → Repository → Protected branches:** protect `main` (and any release branches) so **no one** can push except **Maintainers** — or restrict pushes to **no roles** and rely on mirror-only updates (depends on GitLab edition; at minimum disable **Allowed to push** for Developers).
1. **Settings → General → Visibility:** set as needed (often **Private** mirror of a public GitHub repo is fine).

---

## 4. Option B — GitHub Actions pushes to GitLab

Every push to `main` on GitHub runs a workflow that **pushes** refs to GitLab.

### 4.1 GitLab side

1. Create **Deploy key** (read-write for this repo only) **or** **Project Access Token** with **`write_repository`**.
1. Add the public key to GitLab **Settings → Repository → Deploy keys** (if using SSH), **or** store HTTPS token for CI.
1. Keep GitLab branch protection consistent with “mirror only” (same as §3.3).

### 4.2 GitHub side

1. Repo → **Settings → Secrets and variables → Actions**.
1. Add secrets, for example:
   - `GITLAB_SSH_PRIVATE_KEY` (if SSH push), **or**
   - `GITLAB_USERNAME` + `GITLAB_TOKEN` (if HTTPS push).
1. Add workflow file (example name: `.github/workflows/mirror-to-gitlab.yml`) that runs on `push` to `main` and executes `git push gitlab main` (and tags if desired). **Do not** paste real secrets into the YAML; reference `${{ secrets.* }}` only.

**Note:** Implementing the exact workflow is a separate commit; this document describes **what** to configure. Ask the assistant or maintainer for a minimal workflow when secrets are ready.

---

## 5. Which option to choose

| Situation                                        | Prefer                                                 |
| ---------                                        | ------                                                 |
| Want minimal GitHub changes                      | **A (GitLab pull)**                                    |
| Want near-instant mirror after every GitHub push | **B (Actions push)** or **A + webhook** (if available) |
| Avoid storing GitHub PAT on GitLab               | **B** (GitLab only receives pushes)                    |

---

## 6. Dual CI (GitHub Actions + GitLab CI)

- **Possible:** both run on the same commits once the mirror is up to date.
- **Cost:** duplicate minutes, duplicate secrets (Sonar, test tokens, etc.).
- **Recommendation:** mirror first; enable **`.gitlab-ci.yml`** only when you are ready to maintain **parity** with GitHub workflows (or a **subset** of jobs).

---

## 7. Verification (no secrets in chat)

1. After sync, compare **commit SHA** on GitHub `main` and GitLab `main` (same value).
1. Compare **latest tag** if you mirror tags (some mirror setups need **“mirror all refs”** or a separate tag push job).

---

## 8. Homelab / lab-op (optional)

- **Not required** for mirroring: GitHub and GitLab handle sync in the cloud.
- **Optional:** a small script on the LAN (or a scheduled CI job) that **compares** `git ls-remote` URLs and alerts if SHAs diverge beyond N minutes — useful as a **health** check, not as the primary sync mechanism.

---

## 9. Troubleshooting

| Symptom           | Check                                                                                              |
| -------           | -----                                                                                              |
| Mirror fails auth | Token scope, expiry, 2FA, IP allowlists.                                                           |
| Empty GitLab repo | Default branch name mismatch (`main` vs `master`).                                                 |
| Drift             | Someone pushed to GitLab; remove write access; reset GitLab project from GitHub once (maintainer). |

---

## 10. Related docs

- [REMOTES_AND_ORIGIN.md](REMOTES_AND_ORIGIN.md) — local `git remote` habits; mirror does not replace `origin` on developer machines.
- [COMMIT_AND_PR.md](COMMIT_AND_PR.md) — PR flow stays on GitHub.

---

## 11. Hard lock policy (minimum anti-chaos baseline)

Apply these controls in GitLab so it cannot become an alternate truth source:

1. **Disable direct pushes** to default branch for all human roles below Maintainer.
1. Protect `main` and set:
   - **Allowed to merge:** Maintainers only (or no merge if mirror-only project),
   - **Allowed to push:** no one except mirror automation identity.
1. **Disable force push** on protected branches.
1. Disable or restrict **web IDE edits** and **manual pipelines from arbitrary refs** where possible.
1. Keep project **Private** unless you have an explicit public mirror policy.
1. Use a dedicated machine account/token for mirror writes; rotate regularly.
1. Keep Issues/MRs disabled if this repository is strictly mirror + CI.

If any of the above is not supported by your GitLab tier, document the compensating control in private ops notes.

---

## 12. Recommended architecture (safe default)

- **GitHub:** source of truth, PR, merge, release, tags.
- **GitLab:** mirror + optional extra pipeline only.
- **No human write path to GitLab default branch.**
- **No bidirectional mirroring.**

Flow:

1. Human merges PR in GitHub.
1. Mirror updates GitLab (pull or Actions push).
1. GitLab CI runs additional non-blocking checks.
1. Findings return to GitHub as issues/comments or private operator notes.

---

## 13. Mirror health check (scripted)

Use `scripts/gitlab-mirror-health-check.ps1` to compare `origin/main` and GitLab mirror SHA:

```powershell
.\scripts\gitlab-mirror-health-check.ps1 -GitLabRepoUrl "git@gitlab.com:<group>/<repo>.git"
```

Optional tolerance window can be used before raising alerts.
