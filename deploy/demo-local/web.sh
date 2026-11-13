#!/usr/bin/env bash
# Optional WebDAV + REST toy target (#1447): ONE httpd:2.4 container with mod_dav
# (WebDAV needs PROPFIND) serving /dav and static JSON on /api. Read-only,
# loopback publish, no secrets. Linux host-only (rootless Podman). No PowerShell
# twin by design (docs/ops/SCRIPTS_CROSS_PLATFORM_PAIRING.md, rule 3).
# Usage: web.sh start|stop
set -euo pipefail
. "$(dirname "${BASH_SOURCE[0]}")/lib.sh"

case "${1:-}" in
  start)
    mkdir -p "$STATE/web"
    (cd "$REPO_ROOT" && uv run --no-sync python -I "$DL_DIR/seed_web.py" "$STATE/web")
    chmod -R o+rX "$STATE/web"
    podman run -d --name "$C_WEB" --userns "keep-id:uid=$(id -u),gid=$(id -g)" \
      --user "$(id -u):$(id -g)" --memory 48m "${HARDEN[@]}" --tmpfs /tmp \
      -p "127.0.0.1:$PORT_WEB:8077" \
      -v "$DL_DIR/httpd.conf:/usr/local/apache2/conf/httpd.conf:ro" \
      -v "$STATE/web:/srv/web:ro" "$IMG_HTTPD" >/dev/null
    wait_http "http://127.0.0.1:$PORT_WEB/api/people" 30 || die "httpd not answering"
    ;;
  stop) podman rm -f -t 5 "$C_WEB" >/dev/null 2>&1 || true ;;
  *) die "usage: web.sh start|stop" ;;
esac
