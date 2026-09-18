#!/usr/bin/env bash
# Strict gitleaks git scan — root .gitleaks.toml bypass removed (issue #1933).
set -Eeuo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

# shellcheck source=scripts/db-tool-bootstrap.sh
source "$REPO_ROOT/scripts/db-tool-bootstrap.sh"

db_ensure_gitleaks || {
  echo "run-gitleaks-strict: gitleaks unavailable (bootstrap failed)" >&2
  exit 1
}

policy="${DB_GITLEAKS_POLICY_CONFIG}"
if [[ ! -f "$policy" ]]; then
  echo "run-gitleaks-strict: missing maintainer policy ${policy}" >&2
  exit 1
fi

rm -f .gitleaks.toml .gitleaksignore

gitleaks git . \
  --config "$policy" \
  --no-banner \
  --redact \
  --exit-code 1 \
  --ignore-gitleaks-allow
