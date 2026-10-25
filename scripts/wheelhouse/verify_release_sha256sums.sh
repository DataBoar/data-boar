#!/usr/bin/env bash
# verify_release_sha256sums.sh — fail if SHA256SUMS does not cover every .whl (#1410)
#
# Prevents the class of bug where wheels are appended to a GitHub Release after
# SHA256SUMS was generated (cp314t cells 2026-07-30 without regenerating checksums).
#
# Modes:
#   Local folder (publish preflight):
#     ./scripts/wheelhouse/verify_release_sha256sums.sh --dir /path/to/wheels
#       Expects SHA256SUMS + *.whl in that directory.
#
#   Hosted release (CI / post-upload check):
#     ./scripts/wheelhouse/verify_release_sha256sums.sh \
#       --repo DataBoar/data-boar-site --tag wheelhouse-x86-64-v1-2026-07-29
#
# Exit 0 = line count of checksum entries equals .whl count and every wheel is listed.
# Exit 1 = divergence or missing files.
set -euo pipefail

REPO=""
TAG=""
DIR=""
STRICT_NAMES=1

usage() {
  sed -n '2,20p' "$0" | sed 's/^# \{0,1\}//'
  exit 2
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dir) DIR="${2:-}"; shift 2 ;;
    --repo) REPO="${2:-}"; shift 2 ;;
    --tag) TAG="${2:-}"; shift 2 ;;
    --help|-h) usage ;;
    *) echo "unknown arg: $1" >&2; usage ;;
  esac
done

count_sum_lines() {
  local f="$1"
  # GNU sha256sum format: "<hex>  <filename>" — ignore blank / comment lines
  grep -E '^[0-9a-fA-F]{64}[[:space:]]+' "$f" | wc -l | tr -d ' '
}

list_sum_names() {
  local f="$1"
  # Prefer field 2+ (filenames may theoretically contain spaces; our wheels do not)
  awk '/^[0-9a-fA-F]{64}[[:space:]]+/ { $1=""; sub(/^ /,""); print }' "$f" | sort
}

if [[ -n "$DIR" ]]; then
  [[ -d "$DIR" ]] || { echo "FAIL: --dir not a directory: $DIR" >&2; exit 1; }
  SUMS="$DIR/SHA256SUMS"
  [[ -f "$SUMS" ]] || { echo "FAIL: missing $SUMS" >&2; exit 1; }
  mapfile -t WHLS < <(find "$DIR" -maxdepth 1 -type f -name '*.whl' -printf '%f\n' | sort)
  WHL_COUNT="${#WHLS[@]}"
  SUM_COUNT="$(count_sum_lines "$SUMS")"
  echo "local dir=$DIR  whl=$WHL_COUNT  sha256sums_lines=$SUM_COUNT"
  if [[ "$WHL_COUNT" -eq 0 ]]; then
    echo "FAIL: no .whl files in $DIR" >&2
    exit 1
  fi
  if [[ "$SUM_COUNT" != "$WHL_COUNT" ]]; then
    echo "FAIL: SHA256SUMS line count ($SUM_COUNT) != .whl count ($WHL_COUNT)" >&2
    exit 1
  fi
  if [[ "$STRICT_NAMES" -eq 1 ]]; then
    TMP=$(mktemp -d)
    printf '%s\n' "${WHLS[@]}" >"$TMP/whls"
    list_sum_names "$SUMS" >"$TMP/sums"
    if ! diff -u "$TMP/whls" "$TMP/sums" >/tmp/sha256sums-name-diff.txt; then
      echo "FAIL: SHA256SUMS names do not match .whl set:" >&2
      cat /tmp/sha256sums-name-diff.txt >&2
      rm -rf "$TMP"
      exit 1
    fi
    rm -rf "$TMP"
  fi
  echo "OK: SHA256SUMS covers all $WHL_COUNT wheels"
  exit 0
fi

if [[ -n "$REPO" && -n "$TAG" ]]; then
  command -v gh >/dev/null || { echo "FAIL: gh CLI required for --repo/--tag" >&2; exit 1; }
  TMP=$(mktemp -d)
  trap 'rm -rf "$TMP"' EXIT
  gh release view "$TAG" --repo "$REPO" --json assets \
    --jq '.assets[].name' | sort >"$TMP/assets"
  grep '\.whl$' "$TMP/assets" >"$TMP/whls" || true
  WHL_COUNT=$(wc -l <"$TMP/whls" | tr -d ' ')
  if ! grep -qx 'SHA256SUMS' "$TMP/assets"; then
    echo "FAIL: release $TAG on $REPO has no SHA256SUMS asset (whl=$WHL_COUNT)" >&2
    exit 1
  fi
  gh release download "$TAG" --repo "$REPO" --pattern 'SHA256SUMS' --dir "$TMP"
  SUM_COUNT="$(count_sum_lines "$TMP/SHA256SUMS")"
  echo "release=$REPO@$TAG  whl=$WHL_COUNT  sha256sums_lines=$SUM_COUNT"
  if [[ "$WHL_COUNT" -eq 0 ]]; then
    echo "FAIL: release has no .whl assets" >&2
    exit 1
  fi
  if [[ "$SUM_COUNT" != "$WHL_COUNT" ]]; then
    echo "FAIL: SHA256SUMS line count ($SUM_COUNT) != .whl count ($WHL_COUNT)" >&2
    echo "missing from SUMS:" >&2
    comm -23 "$TMP/whls" <(list_sum_names "$TMP/SHA256SUMS") >&2 || true
    exit 1
  fi
  if [[ "$STRICT_NAMES" -eq 1 ]]; then
    list_sum_names "$TMP/SHA256SUMS" >"$TMP/sums"
    if ! diff -u "$TMP/whls" "$TMP/sums" >/tmp/sha256sums-name-diff.txt; then
      echo "FAIL: SHA256SUMS names do not match release .whl set:" >&2
      cat /tmp/sha256sums-name-diff.txt >&2
      exit 1
    fi
  fi
  echo "OK: SHA256SUMS covers all $WHL_COUNT wheels on $REPO@$TAG"
  exit 0
fi

echo "FAIL: provide --dir DIR  or  --repo OWNER/REPO --tag TAG" >&2
usage
