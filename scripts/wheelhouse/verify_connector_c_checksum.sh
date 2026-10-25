#!/usr/bin/env bash
# verify_connector_c_checksum.sh — download Connector/C tarball and fail if sha256
# diverges from recipe-manifest.yaml (#1379 / #1367).
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
if command -v uv >/dev/null 2>&1 && [ -f "$HERE/../../pyproject.toml" ]; then
  LOAD=(uv run --project "$HERE/../.." python "$HERE/load_manifest.py")
else
  LOAD=(python3 "$HERE/load_manifest.py")
fi

URL="$("${LOAD[@]}" --get mariadb_connector_c.tarball_url)"
EXPECT="$("${LOAD[@]}" --get mariadb_connector_c.sha256)"
VER="$("${LOAD[@]}" --get mariadb_connector_c.version)"
TMP="${TMPDIR:-/tmp}/mariadb-connector-c-ci-$$.tar.gz"

echo "=== Connector/C v$VER checksum gate ==="
echo "    url:    $URL"
echo "    expect: $EXPECT"
curl -fsSL -o "$TMP" "$URL"
GOT="$(sha256sum "$TMP" | awk '{print $1}')"
echo "    got:    $GOT"
rm -f "$TMP"
if [ "$GOT" != "$EXPECT" ]; then
  echo "FAIL: Connector/C tarball sha256 diverges from recipe-manifest.yaml"
  echo "      (PLAN / #1367 pin is the same file — do not patch the hash in CI YAML)"
  exit 1
fi
echo "OK: Connector/C sha256 matches manifest"
