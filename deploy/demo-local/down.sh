#!/usr/bin/env bash
# Remove the local demo scenario (#1447): containers, Boar, corpus and every
# ephemeral secret. Idempotent. Linux host-only (rootless Podman). No
# PowerShell twin by design (docs/ops/SCRIPTS_CROSS_PLATFORM_PAIRING.md, rule 3).
set -uo pipefail
. "$(dirname "${BASH_SOURCE[0]}")/lib.sh"

boar_stop
for c in "$C_BOAR" "$C_WEB" "$C_MONGO" "$C_REDIS" "$C_PG" "$C_SMB"; do
  podman rm -f -t 5 "$c" >/dev/null 2>&1 || true
done
# Only the children this harness creates are removed, never the STATE root.
{ [ -n "$STATE" ] && [ "$STATE" != "/" ] && [ "$STATE" != "$HOME" ]; } || die "bad STATE"
for f in secrets.env boar.mode boar.pid data corpus samba logs web; do
  podman unshare rm -rf -- "${STATE:?}/$f" 2>/dev/null || true
  rm -rf -- "${STATE:?}/$f" 2>/dev/null || true
done
rmdir "$STATE" 2>/dev/null || true
echo "down: containers and ephemeral state removed"
