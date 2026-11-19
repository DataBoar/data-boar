#!/usr/bin/env bash
# Isolated systemd --user + podman storage for prospect acceptance (never real ~/.config).
set -euo pipefail
H=$(mktemp -d /var/tmp/pqhXXXX)
R=$(mktemp -d /tmp/pqXXXX)
chmod 700 "$H" "$R"
mkdir -p "$H/.config/systemd/user" "$H/.local/share" "$H/.cache" "$H/.local/state" "$R/r"
chmod 700 "$R/r"
printf '[Unit]\nDescription=isolated idle\n' >"$H/.config/systemd/user/idle.target"
cat >"$R/envrc" <<E2
export HOME=$H XDG_CONFIG_HOME=$H/.config XDG_DATA_HOME=$H/.local/share XDG_CACHE_HOME=$H/.cache XDG_STATE_HOME=$H/.local/state XDG_RUNTIME_DIR=$R/r ISO_H=$H ISO_R=$R PROSPECT_ACCEPTANCE_ISOLATED=1
unset DBUS_SESSION_BUS_ADDRESS
E2
# Start an isolated user manager without the host session bus (Cursor/SSH often has none).
nohup env -i PATH=/usr/local/bin:/usr/bin:/bin HOME="$H" XDG_CONFIG_HOME="$H/.config" \
  XDG_DATA_HOME="$H/.local/share" XDG_CACHE_HOME="$H/.cache" XDG_STATE_HOME="$H/.local/state" \
  XDG_RUNTIME_DIR="$R/r" USER="${USER:-$(id -un)}" LOGNAME="${LOGNAME:-$(id -un)}" \
  /usr/lib/systemd/systemd --user --unit=idle.target >>"$R/mgr.log" 2>&1 &
echo $! >"$R/mgr.pid"
for _ in $(seq 60); do
  [ -S "$R/r/systemd/private" ] && break
  sleep 0.5
done
if [ ! -S "$R/r/systemd/private" ]; then
  echo "systemd --user não subiu (veja $R/mgr.log)" >&2
  exit 1
fi
# shellcheck disable=SC1090
(
  set -a
  # shellcheck source=/dev/null
  source "$R/envrc"
  set +a
  systemctl --user start dbus.socket
)
# Seed isolated Podman storage from the operator's real graph (acceptance HOME is empty).
host_home="${PROSPECT_ISO_HOST_HOME:-/home/leitao}"
host_graph="$host_home/.local/share/containers/storage"
demo_image="${PROSPECT_TEST_IMAGE:-localhost/data_boar:1.8.1-demo}"
caddy_image="${PROSPECT_ISO_CADDY_IMAGE:-docker.io/library/caddy:2}"
if [ -z "${PROSPECT_ISO_SKIP_IMAGE_LOAD:-}" ]; then
  podman --root "$host_graph" image exists "$demo_image" >/dev/null 2>&1 || {
    echo "imagem ausente no host: $demo_image (em $host_graph)" >&2
    exit 1
  }
  podman --root "$host_graph" save -m "$demo_image" "$caddy_image" \
    | (
      set -a
      # shellcheck source=/dev/null
      source "$R/envrc"
      set +a
      # stdout of this script is the isolation dir only (first line); loader chatter goes to stderr.
      podman load -q >&2
    )
fi
echo "$R"
echo "source $R/envrc   # then: export PROSPECT_TEST_IMAGE=... && pytest tests/acceptance/test_demo_prospect_acceptance.py"