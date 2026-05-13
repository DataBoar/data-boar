#!/usr/bin/env bash
# scripts/labop-smb-server-ensure.sh
# Validates and optionally ensures SMB/Samba server-side prerequisites on a target node.
# Run via narrow sudoers (LABOP_SMB_SERVER) from Maestro Handle-target_cifs.ps1.
#
# Usage: sudo -n bash /path/to/labop-smb-server-ensure.sh [--check | --apply] [--share-path PATH] [--share-name NAME]
#   (no args / --check)  probe only; exit 0 if healthy, 1 if fix needed
#   --apply              start services (additive; does NOT write smb.conf automatically)
#   --share-path PATH    path to validate (default: $HOME/Documents/LGPD)
#   --share-name NAME    Samba share name to look for (default: lgpd_data)
#
# NOTE: smb.conf is NOT auto-written -- operator must configure shares manually.
#       This script only ensures services are running and validates existing config.
#
# Exit codes: 0=healthy, 1=needs fix, 2=invocation error

set -u
export PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin${PATH+:$PATH}"

APPLY=0
SHARE_PATH="${HOME}/Documents/LGPD"
SHARE_NAME="lgpd_data"
STATUS_FILE="${HOME}/.labop-status"

PREV_ARG=""
for arg in "$@"; do
  case "$arg" in
    --apply)       APPLY=1 ;;
    --check)       APPLY=0 ;;
    --share-path)  ;;
    --share-name)  ;;
    --help|-h) echo "Usage: $0 [--check | --apply] [--share-path PATH] [--share-name NAME]"; exit 0 ;;
    *)
      if [[ "$PREV_ARG" == "--share-path" ]]; then
        SHARE_PATH="$arg"
      elif [[ "$PREV_ARG" == "--share-name" ]]; then
        SHARE_NAME="$arg"
      else
        echo "[SMB-Ensure] Unknown arg: $arg" >&2; exit 2
      fi ;;
  esac
  PREV_ARG="$arg"
done

_log() { echo "[SMB-Ensure $(date -u +%H:%M:%SZ)] $*"; }
_ok()  { echo "[SMB-Ensure] OK: $*"; }
_warn(){ echo "[SMB-Ensure] WARN: $*" >&2; }
_fail(){ echo "[SMB-Ensure] FAIL: $*" >&2; }

HOST=$(hostname -f 2>/dev/null || hostname)
_log "Starting on $HOST (apply=$APPLY share_path=$SHARE_PATH share_name=$SHARE_NAME)"

NEED_FIX=0

# ---------------------------------------------------------------------------
# Phase 1: Check smbd
# ---------------------------------------------------------------------------
if ! systemctl is-active --quiet smbd 2>/dev/null; then
  _warn "smbd not running."
  NEED_FIX=1
  if [[ $APPLY -eq 1 ]]; then
    _log "Starting smbd..."
    systemctl start smbd 2>&1 && _ok "smbd started." || _fail "smbd start failed."
  fi
else
  _ok "smbd: active."
fi

# ---------------------------------------------------------------------------
# Phase 2: Check nmbd (optional but typical for NetBIOS browsing)
# ---------------------------------------------------------------------------
if systemctl list-unit-files nmbd.service >/dev/null 2>&1; then
  if ! systemctl is-active --quiet nmbd 2>/dev/null; then
    _warn "nmbd not running (optional; continuing)."
    if [[ $APPLY -eq 1 ]]; then
      systemctl start nmbd 2>&1 && _ok "nmbd started." || _warn "nmbd start failed (non-fatal)."
    fi
  else
    _ok "nmbd: active."
  fi
fi

# ---------------------------------------------------------------------------
# Phase 3: Check share path exists
# ---------------------------------------------------------------------------
if [[ ! -d "$SHARE_PATH" ]]; then
  _warn "Share path does not exist: $SHARE_PATH"
  NEED_FIX=1
  if [[ $APPLY -eq 1 ]]; then
    mkdir -p "$SHARE_PATH" && _ok "Created: $SHARE_PATH" || _fail "mkdir failed: $SHARE_PATH"
  fi
else
  _ok "Share path exists: $SHARE_PATH"
fi

# ---------------------------------------------------------------------------
# Phase 4: Check smb.conf for share definition
# ---------------------------------------------------------------------------
SMB_CONF="/etc/samba/smb.conf"
if [[ -f "$SMB_CONF" ]]; then
  if grep -q "^\[$SHARE_NAME\]" "$SMB_CONF" 2>/dev/null; then
    _ok "Share [$SHARE_NAME] found in $SMB_CONF."
  else
    _warn "Share [$SHARE_NAME] NOT found in $SMB_CONF."
    NEED_FIX=1
    if [[ $APPLY -eq 1 ]]; then
      _warn "Auto-writing smb.conf is intentionally NOT supported (risk of overwriting production config)."
      _warn "Add manually to $SMB_CONF:"
      _warn "  [$SHARE_NAME]"
      _warn "    path = $SHARE_PATH"
      _warn "    read only = yes"
      _warn "    guest ok = yes"
    fi
  fi

  # Phase 5: Quick smbclient self-test (if available and share exists)
  if command -v smbclient >/dev/null 2>&1 && \
     grep -q "^\[$SHARE_NAME\]" "$SMB_CONF" 2>/dev/null; then
    if smbclient "//localhost/$SHARE_NAME" -N -c "ls" >/dev/null 2>&1; then
      _ok "smbclient self-test OK: //localhost/$SHARE_NAME accessible."
    else
      _warn "smbclient self-test failed: //localhost/$SHARE_NAME not accessible."
      NEED_FIX=1
    fi
  fi
else
  _warn "$SMB_CONF not found. Samba may not be installed or configured."
  NEED_FIX=1
fi

# ---------------------------------------------------------------------------
# Phase 6: Write status and exit
# ---------------------------------------------------------------------------
if [[ $NEED_FIX -eq 0 ]]; then
  _ok "SMB/Samba server fully healthy on $HOST."
  echo "SMB_SERVER_READY share=$SHARE_NAME path=$SHARE_PATH at $(date +'%H:%M:%S')" > "$STATUS_FILE" 2>/dev/null || true
  exit 0
else
  if [[ $APPLY -eq 1 ]]; then
    if systemctl is-active --quiet smbd 2>/dev/null; then
      _ok "smbd running after remediation. Share config may still need manual setup."
      echo "SMB_SERVER_DEGRADED share=$SHARE_NAME at $(date +'%H:%M:%S')" > "$STATUS_FILE" 2>/dev/null || true
    fi
  fi
  _fail "SMB server not fully ready on $HOST. Run with --apply to start services."
  echo "SMB_SERVER_DEGRADED share=$SHARE_NAME at $(date +'%H:%M:%S')" > "$STATUS_FILE" 2>/dev/null || true
  exit 1
fi
