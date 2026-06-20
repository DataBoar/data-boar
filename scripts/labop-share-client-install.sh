#!/usr/bin/env bash
# Data Boar - install OS packages for CIFS/NFS/sshfs kernel mounts used in lab workflows.
# See docs/ops/LAB_SMOKE_MULTI_HOST.md and ops/automation/ansible/playbooks/lab-data-boar-share-clients.yml.
#
# Usage on the Linux host (from repo root):
#   sudo bash scripts/labop-share-client-install.sh
#
# For non-interactive SSH from the dev workstation, add NOPASSWD for this script path
# (same pattern as homelab-host-report.sh). Template: docs/private/homelab/LABOP_SHARE_CLIENTS_SUDOERS.pt_BR.md

set -eu
export PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin${PATH+:$PATH}"

if command -v apt-get >/dev/null 2>&1; then
  export DEBIAN_FRONTEND=noninteractive
  exec apt-get install -y cifs-utils nfs-common sshfs fuse3
fi

if command -v xbps-install >/dev/null 2>&1; then
  # Void: sshfs is provided by fuse-sshfs (there is no top-level "sshfs" package name).
  exec xbps-install -Sy cifs-utils nfs-utils fuse-sshfs fuse
fi

echo "labop-share-client-install: no apt-get or xbps-install found" >&2
exit 1
