#!/usr/bin/env bash
# scripts/labop-nfs-server-ensure.sh
# Validates and optionally ensures NFS server-side prerequisites on a target node.
# Run via narrow sudoers (LABOP_NFS_SERVER) from Maestro Handle-target_nfs.ps1.
#
# Usage: sudo -n /usr/bin/bash /path/to/labop-nfs-server-ensure.sh [--check | --apply] [--export-path PATH]
#   Subnet and persona hints: REPO_ROOT/.labop-gate/LAB_OP_SUBNET (and optional LAB_NFS_SVC,
#   LAB_PKG_MGR) written by Maestro Build-EnsureRemoteCommand before narrow-grant invoke.
#   (no args / --check)  probe only; exit 0 if healthy, 1 if fix needed
#   --apply              start services + configure export (additive only)
#   --export-path PATH   path to validate/export (default: $HOME/Documents/LGPD)
#
# Exit codes: 0=healthy, 1=needs fix (hard), 2=invocation error, 3=graceful ALARM (#1021 R9)
#
# Distro support: Debian/Ubuntu (nfs-kernel-server), Fedora/RHEL (nfs-server),
#                 openSUSE (nfsserver), Alpine (nfs), Void (nfs-utils)

set -u
export PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin${PATH+:$PATH}"

APPLY=0
CLEANUP=0
# Resolve operator home even when running as root via sudo
_OPERATOR="${SUDO_USER:-leitao}"
_OP_HOME="$(getent passwd "$_OPERATOR" | cut -d: -f6 2>/dev/null || echo "/home/$_OPERATOR")"
EXPORT_PATH="${_OP_HOME}/Documents/LGPD"
STATUS_FILE="${_OP_HOME}/.labop-status"
FW_TAG="nfs"
# Use the resolved operator home (not $HOME) so the ephemeral-firewall state file is
# found at teardown even under sudo ($HOME=/root) -- otherwise the ephemeral rule can
# leak into a persistent one (#935).
FW_STATE_FILE="${_OP_HOME}/.labop-fw-ephemeral-nfs.json"

for arg in "$@"; do
  case "$arg" in
    --apply)        APPLY=1 ;;
    --check)        APPLY=0 ;;
    --cleanup)      CLEANUP=1 ;;
    --export-path)  ;;
    --help|-h) echo "Usage: $0 [--check | --apply | --cleanup] [--export-path PATH]"; exit 0 ;;
    *)
      if [[ "${PREV_ARG:-}" == "--export-path" ]]; then
        EXPORT_PATH="$arg"
      else
        echo "[NFS-Ensure] Unknown arg: $arg" >&2; exit 2
      fi ;;
  esac
  PREV_ARG="$arg"
done

# Source firewall library
_SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
_REPO_ROOT="$(cd "$_SCRIPT_DIR/.." && pwd)"
_GATE_DIR="$_REPO_ROOT/.labop-gate"
if [[ -f "$_GATE_DIR/LAB_OP_SUBNET" ]]; then
  LAB_OP_SUBNET="$(tr -d '[:space:]' <"$_GATE_DIR/LAB_OP_SUBNET")"
  export LAB_OP_SUBNET
fi
if [[ -f "$_GATE_DIR/LAB_NFS_SVC" ]]; then
  LAB_NFS_SVC="$(tr -d '[:space:]' <"$_GATE_DIR/LAB_NFS_SVC")"
  export LAB_NFS_SVC
fi
if [[ -f "$_GATE_DIR/LAB_PKG_MGR" ]]; then
  LAB_PKG_MGR="$(tr -d '[:space:]' <"$_GATE_DIR/LAB_PKG_MGR")"
  export LAB_PKG_MGR
fi
# shellcheck source=labop-firewall-lib.sh
source "$_SCRIPT_DIR/labop-firewall-lib.sh" 2>/dev/null || {
  echo "[NFS-Ensure] WARN: labop-firewall-lib.sh not found - firewall checks skipped." >&2
}

_log() { echo "[NFS-Ensure $(date -u +%H:%M:%SZ)] $*"; }
_ok()  { echo "[NFS-Ensure] OK: $*"; }
_warn(){ echo "[NFS-Ensure] WARN: $*" >&2; }
_fail(){ echo "[NFS-Ensure] FAIL: $*" >&2; }

HOST=$(hostname -f 2>/dev/null || hostname)
_log "Starting on $HOST (apply=$APPLY cleanup=$CLEANUP export_path=$EXPORT_PATH subnet=$LAB_OP_SUBNET)"

# ---------------------------------------------------------------------------
# Cleanup mode: revert ephemeral firewall rules only
# ---------------------------------------------------------------------------
if [[ $CLEANUP -eq 1 ]]; then
  _log "Cleanup mode: reverting ephemeral firewall rules."
  type _fw_cleanup_ephemeral >/dev/null 2>&1 && _fw_cleanup_ephemeral
  exit 0
fi

NEED_FIX=0

# ---------------------------------------------------------------------------
# Detect init system (systemd vs runit/sv vs openrc vs sysv)
# ---------------------------------------------------------------------------
_svc_active() {
  local svc="$1"
  if command -v systemctl >/dev/null 2>&1; then
    systemctl is-active --quiet "$svc" 2>/dev/null
  elif command -v sv >/dev/null 2>&1; then
    sv status "$svc" 2>/dev/null | grep -q "^run:"
  elif command -v rc-service >/dev/null 2>&1; then
    rc-service "$svc" status >/dev/null 2>&1
  else
    return 1
  fi
}

