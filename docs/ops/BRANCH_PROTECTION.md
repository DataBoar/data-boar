# Branch protection on `main` (operator runbook)

**Português (Brasil):** [BRANCH_PROTECTION.pt_BR.md](BRANCH_PROTECTION.pt_BR.md)

This runbook records **what GitHub actually enforces** on the default branch. It does **not** change repository settings. Re-read the live API before claiming a new check is required.

**Verified:** `gh api` on **2026-08-19** against `DataBoar/data-boar`.

Contributor-facing summary: [CONTRIBUTING.md](../../CONTRIBUTING.md) (*Pull Request requirements*). Heat tokens: [WORKFLOW_DEFERRED_FOLLOWUPS.md](WORKFLOW_DEFERRED_FOLLOWUPS.md). Quality wishlist: [QUALITY_WORKFLOW_RECOMMENDATIONS.md](../QUALITY_WORKFLOW_RECOMMENDATIONS.md) §9.

## Classic rules vs rulesets

GitHub applies **both** layers on this repo:

| Layer                                                                          | What the API showed (2026-08-19)                                                                                                                                                                                                                |
| ---                                                                            | ---                                                                                                                                                                                                                                             |
| **Classic** `GET /repos/{owner}/{repo}/branches/main/protection`               | Rule exists (not 404). **Required signatures** on. Force-push and branch deletion **off**. `enforce_admins` **off**. Conversation resolution **off**. This endpoint does **not** list the pytest required checks — those live in a **ruleset**. |
| **Ruleset** `restriction baseline` (`13887245`, **active**, `~DEFAULT_BRANCH`) | `deletion`, `non_fast_forward`, `required_signatures`.                                                                                                                                                                                          |
| **Ruleset** `main-gate-pii` (`17861726`, **active**, `~DEFAULT_BRANCH`)        | `pull_request` (see reviews below) + **required status checks**.                                                                                                                                                                                |

Classic **404 Branch not protected** would still be possible on a different repo that uses **only** rulesets. Here classic protection **and** rulesets are both present.

## Re-check:

```bash
gh api repos/DataBoar/data-boar/branches/main/protection
gh api repos/DataBoar/data-boar/rulesets
gh api repos/DataBoar/data-boar/rulesets/17861726
gh api repos/DataBoar/data-boar/rulesets/13887245
```

## Required status checks on `main`

Ruleset `main-gate-pii` → `required_status_checks` (exact `context` names):

| Required (merge-blocking) | Advisory on typical PRs (runs, not in that list)                                             |
| ---                       | ---                                                                                          |
| **Test (Python 3.12)**    | **Lint (pre-commit)**, **Bandit (strict)**, **Dependency audit**, **Dependency review (PR)** |
| **Test (Python 3.13)**    | **Test Windows (Python 3.12)**, **Ansible syntax-check**                                     |
| **Test (Python 3.14)**    | **Semgrep**, **CodeQL**, **SonarQube / SonarCloud**, **Secret scan (Gitleaks)**              |

`strict_required_status_checks_policy` is **false** (the branch need not be up to date with `main` for the required checks to count).

Windows, lint, Bandit, Semgrep, CodeQL, and Sonar are **warm** signals: they run in CI and operators treat a red job as a stop, but GitHub will still allow merge if the three Linux pytest jobs are green.

Job names come from [`.github/workflows/ci.yml`](../../.github/workflows/ci.yml) and sibling workflows. If you add a required check, wait for at least one **green** run of that exact name, then add it in the ruleset UI — do not invent names in this file.

## Reviews, CODEOWNERS, signatures

From ruleset `main-gate-pii` `pull_request` parameters (2026-08-19):

- **Required approving reviews:** `0`
- **Require code owner review:** `false`
- **Dismiss stale reviews on push:** `false`
- **Allowed merge methods:** merge, squash, rebase (repo also has `delete_branch_on_merge: true`)

