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
systemd-run --user --scope -p Delegate=yes --unit="pq-iso-$(basename "$R")" -q -- \
  env -i PATH=/usr/local/bin:/usr/bin:/bin HOME="$H" XDG_CONFIG_HOME="$H/.config" \
  XDG_DATA_HOME="$H/.local/share" XDG_CACHE_HOME="$H/.cache" XDG_STATE_HOME="$H/.local/state" \
  XDG_RUNTIME_DIR="$R/r" USER="${USER:-$(id -un)}" LOGNAME="${LOGNAME:-$(id -un)}" \
  /usr/lib/systemd/systemd --user --unit=idle.target >"$R/mgr.log" 2>&1 &
echo $! >"$R/mgr.pid"
for _ in $(seq 30); do
  [ -S "$R/r/systemd/private" ] && break
  sleep 0.5
done
# shellcheck disable=SC1090
( source "$R/envrc"; systemctl --user start dbus.socket )
echo "$R"
echo "source $R/envrc   # then: export PROSPECT_TEST_IMAGE=... && pytest tests/acceptance/test_demo_prospect_acceptance.py"