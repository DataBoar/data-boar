#!/usr/bin/env bash
# check-hubs.sh — mirror of scripts/check-hubs.ps1
set -euo pipefail
REPO_ROOT=$(cd "$(dirname "$0")/.." && pwd)
PY=python3
command -v python3 >/dev/null 2>&1 || PY=python
"$PY" "$REPO_ROOT/scripts/check_hubs.py"
