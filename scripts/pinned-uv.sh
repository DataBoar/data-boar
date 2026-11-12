#!/usr/bin/env bash
# pinned-uv.sh — print the directory of the uv pinned in .github/uv-version (#2232).
#
# stdout: ONE line, the directory that holds the pinned `uv` (prepend it to PATH).
# stderr: progress and errors. Exit 0 only when that exact uv version is available.
#
# Cache (outside the repo, global PATH untouched):
#   ${DATA_BOAR_UV_CACHE_DIR:-${XDG_CACHE_HOME:-$HOME/.cache}/data-boar}/uv-<version>/uv
# Resolution order (every step needs `uv --version` to print EXACTLY the pinned version):
#   1. the cached binary;
#   2. a uv already on PATH (any platform; it is linked into the cache dir, not hashed);
#   3. otherwise the official astral-sh/uv release asset of THIS platform is downloaded (Linux and
#      macOS, x86_64 and aarch64; Windows is covered by the twin scripts/pinned-uv.ps1) and its SHA256
#      is checked against the digest registered in tests/test_uv_version_single_source.py
#      (KNOWN_ASSET_SHA256, one entry per <version>/<asset>, from the official release). No digest,
#      no download.
# There is no skip and no fallback to another version: failure is a hard error.
# Cross-platform twin: scripts/pinned-uv.ps1 (same contract; keep them in sync, see
# docs/ops/SCRIPTS_CROSS_PLATFORM_PAIRING.md).
#
# Test seams: PINNED_UV_BASE_URL replaces https://github.com/astral-sh/uv/releases/download (the
# digest check still applies); PINNED_UV_UNAME overrides "<uname -s>-<uname -m>" (e.g. Darwin-arm64).
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

# Any platform: a uv of EXACTLY the pinned version already on PATH is enough. We do not hash
# an install the developer made themselves; the digest registry only guards what we download.
# It is exposed through the cache dir (a symlink), so PATH order cannot shadow it later.
PATH_UV="$(command -v uv 2>/dev/null || true)"
if [[ -n "$PATH_UV" ]]; then
  PATH_UV="$(cd "$(dirname "$PATH_UV")" && pwd)/$(basename "$PATH_UV")"
  if [[ "$(reported_version "$PATH_UV")" == "$VERSION" ]]; then
    mkdir -p "$DEST_DIR" || die "cannot create cache dir $DEST_DIR"
    ln -sfn "$PATH_UV" "$DEST_BIN"
    echo "pinned-uv.sh: using uv $VERSION found on PATH ($PATH_UV)" >&2
    echo "$DEST_DIR"
    exit 0
  fi
fi

# Not cached, not on PATH (or only other versions there): download, verify, install.
PLATFORM="${PINNED_UV_UNAME:-$(uname -s)-$(uname -m)}"
case "$PLATFORM" in
  Linux-x86_64) ASSET="uv-x86_64-unknown-linux-gnu.tar.gz" ;;
  Linux-aarch64 | Linux-arm64) ASSET="uv-aarch64-unknown-linux-gnu.tar.gz" ;;
  Darwin-x86_64) ASSET="uv-x86_64-apple-darwin.tar.gz" ;;
  Darwin-arm64 | Darwin-aarch64) ASSET="uv-aarch64-apple-darwin.tar.gz" ;;
  *) die "no uv $VERSION in the cache ($DEST_BIN) or on PATH, and this script downloads only for Linux and macOS on x86_64/aarch64 (this platform: $PLATFORM; on Windows use scripts/pinned-uv.ps1). Install uv $VERSION so that 'uv --version' reports exactly $VERSION and keep it on PATH (this script finds it there), or place it at $DEST_BIN" ;;
esac
TARGET="${ASSET%.tar.gz}"

[[ -f "$GUARD_TEST" ]] || die "$GUARD_TEST not found (digest registry)"
EXPECTED_SHA="$(grep -oE "\"${VERSION//./\\.}/${ASSET//./\\.}\": *\"[0-9a-f]{64}\"" "$GUARD_TEST" | head -n1 | grep -oE '[0-9a-f]{64}' || true)"
[[ -n "$EXPECTED_SHA" ]] || die "no official SHA256 registered for uv $VERSION / $ASSET in $GUARD_TEST (KNOWN_ASSET_SHA256); refusing to download an unverified binary"

command -v curl >/dev/null 2>&1 || die "curl not found"
# Stock macOS ships `shasum`, not `sha256sum` (Bugbot, #2233): accept either, same digest.
sha256_of() {
  if command -v sha256sum >/dev/null 2>&1; then
    sha256sum "$1" | awk '{print $1}'
  elif command -v shasum >/dev/null 2>&1; then
    shasum -a 256 "$1" | awk '{print $1}'
  else
    return 1
  fi
}
command -v sha256sum >/dev/null 2>&1 || command -v shasum >/dev/null 2>&1 || die "neither sha256sum nor shasum found (needed to verify the download)"

mkdir -p "$CACHE_ROOT" || die "cannot create cache dir $CACHE_ROOT"
TMP="$(mktemp -d "$CACHE_ROOT/.fetch-XXXXXX")"
trap 'rm -rf "$TMP"' EXIT

URL="$BASE_URL/$VERSION/$ASSET"
echo "pinned-uv.sh: downloading uv $VERSION from $URL" >&2
curl --fail --silent --show-error --location --retry 3 --connect-timeout 20 --max-time 300 \
  "$URL" -o "$TMP/uv.tgz" || die "download of uv $VERSION failed ($URL)"

ACTUAL_SHA="$(sha256_of "$TMP/uv.tgz")" || die "cannot compute the SHA256 of the download"
[[ "$ACTUAL_SHA" == "$EXPECTED_SHA" ]] || die "SHA256 mismatch for uv $VERSION ($ASSET): expected $EXPECTED_SHA, got $ACTUAL_SHA"

tar -xzf "$TMP/uv.tgz" -C "$TMP" || die "cannot extract the uv tarball"
[[ -f "$TMP/$TARGET/uv" ]] || die "tarball has no $TARGET/uv"
mkdir -p "$DEST_DIR"
install -m 0755 "$TMP/$TARGET/uv" "$DEST_BIN.new"
mv -f "$DEST_BIN.new" "$DEST_BIN"

[[ "$(reported_version "$DEST_BIN")" == "$VERSION" ]] || die "installed uv reports '$(reported_version "$DEST_BIN")', expected $VERSION"
echo "pinned-uv.sh: installed uv $VERSION in $DEST_DIR (SHA256 verified)" >&2
echo "$DEST_DIR"
