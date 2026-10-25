#!/usr/bin/env bash
# pre-commit-and-tests.sh — Linux/macOS mirror of scripts/pre-commit-and-tests.ps1.
# Runs pre-commit (unless skipped) then full pytest with warnings as errors.
# Usage (from repo root):
#   ./scripts/pre-commit-and-tests.sh
#   ./scripts/pre-commit-and-tests.sh --skip-pre-commit
# Windows: prefer .\scripts\pre-commit-and-tests.ps1
set -euo pipefail

REPO_ROOT=$(cd "$(dirname "$0")/.." && pwd)
cd "$REPO_ROOT" || exit 2

SKIP_PRECOMMIT=0
while [[ $# -gt 0 ]]; do
  case "$1" in
    -SkipPreCommit | --skip-pre-commit) SKIP_PRECOMMIT=1 ;;
    -h | --help)
      echo "Usage: $0 [--skip-pre-commit]"
      exit 0
      ;;
    *)
      echo "pre-commit-and-tests.sh: unknown option: $1" >&2
      exit 2
      ;;
  esac
  shift
done

if [[ ! -f .venv/pyvenv.cfg ]]; then
  echo "No .venv/pyvenv.cfg - running uv sync to recreate the environment..." >&2
  uv sync
  if [[ ! -f .venv/pyvenv.cfg ]]; then
    echo "pre-commit-and-tests.sh: uv sync did not create .venv; fix disk path or UV_* env and retry." >&2
    exit 2
  fi
fi

if [[ "$SKIP_PRECOMMIT" -eq 0 ]]; then
  echo "Running pre-commit (Ruff + markdown + pt-BR locale guards)..." >&2
  if ! uv run pre-commit run --all-files; then
    echo "pre-commit failed. Attempting to auto-apply Ruff formatting and re-run pre-commit once..." >&2
    uv run ruff format . 2>/dev/null || true
    if ! uv run pre-commit run --all-files; then
      echo "pre-commit still failing after auto-format. Fix issues above before committing or pushing." >&2
      exit 1
    fi
  fi
fi

echo "Memory safety gate (Hypothesis + PyO3, tests/security/test_mem_integrity.py)..." >&2
set +e
uv run pytest tests/security/test_mem_integrity.py -v -W error --tb=short
rc=$?
set -e
if [[ "$rc" -ne 0 ]]; then
  echo "Memory safety pytest failed. Fix failures before committing or pushing." >&2
  exit "$rc"
fi

echo "Running pytest (full suite, warnings treated as errors)..." >&2
set +e
uv run pytest -v -W error --tb=short --deselect tests/security/test_mem_integrity.py
rc=$?
set -e
if [[ "$rc" -ne 0 ]]; then
  echo "pytest failed. Fix test failures before committing or pushing." >&2
fi
exit "$rc"
