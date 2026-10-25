#!/usr/bin/env bash
# OSV dependency scan — pinned binary bootstrap (issue #1933).
set -Eeuo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

# shellcheck source=scripts/db-tool-bootstrap.sh
source "$REPO_ROOT/scripts/db-tool-bootstrap.sh"

db_ensure_osv_scanner || {
  echo "run-osv-scanner: osv-scanner unavailable (bootstrap failed)" >&2
  exit 1
}

osv-scanner scan source -r "$REPO_ROOT" --config="$REPO_ROOT/security/osv-scanner.toml"
