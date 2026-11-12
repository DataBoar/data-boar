#!/usr/bin/env bash
# Restart Data Boar with a (possibly filtered) config, for the rehearsal (#1447).
# Linux host-only (rootless Podman). No PowerShell twin by design
# (docs/ops/SCRIPTS_CROSS_PLATFORM_PAIRING.md, rule 3).
#
# Usage: boar.sh restart <container|native> [target-name[,..]] [smb-variant]
#        boar.sh stop
# The PID used in native mode is the one this harness started (boar.pid).
set -euo pipefail
. "$(dirname "${BASH_SOURCE[0]}")/lib.sh"

case "${1:-}" in
  restart)
    mode="${2:?mode}"
    only="${3:-}"
    variant="${4:-}"
    boar_stop
    render_config "$mode" "$STATE/data/config.yaml" "$only" "$variant"
    boar_start "$mode"
    ;;
  stop) boar_stop ;;
  *) die "usage: boar.sh restart <container|native> [targets] [variant] | stop" ;;
esac
