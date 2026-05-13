#!/usr/bin/env bash
# scripts/labop-nfs-server-ensure.sh
# Validates and optionally ensures NFS server-side prerequisites on a target node.
# Run via narrow sudoers (LABOP_NFS_SERVER) from Maestro Handle-target_nfs.ps1.
#
# Usage: sudo -n bash /path/to/labop-nfs-server-ensure.sh [--check | --apply] [--export-path PATH]
#   (no args / --check)  probe only; exit 0 if healthy, 1 if fix needed
#   --apply              start services + configure export (additive only)
#   --export-path PATH   path to validate/export (default: $HOME/Documents/LGPD)
#
# Exit codes: 0=healthy, 1=needs fix, 2=invocation error
#
# Distro support: Debian/Ubuntu (nfs-kernel-server), Fedora/RHEL (nfs-server),
#                 openSUSE (nfsserver), Alpine (nfs), Void (nfs-utils)

set -u
export PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin${PATH+:$PATH}"

APPLY=0
EXPORT_PATH="${HOME}/Documents/LGPD"
STATUS_FILE="${HOME}/.labop-status"

for arg in "$@"; do
  case "$arg" in
    --apply)        APPLY=1 ;;
    --check)        APPLY=0 ;;
    --export-path)  ;;  # handled below via shift-next
    --help|-h) echo "Usage: $0 [--check | --apply] [--export-path PATH]"; exit 0 ;;
    *)
      if [[ "${PREV_ARG:-}" == "--export-path" ]]; then
        EXPORT_PATH="$arg"
      else
        echo "[NFS-Ensure] Unknown arg: $arg" >&2; exit 2
      fi ;;
  esac
  PREV_ARG="$arg"
done

_log() { echo "[NFS-Ensure $(date -u +%H:%M:%SZ)] $*"; }
_ok()  { echo "[NFS-Ensure] OK: $*"; }
_warn(){ echo "[NFS-Ensure] WARN: $*" >&2; }
_fail(){ echo "[NFS-Ensure] FAIL: $*" >&2; }

HOST=$(hostname -f 2>/dev/null || hostname)
_log "Starting on $HOST (apply=$APPLY export_path=$EXPORT_PATH)"

NEED_FIX=0

# ---------------------------------------------------------------------------
# Phase 1: Detect NFS service name (distro-agnostic)
# ---------------------------------------------------------------------------
NFS_SVC=""
for candidate in nfs-kernel-server nfs-server nfsserver nfs; do
  if systemctl list-unit-files "$candidate.service" >/dev/null 2>&1; then
    NFS_SVC="$candidate"
    break
  fi
done

if [[ -z "$NFS_SVC" ]]; then
  _fail "No NFS server service found (tried: nfs-kernel-server nfs-server nfsserver nfs)."
  echo "NFS_SERVER_UNAVAILABLE at $(date +'%H:%M:%S')" > "$STATUS_FILE" 2>/dev/null || true
  exit 1
fi
_log "NFS service: $NFS_SVC"

# ---------------------------------------------------------------------------
# Phase 2: Check rpcbind
# ---------------------------------------------------------------------------
if ! systemctl is-active --quiet rpcbind 2>/dev/null; then
  _warn "rpcbind not running."
  NEED_FIX=1
  if [[ $APPLY -eq 1 ]]; then
    _log "Starting rpcbind..."
    systemctl start rpcbind 2>&1 && _ok "rpcbind started." || _fail "rpcbind start failed."
  fi
else
  _ok "rpcbind: active."
fi

# ---------------------------------------------------------------------------
# Phase 3: Check NFS server
# ---------------------------------------------------------------------------
if ! systemctl is-active --quiet "$NFS_SVC" 2>/dev/null; then
  _warn "$NFS_SVC not running."
  NEED_FIX=1
  if [[ $APPLY -eq 1 ]]; then
    _log "Starting $NFS_SVC..."
    systemctl start "$NFS_SVC" 2>&1 && _ok "$NFS_SVC started." || _fail "$NFS_SVC start failed."
  fi
else
  _ok "$NFS_SVC: active."
fi

# ---------------------------------------------------------------------------
# Phase 4: Check export path
# ---------------------------------------------------------------------------
if [[ ! -d "$EXPORT_PATH" ]]; then
  _warn "Export path does not exist: $EXPORT_PATH"
  NEED_FIX=1
  if [[ $APPLY -eq 1 ]]; then
    mkdir -p "$EXPORT_PATH" && _ok "Created: $EXPORT_PATH" || _fail "mkdir failed: $EXPORT_PATH"
  fi
else
  _ok "Export path exists: $EXPORT_PATH"
fi

# Phase 5: Check if path is exported
if command -v exportfs >/dev/null 2>&1; then
  if exportfs -v 2>/dev/null | grep -qF "$EXPORT_PATH"; then
    _ok "Path is exported: $(exportfs -v 2>/dev/null | grep -F "$EXPORT_PATH" | head -1)"
  else
    _warn "Path not exported: $EXPORT_PATH"
    NEED_FIX=1
    if [[ $APPLY -eq 1 ]]; then
      _log "Adding export: $EXPORT_PATH *(ro,sync,no_subtree_check)"
      echo "$EXPORT_PATH *(ro,sync,no_subtree_check)" >> /etc/exports
      exportfs -ra 2>&1 && _ok "exportfs -ra OK." || _fail "exportfs -ra failed."
    fi
  fi
fi

# ---------------------------------------------------------------------------
# Phase 6: Write status and exit
# ---------------------------------------------------------------------------
if [[ $NEED_FIX -eq 0 ]]; then
  _ok "NFS server fully healthy on $HOST."
  echo "NFS_SERVER_READY path=$EXPORT_PATH at $(date +'%H:%M:%S')" > "$STATUS_FILE" 2>/dev/null || true
  exit 0
else
  if [[ $APPLY -eq 1 ]]; then
    # Re-probe after apply
    if systemctl is-active --quiet "$NFS_SVC" 2>/dev/null && \
       systemctl is-active --quiet rpcbind 2>/dev/null; then
      _ok "NFS server healthy after remediation."
      echo "NFS_SERVER_READY path=$EXPORT_PATH at $(date +'%H:%M:%S')" > "$STATUS_FILE" 2>/dev/null || true
      exit 0
    fi
  fi
  _fail "NFS server not fully ready on $HOST. Run with --apply to attempt remediation."
  echo "NFS_SERVER_DEGRADED path=$EXPORT_PATH at $(date +'%H:%M:%S')" > "$STATUS_FILE" 2>/dev/null || true
  exit 1
fi
