#!/usr/bin/env bash
# lint-only.sh — Linux/macOS mirror of scripts/lint-only.ps1.
# Pre-commit only (no pytest). Use for docs/style-only iterations.
# Usage (from repo root): ./scripts/lint-only.sh
# Windows: prefer .\scripts\lint-only.ps1
set -euo pipefail

REPO_ROOT=$(cd "$(dirname "$0")/.." && pwd)
cd "$REPO_ROOT" || exit 2

echo "=== lint-only: pre-commit (Ruff + format + markdown) ===" >&2
set +e
uv run pre-commit run --all-files
rc=$?
set -e
if [[ "$rc" -eq 0 ]]; then
  echo "lint-only: OK." >&2
else
  echo "lint-only: FAILED." >&2
fi
exit "$rc"
