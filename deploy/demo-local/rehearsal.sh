#!/usr/bin/env bash
# Full rehearsal of the LOCAL demo scenario (#1447): scan each target in turn,
# measure RAM peak / time / findings, print a markdown table with a cut rule.
# Linux host-only (rootless Podman). No PowerShell twin by design
# (docs/ops/SCRIPTS_CROSS_PLATFORM_PAIRING.md, rule 3).
#
# Usage: rehearsal.sh [--mode container|native] [--fresh] [--out FILE]
#   --fresh  run down.sh + up.sh first and include the startup time.
# Needs the scenario up (up.sh). The table goes to stdout and to --out
# (default: $STATE/rehearsal-table.md, outside the repo).
set -euo pipefail
. "$(dirname "${BASH_SOURCE[0]}")/lib.sh"

MODE=$(boar_mode)
MODE=${MODE:-container}
FRESH=0
OUT=""
while [ $# -gt 0 ]; do
  case "$1" in
    --mode) MODE="${2:?}"; shift 2 ;;
    --fresh) FRESH=1; shift ;;
    --out) OUT="${2:?}"; shift 2 ;;
    *) die "usage: rehearsal.sh [--mode container|native] [--fresh] [--out FILE]" ;;
  esac
done

UP_SECONDS=""
if [ "$FRESH" = 1 ]; then
  "$DL_DIR/down.sh" >/dev/null
  t0=$(date +%s.%N)
  "$DL_DIR/up.sh" --mode "$MODE" >/dev/null
  UP_SECONDS=$(printf '%.1f' "$(echo "$(date +%s.%N) - $t0" | bc)")
fi
[ -f "$SECRETS" ] || die "scenario is not up; run up.sh (or use --fresh)"
OUT="${OUT:-$STATE/rehearsal-table.md}"

cd "$REPO_ROOT"
uv run --no-sync python -I "$DL_DIR/rehearsal.py" --mode "$MODE" --state "$STATE" \
  --boar-url "$BOAR_URL" --out "$OUT" --up-seconds "${UP_SECONDS:-}"
