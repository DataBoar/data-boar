#!/usr/bin/env bash
# pinned-uv.sh — print the directory of the uv pinned in .github/uv-version (#2232).
#
# stdout: ONE line, the directory that holds the pinned `uv` (prepend it to PATH).
# stderr: progress and errors. Exit 0 only when that exact uv version is available.
#
# Cache (outside the repo, global PATH untouched):
#   ${DATA_BOAR_UV_CACHE_DIR:-${XDG_CACHE_HOME:-$HOME/.cache}/data-boar}/uv-<version>/uv
# A cached binary is reused only if `uv --version` prints exactly the pinned version.
# Otherwise the official astral-sh/uv linux-x86_64 tarball is downloaded and its SHA256 is
# checked against the digest registered in tests/test_uv_version_single_source.py
# (KNOWN_LINUX_X64_SHA256, from the official release asset). No digest, no download.
# There is no skip and no fallback to another version: failure is a hard error.
#
# Test seam: PINNED_UV_BASE_URL replaces https://github.com/astral-sh/uv/releases/download
# (the digest check still applies).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VERSION_FILE="$ROOT/.github/uv-version"
GUARD_TEST="$ROOT/tests/test_uv_version_single_source.py"
BASE_URL="${PINNED_UV_BASE_URL:-https://github.com/astral-sh/uv/releases/download}"

die() {
  echo "pinned-uv.sh: ERROR: $*" >&2
  exit 1
}

[[ -f "$VERSION_FILE" ]] || die "$VERSION_FILE not found"
VERSION="$(tr -d '[:space:]' <"$VERSION_FILE")"
[[ "$VERSION" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]] || die "$VERSION_FILE must hold only a version like 0.11.2, got '$VERSION'"

CACHE_ROOT="${DATA_BOAR_UV_CACHE_DIR:-${XDG_CACHE_HOME:-${HOME}/.cache}/data-boar}"
DEST_DIR="$CACHE_ROOT/uv-$VERSION"
DEST_BIN="$DEST_DIR/uv"

reported_version() {
  "$1" --version 2>/dev/null | awk 'NR==1 {print $2}'
}

if [[ -x "$DEST_BIN" ]] && [[ "$(reported_version "$DEST_BIN")" == "$VERSION" ]]; then
  echo "pinned-uv.sh: using cached uv $VERSION ($DEST_BIN)" >&2
  echo "$DEST_DIR"
  exit 0
fi

# Not cached (or cache holds another version): download, verify, install.
[[ -f "$GUARD_TEST" ]] || die "$GUARD_TEST not found (digest registry)"
EXPECTED_SHA="$(grep -oE "\"${VERSION//./\\.}\": *\"[0-9a-f]{64}\"" "$GUARD_TEST" | head -n1 | grep -oE '[0-9a-f]{64}' || true)"
[[ -n "$EXPECTED_SHA" ]] || die "no official SHA256 registered for uv $VERSION in $GUARD_TEST; refusing to download an unverified binary"

case "$(uname -s)-$(uname -m)" in
  Linux-x86_64) TARGET="uv-x86_64-unknown-linux-gnu" ;;
  *) die "no pinned digest for platform $(uname -s)-$(uname -m); only linux-x86_64 is registered (install uv $VERSION yourself and put it first on PATH)" ;;
esac

command -v curl >/dev/null 2>&1 || die "curl not found"
command -v sha256sum >/dev/null 2>&1 || die "sha256sum not found"

mkdir -p "$CACHE_ROOT" || die "cannot create cache dir $CACHE_ROOT"
TMP="$(mktemp -d "$CACHE_ROOT/.fetch-XXXXXX")"
trap 'rm -rf "$TMP"' EXIT

URL="$BASE_URL/$VERSION/$TARGET.tar.gz"
echo "pinned-uv.sh: downloading uv $VERSION from $URL" >&2
curl --fail --silent --show-error --location --retry 3 --connect-timeout 20 --max-time 300 \
  "$URL" -o "$TMP/uv.tgz" || die "download of uv $VERSION failed ($URL)"

ACTUAL_SHA="$(sha256sum "$TMP/uv.tgz" | awk '{print $1}')"
[[ "$ACTUAL_SHA" == "$EXPECTED_SHA" ]] || die "SHA256 mismatch for uv $VERSION: expected $EXPECTED_SHA, got $ACTUAL_SHA"

tar -xzf "$TMP/uv.tgz" -C "$TMP" || die "cannot extract the uv tarball"
[[ -f "$TMP/$TARGET/uv" ]] || die "tarball has no $TARGET/uv"
mkdir -p "$DEST_DIR"
install -m 0755 "$TMP/$TARGET/uv" "$DEST_BIN.new"
mv -f "$DEST_BIN.new" "$DEST_BIN"

[[ "$(reported_version "$DEST_BIN")" == "$VERSION" ]] || die "installed uv reports '$(reported_version "$DEST_BIN")', expected $VERSION"
echo "pinned-uv.sh: installed uv $VERSION in $DEST_DIR (SHA256 verified)" >&2
echo "$DEST_DIR"
