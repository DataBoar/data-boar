#!/usr/bin/env bash
# workflow-security-lint.sh — Linux/macOS mirror of scripts/workflow-security-lint.ps1.
# Usage (from repo root): ./scripts/workflow-security-lint.sh [--enforce] [--skip-if-missing]
# Windows: prefer .\scripts\workflow-security-lint.ps1
set -euo pipefail

REPO_ROOT=$(cd "$(dirname "$0")/.." && pwd)
cd "$REPO_ROOT" || exit 2

WORKFLOWS_DIR="$REPO_ROOT/.github/workflows"
ENFORCE=0
SKIP_IF_MISSING=0

for arg in "$@"; do
  case "$arg" in
    --enforce) ENFORCE=1 ;;
    --skip-if-missing) SKIP_IF_MISSING=1 ;;
    *)
      echo "workflow-security-lint.sh: unknown option: $arg" >&2
      exit 2
      ;;
  esac
done

if [[ "${DATA_BOAR_ENFORCE_ZIZMOR:-}" == "true" ]]; then
  ENFORCE=1
fi

if [[ ! -d "$WORKFLOWS_DIR" ]]; then
  echo "workflow-security-lint: SKIP (missing $WORKFLOWS_DIR)." >&2
  exit 0
fi

run_zizmor() {
  if command -v zizmor >/dev/null 2>&1; then
    zizmor "$WORKFLOWS_DIR"
    return
  fi
  if command -v uvx >/dev/null 2>&1; then
    uvx zizmor "$WORKFLOWS_DIR"
    return
  fi
  if command -v uv >/dev/null 2>&1; then
    uv tool run zizmor "$WORKFLOWS_DIR"
    return
  fi
  return 127
}

echo "=== workflow-security-lint: zizmor on .github/workflows ===" >&2
if [[ "$ENFORCE" -eq 1 ]]; then
  echo "  Mode: enforce (fail on findings)." >&2
else
  echo "  Mode: advisory (warn on findings; use --enforce to fail)." >&2
fi

set +e
run_zizmor
code=$?
set -e

if [[ "$code" -eq 127 ]]; then
  msg="workflow-security-lint: zizmor not found (install: uv tool install zizmor, or use uvx)."
  if [[ "$SKIP_IF_MISSING" -eq 1 ]]; then
    echo "$msg SKIP (--skip-if-missing)." >&2
    exit 0
  fi
  echo "$msg" >&2
  exit 2
fi

if [[ "$code" -eq 0 ]]; then
  echo "workflow-security-lint: OK (no findings)." >&2
  exit 0
fi

if [[ "$ENFORCE" -eq 1 ]]; then
  echo "workflow-security-lint: FAILED (zizmor exit $code, enforcement on)." >&2
  exit "$code"
fi

echo "workflow-security-lint: WARN (zizmor exit $code, advisory mode)." >&2
echo "  Re-run with --enforce or set DATA_BOAR_ENFORCE_ZIZMOR=true to fail on findings." >&2
exit 0
