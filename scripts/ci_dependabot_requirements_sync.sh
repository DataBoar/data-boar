#!/usr/bin/env bash
# Regenerate requirements.txt on Dependabot PRs under required_signatures (#1419).
# Default (no signing secret): PR comment + exit 1 — never unsigned git push.
# Optional: DEPENDABOT_SYNC_SSH_SIGNING_KEY opens a signed child PR into the Dependabot branch.
set -euo pipefail

PR_NUMBER="${GITHUB_EVENT_PULL_REQUEST_NUMBER:?}"
HEAD_REF="${GITHUB_EVENT_PULL_REQUEST_HEAD_REF:?}"

uv export --frozen --no-emit-project -o requirements.txt

if ! git status --porcelain requirements.txt | grep -q .; then
  echo "No changes to requirements.txt"
  exit 0
fi

echo "requirements.txt drift detected for PR #${PR_NUMBER}"

post_handoff_comment() {
  gh pr comment "${PR_NUMBER}" --body "$(cat <<EOF
## requirements.txt drift (unsigned push blocked)

\`uv.lock\` / \`pyproject.toml\` changed but GitHub Actions **cannot** push an unsigned commit under the \`required_signatures\` ruleset ([#1419](https://github.com/DataBoar/data-boar/issues/1419)).

**Option A — signed commit on this Dependabot branch:**
\`\`\`bash
git fetch origin pull/${PR_NUMBER}/head:dependabot-review
git checkout dependabot-review
uv export --frozen --no-emit-project -o requirements.txt
git add requirements.txt
git commit -S -m "chore(deps): regenerate requirements.txt after uv.lock update"
git push origin "HEAD:<dependabot-branch-name>"
\`\`\`

**Option B — supersede PR:** apply the bump + export locally with signed commits (see [CONTRIBUTING.md](https://github.com/DataBoar/data-boar/blob/main/CONTRIBUTING.md)).

Download the CI-generated \`requirements.txt\` from the **workflow artifact** on this run when present.
EOF
)"
}

if [[ -z "${DEPENDABOT_SYNC_SSH_SIGNING_KEY:-}" ]]; then
  post_handoff_comment
  echo "::error::requirements.txt drift; configure DEPENDABOT_SYNC_SSH_SIGNING_KEY for signed child PRs, or apply manually (#1419)."
  exit 1
fi

if [[ -z "${DEPENDABOT_SYNC_SSH_ALLOWED_SIGNERS:-}" ]]; then
  post_handoff_comment
  echo "::error::DEPENDABOT_SYNC_SSH_SIGNING_KEY is set but DEPENDABOT_SYNC_SSH_ALLOWED_SIGNERS is missing."
  exit 1
fi

SIGNING_KEY_FILE="${RUNNER_TEMP}/dependabot_sync_signing_key"
ALLOWED_SIGNERS_FILE="${RUNNER_TEMP}/dependabot_sync_allowed_signers"
umask 077
printf '%s\n' "${DEPENDABOT_SYNC_SSH_SIGNING_KEY}" >"${SIGNING_KEY_FILE}"
printf '%s\n' "${DEPENDABOT_SYNC_SSH_ALLOWED_SIGNERS}" >"${ALLOWED_SIGNERS_FILE}"

git config --local gpg.format ssh
git config --local user.signingkey "${SIGNING_KEY_FILE}"
git config --local gpg.ssh.allowedSignersFile "${ALLOWED_SIGNERS_FILE}"
git config --local commit.gpgsign true
git config --local user.name "${DEPENDABOT_SYNC_GIT_USER_NAME:-github-actions[bot]}"
git config --local user.email "${DEPENDABOT_SYNC_GIT_USER_EMAIL:-41898282+github-actions[bot]@users.noreply.github.com}"

SYNC_BRANCH="ci/requirements-sync-pr-${PR_NUMBER}"
git checkout -b "${SYNC_BRANCH}"
git add requirements.txt
git commit -S -m "chore(deps): regenerate requirements.txt for Dependabot PR #${PR_NUMBER}"

git push origin "HEAD:${SYNC_BRANCH}"

CHILD_URL="$(gh pr create \
  --base "${HEAD_REF}" \
  --head "${SYNC_BRANCH}" \
  --title "chore(deps): requirements.txt sync for Dependabot PR #${PR_NUMBER}" \
  --body "$(cat <<EOF
Automated \`requirements.txt\` export for Dependabot PR #${PR_NUMBER}.

**Merge this PR into the Dependabot branch** (\`${HEAD_REF}\`) before landing the dependency bump. Signed commits only — no unsigned push to protected refs ([#1419](https://github.com/DataBoar/data-boar/issues/1419)).
EOF
)")"

gh pr comment "${PR_NUMBER}" --body "Opened signed requirements.txt sync PR: ${CHILD_URL}"
echo "Created child PR: ${CHILD_URL}"