[`.github/CODEOWNERS`](../../.github/CODEOWNERS) still owns PII/security gate paths ([ADR 0071](../adr/ADR-0071-self-protecting-pii-gate.md)). The ruleset does **not** yet require that review. Enabling **Require review from Code Owners** is an operator GitHub-UI change, not a docs edit.

**Required signatures** are on in **classic** protection **and** ruleset `restriction baseline`. Bot-only branches (Dependabot) that cannot sign commits need a maintainer-signed supersede PR or the handoff in [DEPENDABOT_REQUIREMENTS_SYNC.md](DEPENDABOT_REQUIREMENTS_SYNC.md) ([#1419](https://github.com/DataBoar/data-boar/issues/1419)).

## `ZIZMOR_ENFORCE`

| Fact                  | Value (2026-08-19)                                                                                                                                                                                                   |
| ---                   | ---                                                                                                                                                                                                                  |
| Repo Actions variable | **`ZIZMOR_ENFORCE=true`**                                                                                                                                                                                            |
| Workflow              | [`.github/workflows/zizmor.yml`](../../.github/workflows/zizmor.yml)                                                                                                                                                 |
| When it runs          | Every `pull_request` / `push` to `main`/`master` (**no** `paths:` filter — a `code_scanning` ruleset that requires zizmor needs a result for that commit and ref); weekly schedule; `workflow_dispatch` |
| Job behaviour         | With the variable **not** `false`, a zizmor finding **fails the job** (`ENFORCE_ZIZMOR`). That job is **not** in `required_status_checks`. Unconditional runs make a `code_scanning` tool requirement **eligible** without merge deadlock; adding zizmor back to the ruleset is a separate operator UI step. |
| Local / `check-all`   | Advisory unless `DATA_BOAR_ENFORCE_ZIZMOR` / `-Enforce` — see [WORKFLOW_DEFERRED_FOLLOWUPS.md](WORKFLOW_DEFERRED_FOLLOWUPS.md) and `scripts/workflow-security-lint.*`.                                               |

**Re-check:** `gh api repos/DataBoar/data-boar/actions/variables/ZIZMOR_ENFORCE`

Do not turn the variable **off** to silence a finding. Fix the workflow YAML (or use a documented, operator-approved exception). Same posture as other security gates.

## Heat model (cold → warm → hot)

Same tokens as [WORKFLOW_DEFERRED_FOLLOWUPS.md](WORKFLOW_DEFERRED_FOLLOWUPS.md):

| Token         | Meaning here                                                                                         |
| ---           | ---                                                                                                  |
| **cold**      | Documented only; no GitHub gate.                                                                     |
| **warm**      | CI job or habit exists; **not** a required check (or only a slice is required).                      |
| **hot**       | Named check is in the ruleset `required_status_checks` list (or equivalent fail-closed merge block). |
| **maxed_out** | Org-wide rules / attestations beyond this repo.                                                      |

**This repo (2026-08-19):** the **Branch protection** follow-up row stays **warm**. The Linux pytest matrix is already **hot**. Bump the follow-up row to **hot** only when the recommended set in QUALITY §9 (Lint, audit, Bandit, Semgrep, and any CodeQL/Sonar you intend to block on) is **required** on `main`.

## Related

- [COMMIT_AND_PR.md](COMMIT_AND_PR.md) ([pt-BR](COMMIT_AND_PR.pt_BR.md)) — local commit/PR scripts
- [GITHUB_ISSUE_CANONICAL_AND_DUPLICATE_CLOSE.md](GITHUB_ISSUE_CANONICAL_AND_DUPLICATE_CLOSE.md) — merge only with green `gh pr checks`
- [ADR 0005](../adr/ADR-0005-ci-github-actions-supply-chain-pins.md) — Actions SHA pins
- [ADR 0071](../adr/ADR-0071-self-protecting-pii-gate.md) — CODEOWNERS + gate files
