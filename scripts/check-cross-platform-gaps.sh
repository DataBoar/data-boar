#!/usr/bin/env bash
# check-cross-platform-gaps.sh — mirror of scripts/check-cross-platform-gaps.ps1
set -euo pipefail
REPO_ROOT=$(cd "$(dirname "$0")/.." && pwd)
PY=python3
command -v python3 >/dev/null 2>&1 || PY=python
ARGS=("$REPO_ROOT/scripts/check_cross_platform_gaps.py")
if [[ "${1:-}" == "--missing-only" ]] || [[ "${1:-}" == "-MissingOnly" ]]; then
  ARGS+=(--missing-only)
fi
"$PY" "${ARGS[@]}"
