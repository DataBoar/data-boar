#!/usr/bin/env bash
# Build the /extras overlay for the Data Boar container image (#1447).
# Linux host-only (needs the host's free-threaded CPython 3.14 via uv, and gcc
# for sdists such as brotli). No PowerShell twin by design
# (docs/ops/SCRIPTS_CROSS_PLATFORM_PAIRING.md, rule 3).
#
# The image (PYTHONPATH=/extras:/app, CPython 3.14 free-threaded, no pip) lacks
# pymongo, redis, smbprotocol, webdavclient3 and py7zr. This installs the pins in
# extras.txt for cp314t into $EXTRAS_DIR, then:
#   * drops every package the image already ships (the overlay comes FIRST on
#     PYTHONPATH and would shadow it, e.g. cryptography, lxml, requests);
#   * fails if any native module is not cp314t or is abi3.
# Usage: build-extras.sh [--ensure|--force]   (default: --ensure)
set -euo pipefail
. "$(dirname "${BASH_SOURCE[0]}")/lib.sh"

EXTRAS_DIR="${DEMO_LOCAL_EXTRAS_DIR:-$HOME/.cache/databoar-demo-local/extras}"
stamp="$(cat "$DL_DIR/extras.txt" "$DL_DIR/build-extras.sh" | sha256sum | cut -c1-16)-$IMG_BOAR"
mode="${1:---ensure}"
if [ "$mode" = --ensure ] && [ -f "$EXTRAS_DIR/.stamp" ] && [ "$(cat "$EXTRAS_DIR/.stamp")" = "$stamp" ]; then
  exit 0
fi

py="$(uv python find 3.14t)" || die "no free-threaded Python 3.14 (uv python install 3.14t)"
work="$(mktemp -d "${TMPDIR:-$HOME/.cache}/extras-build.XXXXXX")"
trap 'rm -rf -- "${work:?}"' EXIT

uv pip install -q --python "$py" --target "$work/pkg" -r "$DL_DIR/extras.txt"

# Packages the image already has (top-level modules and distributions).
podman run --rm --entrypoint python "$IMG_BOAR" -c '
import importlib.metadata as m, pkgutil, re
mods = {x.name for x in pkgutil.iter_modules()}
dists = {re.sub(r"[-_.]+", "_", d.metadata["Name"]).lower() for d in m.distributions()}
print("\n".join(sorted(mods | {"dist:" + d for d in dists})))' 2>/dev/null \
  | grep -v Warning >"$work/image.txt"
[ -s "$work/image.txt" ] || die "could not list the image's packages"

keep_mod='^(py7zr|pymongo|bson|gridfs|redis|smbprotocol|smbclient|webdav3|requests_ntlm|spnego)$'
keep_dist='^(py7zr|pymongo|redis|smbprotocol|webdavclient3|requests_ntlm|pyspnego)$'
for entry in "$work"/pkg/*; do
  name="$(basename "$entry")"
  case "$name" in
    *.dist-info)
      d="$(echo "${name%%-*}" | sed 's/[-_.]\+/_/g' | tr 'A-Z' 'a-z')"
      if grep -qx "dist:$d" "$work/image.txt" && ! echo "$d" | grep -Eq "$keep_dist"; then
        rm -rf -- "$entry"
      fi ;;
    __pycache__ | bin) rm -rf -- "$entry" ;;
    *)
      mod="${name%%.*}"
      if grep -qx "$mod" "$work/image.txt" && ! echo "$mod" | grep -Eq "$keep_mod"; then
        rm -rf -- "$entry"
      fi ;;
  esac
done

# ABI check: only cp314t native modules; abi3 would not load.
bad="$(find "$work/pkg" -name '*.so*' ! -name '*cpython-314t*' || true)"
[ -z "$bad" ] || die "non-cp314t native modules: $bad"
if find "$work/pkg" -name '*abi3*' | grep -q .; then die "abi3 module found in overlay"; fi

rm -rf -- "${EXTRAS_DIR:?}"
mkdir -p "$(dirname "$EXTRAS_DIR")"
mv "$work/pkg" "$EXTRAS_DIR"
chmod -R a+rX "$EXTRAS_DIR"
echo "$stamp" >"$EXTRAS_DIR/.stamp"
echo "extras overlay ready: $EXTRAS_DIR"
