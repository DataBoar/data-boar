#!/usr/bin/env bash
# Example: Session B — git-filter-repo on a Linux lab node (copy to docs/private/scripts/ and adapt).
# Never run on the primary Windows canonical clone. Operator sets DATA_BOAR_ALLOW_DESTRUCTIVE_REPO_OPS=1
# only on the designated host. See docs/ops/PRIMARY_WINDOWS_WORKSTATION_PROTECTION.md and
# docs/ops/PII_PUBLIC_TREE_OPERATOR_GUIDE.md (history rewrite).
#
# After rewrite, record:
#   git count-objects -v   (before vs after)
#   git rev-parse HEAD     (must change)
#   du -sh .git
#
set -euo pipefail

REPO_ROOT="${REPO_ROOT:-${HOME}/Projects/dev/data-boar}"
EXPR="${REPO_ROOT}/scripts/filter_repo_pii_replacements.txt"

echo "session-b: REPO_ROOT=${REPO_ROOT}"
echo "session-b: replace rules from ${EXPR}"
test -f "${EXPR}" || { echo "missing ${EXPR}" >&2; exit 1; }

cd "${REPO_ROOT}"

echo "=== BEFORE ==="
git rev-parse HEAD
du -sh .git || true
git count-objects -v || true

if [[ "${DATA_BOAR_ALLOW_DESTRUCTIVE_REPO_OPS:-0}" != "1" ]]; then
  echo "Refusing: export DATA_BOAR_ALLOW_DESTRUCTIVE_REPO_OPS=1 on this lab host only when rewriting history." >&2
  exit 1
fi

command -v git-filter-repo >/dev/null 2>&1 || { echo "git-filter-repo not on PATH" >&2; exit 1; }

# Order matters: run tracked regex bundle FIRST, then operator-private literals (otherwise
# private name replacements can be overwritten by a second pass of generic rules).
git filter-repo --force \
  --replace-text "${REPO_ROOT}/scripts/filter_repo_pii_replacements.txt" \
  --replace-text "${HOME}/pii-private-replacements.filtered.txt"

echo "=== AFTER ==="
git rev-parse HEAD
du -sh .git || true
git count-objects -v || true

echo "session-b: run uv run python scripts/pii_history_guard.py --full-history && uv run pytest -q"
