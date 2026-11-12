#!/usr/bin/env bash
# Restore the demo data directory to the baseline snapshot (#1447).
#
# Linux host-only: runs on the demo host under rootless Podman, as the
# ExecStartPre of dashboard.service. No PowerShell twin by design
# (docs/ops/SCRIPTS_CROSS_PLATFORM_PAIRING.md, rule 3).
#
# Usage: demo-restore-baseline.sh <data-dir> <baseline-dir>
#   <data-dir>      must end in /demo/data (guard against a wrong path)
#   <baseline-dir>  clean snapshot; must contain config.yaml
#
# Files in <data-dir> belong to the container's mapped user (:U volume), so the
# delete and copy run inside `podman unshare`. Idempotent: if it stops halfway,
# the next start (or the next reset) restores the baseline again.
set -euo pipefail

data="${1:?usage: demo-restore-baseline.sh <data-dir> <baseline-dir>}"
base="${2:?usage: demo-restore-baseline.sh <data-dir> <baseline-dir>}"

case "$data" in
*/demo/data) ;;
*)
	echo "demo-restore-baseline: refusing unexpected data dir: $data" >&2
	exit 2
	;;
esac
if [ ! -f "$base/config.yaml" ]; then
	echo "demo-restore-baseline: baseline has no config.yaml: $base" >&2
	exit 3
fi
if [ ! -d "$data" ]; then
	echo "demo-restore-baseline: data dir does not exist: $data" >&2
	exit 4
fi

trap 'echo "demo-restore-baseline: failed; $data may be partial, rerun to restore" >&2' ERR

# shellcheck disable=SC2016  # $1/$2 expand inside the unshare shell
podman unshare sh -c 'find "$1" -mindepth 1 -delete && cp -a "$2/." "$1/"' sh "$data" "$base"
echo "demo-restore-baseline: $data restored from $base"
