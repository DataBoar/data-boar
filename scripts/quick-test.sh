#!/usr/bin/env bash
# quick-test.sh — Linux/macOS mirror of scripts/quick-test.ps1.
# Run a pytest subset (by path or -k keyword) to save time vs full check-all.
# Usage (from repo root):
#   ./scripts/quick-test.sh
#   ./scripts/quick-test.sh --path tests/test_foo.py
#   ./scripts/quick-test.sh --path tests/test_foo.py --keyword test_bar
#   ./scripts/quick-test.sh -k "content_type"
# Windows: prefer .\scripts\quick-test.ps1
set -euo pipefail

REPO_ROOT=$(cd "$(dirname "$0")/.." && pwd)
cd "$REPO_ROOT" || exit 2

PATH_ARG=""
KEYWORD=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    -Path | --path)
      if [[ $# -lt 2 ]]; then
        echo "quick-test.sh: missing value for $1" >&2
        exit 2
      fi
      PATH_ARG="$2"
      shift 2
      ;;
    -Keyword | --keyword | -k)
      if [[ $# -lt 2 ]]; then
        echo "quick-test.sh: missing value for $1" >&2
        exit 2
      fi
      KEYWORD="$2"
      shift 2
      ;;
    -h | --help)
      echo "Usage: $0 [--path PATH] [--keyword|-k PATTERN]"
      echo "  (same intent as quick-test.ps1 -Path / -Keyword)"
      exit 0
      ;;
    *)
      echo "quick-test.sh: unknown option: $1" >&2
      exit 2
      ;;
  esac
done

args=(-v -W error --tb=short)
if [[ -n "$PATH_ARG" ]]; then
  args+=("$PATH_ARG")
fi
if [[ -n "$KEYWORD" ]]; then
  args+=(-k "$KEYWORD")
fi

echo "=== quick-test: pytest (subset) ===" >&2
if [[ -n "$PATH_ARG" ]]; then
  echo "  Path: $PATH_ARG" >&2
fi
if [[ -n "$KEYWORD" ]]; then
  echo "  Keyword: $KEYWORD" >&2
fi

set +e
uv run pytest "${args[@]}"
rc=$?
set -e
if [[ "$rc" -eq 0 ]]; then
  echo "quick-test: OK." >&2
else
  echo "quick-test: FAILED." >&2
fi
exit "$rc"
