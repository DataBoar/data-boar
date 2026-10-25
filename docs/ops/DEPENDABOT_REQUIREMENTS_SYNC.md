# Dependabot `requirements.txt` sync under `required_signatures`

**Português (Brasil):** [DEPENDABOT_REQUIREMENTS_SYNC.pt_BR.md](DEPENDABOT_REQUIREMENTS_SYNC.pt_BR.md)

GitHub issue [#1419](https://github.com/DataBoar/data-boar/issues/1419). Related: [ADR 0044](../adr/ADR-0044-dependabot-uv-ecosystem-for-pyproject-lock-closure.md), [BRANCH_PROTECTION.md](BRANCH_PROTECTION.md).

## Problem

Dependabot PRs update `uv.lock` (and sometimes `pyproject.toml`). [ADR 0030](../adr/ADR-0030-python-dependency-update-closure-single-pass.md) requires `requirements.txt` to stay in sync (`uv export --frozen --no-emit-project`). `pylock.toml` must stay in sync too (`uv export --format pylock.toml --frozen --all-extras --all-groups --output-file pylock.toml`): the CI OSV scanner reads it, so a stale export scans versions the project no longer installs ([#1937](https://github.com/DataBoar/data-boar/issues/1937)). `tests/test_dependency_artifacts_sync.py` fails on drift in either file.

The workflow [`.github/workflows/dependabot-sync.yml`](../../.github/workflows/dependabot-sync.yml) regenerates the export on those PRs. The repository ruleset **`restriction baseline`** enforces **`required_signatures`** with **no bypass** for the GitHub Actions bot. Unsigned `git push` from Actions is **rejected** — this is expected, not a misconfiguration.

## What the workflow does now

| Condition | Behaviour |
| --- | --- |
| No `requirements.txt` / `pylock.toml` drift | Job succeeds (no-op). |
| Drift, **no** signing secrets | Posts a **PR comment** with signed-commit instructions, uploads a **workflow artifact** (`requirements-txt-pr-<N>`, both exports), job **fails** (Slack notify when configured). **No unsigned push.** |
| Drift, signing secrets configured | Opens a **signed child PR** into the Dependabot branch (`ci/requirements-sync-pr-<N>`). Maintainer merges that child PR into the Dependabot branch, then lands the bump. |

Script: [`scripts/ci_dependabot_requirements_sync.sh`](../../scripts/ci_dependabot_requirements_sync.sh).

**Pwn-request hardening:** the workflow checks out the sync script from the **trusted base ref** (`pull_request.base.ref`) and only `uv.lock` / `pyproject.toml` / `requirements.txt` / `pylock.toml` from the **untrusted PR head**. The job also requires `head.ref` to match `dependabot/*`. Never run scripts or workflow YAML from the Dependabot branch when `contents: write`, `pull-requests: write`, or signing secrets are in scope.

## Operator handoff (default — no secrets)

When the sync job fails on a Dependabot PR:

1. Read the bot comment on the PR (exact `git` commands).
2. Optionally download `requirements.txt` and `pylock.toml` from the failed workflow run artifact.
3. On your workstation: fetch the Dependabot branch, run `uv export --frozen --no-emit-project -o requirements.txt` and `uv export --format pylock.toml --frozen --all-extras --all-groups --output-file pylock.toml`, **`git commit -S`**, push.
4. Or supersede the Dependabot PR with a fully signed maintainer branch ([CONTRIBUTING.md](../../CONTRIBUTING.md)).

## Optional automation — SSH commit signing (high bar)

To enable the **signed child PR** path without loosening the ruleset:

1. Create or designate a **machine GitHub user** (not a ruleset bypass).
2. Register an **SSH signing key** on that user ([GitHub docs](https://docs.github.com/en/authentication/managing-commit-signature-verification/about-commit-signature-verification)).
3. Add repository **secrets** (Settings → Secrets and variables → Actions):

| Secret | Content |
| --- | --- |
| `DEPENDABOT_SYNC_SSH_SIGNING_KEY` | Private key PEM (OpenSSH format) |
| `DEPENDABOT_SYNC_SSH_ALLOWED_SIGNERS` | One line: `ssh-ed25519 AAAA… comment` matching the public key |

4. Optional **variables** for committer identity (must match the signing user if GitHub verification requires it):

| Variable | Example |
| --- | --- |
| `DEPENDABOT_SYNC_GIT_USER_NAME` | `databoar-bot` |
| `DEPENDABOT_SYNC_GIT_USER_EMAIL` | `bot@users.noreply.github.com` |

5. Confirm a test Dependabot PR gets a child sync PR and that merging it keeps signature status **Verified**.

**Non-goals:** ruleset bypass, disabling `required_signatures`, or unsigned pushes “temporarily”.

## Re-check

```bash
gh workflow view dependabot-sync.yml
gh api repos/DataBoar/data-boar/rulesets/13887245
```
