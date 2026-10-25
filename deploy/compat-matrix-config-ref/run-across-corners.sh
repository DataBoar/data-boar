#!/bin/bash
# run-across-corners.sh — LAYER 1 of the comparable config (#1368) on every corner.
#
# DESIGN DECISION: extract the corpus ONCE on the host and mount it read-only into
# each corner. Comparability requires the SAME BYTES everywhere — per-corner
# extraction would open the door to silent divergence, which is exactly the
# failure mode this config exists to catch.
#
# Comparable output per corner: findings + scan_failures BY REASON.
#
# Env:
#   DATABOAR_REPO       — repo root (default: two levels above this script)
#   WHEELHOUSE_DIR      — wheelhouse-x86-64-v1 root (required for musl corners)
#   CONFIG_MATRIX_WORK  — work/results dir (default: ${TMPDIR:-/tmp}/data-boar-config-matrix)
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"
REPO="${DATABOAR_REPO:-$(cd "$HERE/../.." && pwd)}"
BASE="${CONFIG_MATRIX_WORK:-${TMPDIR:-/tmp}/data-boar-config-matrix}"
CORPUS="$BASE/corpus"
RES="$BASE/res"; rm -rf "$RES"; mkdir -p "$RES"
WH="${WHEELHOUSE_DIR:-}"

echo "########## corpus (once, from origin/main) ##########"
if [ ! -d "$CORPUS/compressed" ]; then
  mkdir -p "$CORPUS"
  git -C "$REPO" archive origin/main tests/data | tar -x -C "$CORPUS" --strip-components=2 || exit 1
fi
echo "  $(find "$CORPUS" -type f | wc -l) files · $(du -sh "$CORPUS" | cut -f1)"
sha256sum "$CORPUS"/compressed/*.* 2>/dev/null | sed 's|.*/|  |' | head -4

# extract findings + failures inside the corner (same code for container and metal)
EXTRACT='
S=$(ls -1 /w/out/POC_SUMMARY_*.md 2>/dev/null | head -1)
[ -n "$S" ] && grep -o "[0-9]* achados em base · [0-9]* em arquivos · [0-9]* falhas" "$S" | head -1
python3 - <<PYEOF
import sqlite3, os
db="/w/out/matrix.db"
if os.path.exists(db):
    c=sqlite3.connect(db)
    try:
        for r,n in c.execute("SELECT reason, COUNT(*) FROM scan_failures GROUP BY reason ORDER BY 2 DESC"):
            print("FAIL:%s=%d" % (r, n))
    except Exception:
        print("FAIL:tabela-ausente")
else: print("FAIL:sem-db")
PYEOF
'

corner() {  # $1=label $2=image $3=prep $4=mount_wheelhouse(0|1)
  NAME="$1"; IMG="$2"; PREP="$3"; MOUNT="$4"
  printf '  %-16s ' "$NAME"
  if [ "$MOUNT" = 1 ] && [ -z "$WH" ]; then
    echo "SKIP (set WHEELHOUSE_DIR for musl corners)"
    return 0
  fi
  ARGS="--rm --replace --name cfg-$NAME --platform linux/amd64 -v $CORPUS:/corpus:ro -v $HERE:/cfg:ro"
  [ "$MOUNT" = 1 ] && ARGS="$ARGS -v $WH/musllinux:/wh:ro"
  # shellcheck disable=SC2086
  podman run $ARGS "$IMG" sh -c "$PREP
. /v/bin/activate 2>/dev/null || true
export TMPDIR=/var/tmp/db && mkdir -p \$TMPDIR /w/out && cd /w
cp /cfg/config-files.yaml ./config.yaml
sed -i 's|\./corpus|/corpus|g; s|\./out|/w/out|g' ./config.yaml
data-boar --config ./config.yaml --scan-compressed --content-type-check >/w/scan.log 2>&1
$EXTRACT" > "$RES/$NAME.txt" 2>&1
  F=$(grep -o "[0-9]* em arquivos" "$RES/$NAME.txt" | head -1 | grep -o "[0-9]*")
  FAILS=$(grep "^FAIL:" "$RES/$NAME.txt" | sed 's/^FAIL://' | tr '\n' ' ')
  if [ -n "${F:-}" ]; then echo "OK ${F} findings | failures: ${FAILS:-none}"
  else echo "FAIL $(tail -2 "$RES/$NAME.txt" | tr '\n' ' ' | cut -c1-80)"; fi
}

PREP_DEB='apt-get -qq update >/dev/null 2>&1; DEBIAN_FRONTEND=noninteractive apt-get -qq install -y python3-venv >/dev/null 2>&1
python3 -m venv /v && . /v/bin/activate && pip install -q data-boar'
PREP_FED='dnf -q -y install python3 >/dev/null 2>&1; python3 -m venv /v && . /v/bin/activate && pip install -q data-boar'
PREP_ALP='apk add --no-cache libgomp >/dev/null 2>&1
python3 -m venv /v && . /v/bin/activate
pip install -q --find-links /wh data-boar
pip install -q --no-index --find-links /wh --force-reinstall numpy scipy scikit-learn pandas'
PREP_VOIDM='xbps-install -Syu xbps >/dev/null 2>&1; xbps-install -Sy python3 python3-devel >/dev/null 2>&1
python3 -m venv /v && . /v/bin/activate
pip install -q --find-links /wh data-boar
pip install -q --no-index --find-links /wh --force-reinstall numpy scipy scikit-learn pandas'

echo; echo "########## corners ##########"
# --platform linux/amd64 is mandatory: without it a local tag may be another
# arch and the corner runs emulated (30+ min stuck — measured).
corner debian   docker.io/library/debian:trixie      "$PREP_DEB"   0
corner fedora   docker.io/library/fedora:latest      "$PREP_FED"   0
corner alpine312 docker.io/library/python:3.12-alpine "$PREP_ALP"  1
corner alpine314 docker.io/library/python:3.14-alpine "$PREP_ALP"  1
corner voidmusl ghcr.io/void-linux/void-musl-full:latest "$PREP_VOIDM" 1
echo; echo "CORNERS_DONE"; date
