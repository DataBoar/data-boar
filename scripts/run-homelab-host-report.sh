#!/usr/bin/env bash
set -euo pipefail

# Convenience wrapper: run the repo's host report script from repo root,
# ensuring it can be executed even after a fresh clone.

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
REPO_ROOT="$(cd -- "${SCRIPT_DIR}/.." && pwd -P)"

cd -- "$REPO_ROOT"

chmod +x scripts/homelab-host-report.sh
exec bash scripts/homelab-host-report.sh