_svc_start() {
  local svc="$1"
  if command -v systemctl >/dev/null 2>&1; then
    systemctl start "$svc" 2>&1
  elif command -v sv >/dev/null 2>&1; then
    # runit (Void): `sv start` fails with "unable to change to service directory"
    # when the service is defined in /etc/sv but not linked into the supervised
    # runsvdir. Link it first, wait for runsv to spawn, then start (#940).
    local _rsv="" _d _i
    for _d in /var/service /run/runit/service /etc/runit/runsvdir/current /service; do
      if [[ -d "$_d" ]]; then _rsv="$_d"; break; fi
    done
    if [[ -n "$_rsv" && -d "/etc/sv/$svc" && ! -e "$_rsv/$svc" ]]; then
      _log "runit: linking /etc/sv/$svc into $_rsv (service not yet supervised)."
      ln -s "/etc/sv/$svc" "$_rsv/$svc" 2>&1 || true
      for _i in 1 2 3 4 5; do
        [[ -e "$_rsv/$svc/supervise" ]] && break
        sleep 1
      done
    fi
    sv start "$svc" 2>&1
  elif command -v rc-service >/dev/null 2>&1; then
    rc-service "$svc" start 2>&1
  else
    echo "No supported init system found (systemd/runit/openrc)" >&2; return 1
  fi
}

_svc_list_units() {
  if command -v systemctl >/dev/null 2>&1; then
    systemctl list-unit-files "$1.service" >/dev/null 2>&1
  elif command -v sv >/dev/null 2>&1; then
    test -d "/etc/sv/$1" 2>/dev/null
  else
    return 1
  fi
}

# ---------------------------------------------------------------------------
# Detect NFS service name (distro-agnostic)
# ---------------------------------------------------------------------------
NFS_SVC=""
for candidate in nfs-kernel-server nfs-server nfsserver nfs rpc.nfsd; do
  if _svc_list_units "$candidate" 2>/dev/null; then
    NFS_SVC="$candidate"; break
  fi
done

if [[ -z "$NFS_SVC" ]]; then
  # Void Linux: nfs-utils package provides runit services under different names
  for candidate in nfs-server nfsd; do
    if command -v sv >/dev/null 2>&1 && test -d "/etc/sv/$candidate" 2>/dev/null; then
      NFS_SVC="$candidate"; break
    fi
  done
fi

if [[ -z "$NFS_SVC" ]]; then
  _fail "No NFS server service found (tried: nfs-kernel-server nfs-server nfsserver nfs)."
  echo "NFS_SERVER_UNAVAILABLE at $(date +'%H:%M:%S')" > "$STATUS_FILE" 2>/dev/null || true
  echo "[NFS-Ensure] ALARM=nfs_server_unavailable hint=t14_primary_nfs_coverage" >&2
  exit 3
fi
_log "NFS service: $NFS_SVC"

# ---------------------------------------------------------------------------
# Phase 2: Check rpcbind (skip on runit/Void where rpcbind may be unnecessary)
# ---------------------------------------------------------------------------
if command -v systemctl >/dev/null 2>&1; then
  if ! _svc_active rpcbind; then
    _warn "rpcbind not running."
    NEED_FIX=1
    if [[ $APPLY -eq 1 ]]; then
      _log "Starting rpcbind..."
      _svc_start rpcbind && _ok "rpcbind started." || _fail "rpcbind start failed."
    fi
  else
    _ok "rpcbind: active."
  fi
else
  _log "rpcbind check skipped (no systemctl - runit/OpenRC manages portmapper differently)."
fi

# ---------------------------------------------------------------------------
# Phase 3: Check NFS server
# ---------------------------------------------------------------------------
if ! _svc_active "$NFS_SVC" 2>/dev/null; then
  _warn "$NFS_SVC not running."
  NEED_FIX=1
  if [[ $APPLY -eq 1 ]]; then
    _log "Starting $NFS_SVC..."
    _svc_start "$NFS_SVC" && _ok "$NFS_SVC started." || _fail "$NFS_SVC start failed."
  fi
else
  _ok "$NFS_SVC: active."
fi
NFS_PORT=2049
if type _port_listening >/dev/null 2>&1; then
  if _port_listening $NFS_PORT; then
    _ok "Port $NFS_PORT/tcp listening."
  else
    _warn "Port $NFS_PORT/tcp NOT listening - NFS service may not be fully started."
    NEED_FIX=1
  fi
fi

# Phase 3b: Firewall check for NFS port
if type _fw_detect >/dev/null 2>&1; then
  _fw_detect
  if _fw_port_allowed $NFS_PORT tcp; then
    _ok "Firewall allows $LAB_OP_SUBNET -> port $NFS_PORT/tcp."
  else
    _warn "Firewall BLOCKS $LAB_OP_SUBNET -> port $NFS_PORT/tcp."
    NEED_FIX=1
    if [[ $APPLY -eq 1 ]]; then
      _log "Opening port $NFS_PORT/tcp ephemerally for $LAB_OP_SUBNET..."
      _fw_open_ephemeral $NFS_PORT tcp || _warn "Ephemeral rule failed (check sudoers LABOP_NFS_SERVER)."
    else
      type _fw_troubleshoot_hint >/dev/null 2>&1 && _fw_troubleshoot_hint $NFS_PORT tcp "NFS"
    fi
  fi
fi
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
      exportfs -ra 2>&1 && _ok "exportfs -ra OK." || {
        _fail "exportfs -ra failed."
        echo "[NFS-Ensure] ALARM=nfs_export_unavailable hint=t14_primary_nfs_coverage" >&2
        exit 3
      }
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
