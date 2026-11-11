#!/usr/bin/env bash
# haiku_build_wheels.sh — run INSIDE a Haiku guest: build one wheel per requirements pin (#2175).
#
# Usage: haiku_build_wheels.sh <requirements.txt> <out-dir>
#   PYTHON=python3 PER_PKG_TIMEOUT=2400 NO_ISOLATION_PKGS="numpy pandas scipy scikit-learn" \
#     haiku_build_wheels.sh requirements.txt ~/haiku-wheelhouse
#
# No Docker, no auditwheel: Haiku has neither. It writes, under <out-dir>:
#   wheels/        the built wheels (pip wheel --no-deps, one pin at a time)
#   results.tsv    package, status (OK | OK_NO_ISOLATION | SKIP | FAIL | TIMEOUT), seconds
#   platform.txt   sysconfig.get_platform() as reported by the guest (never assume the tag)
#   SHA256SUMS     checksums of every wheel (publish gate: verify_release_sha256sums.sh)
# Exit: 0 all pins built or skipped; 2 at least one FAIL or TIMEOUT (see results.tsv).
#
# STATUS: written from the #2175 measurements; it has NOT been run on a Haiku guest yet.
# The hermetic test (tests/test_haiku_build_wheels.py) exercises it with a fake interpreter.
set -euo pipefail

REQ="${1:?usage: haiku_build_wheels.sh <requirements.txt> <out-dir>}"
OUT="${2:?usage: haiku_build_wheels.sh <requirements.txt> <out-dir>}"
PY="${PYTHON:-python3}"
PER_PKG_TIMEOUT="${PER_PKG_TIMEOUT:-2400}"
NO_ISOLATION_PKGS="${NO_ISOLATION_PKGS:-numpy pandas scipy scikit-learn}"

[ -f "$REQ" ] || { echo "error: $REQ not found" >&2; exit 1; }
WHEELS="$OUT/wheels"
RESULTS="$OUT/results.tsv"
mkdir -p "$WHEELS"

"$PY" -c 'import sysconfig; print(sysconfig.get_platform())' > "$OUT/platform.txt"
printf 'package\tstatus\tseconds\n' > "$RESULTS"

count_wheels() { find "$WHEELS" -maxdepth 1 -name '*.whl' | wc -l | tr -d ' '; }

in_list() { # in_list <name> <space separated list>
  local n="$1" item
  for item in $2; do [ "$item" = "$n" ] && return 0; done
  return 1
}

failed=0
while IFS= read -r line; do
  # uv-export lines look like: name==1.2.3 ; marker \   (hash lines and comments are skipped)
  [[ $line =~ ^([A-Za-z0-9_.-]+)==([^[:space:];\\]+)(.*)$ ]] || continue
  name="${BASH_REMATCH[1]}"
  spec="$name==${BASH_REMATCH[2]}"
  rest="${BASH_REMATCH[3]}"
  if [[ $rest == *";"* ]]; then
    marker="${rest#*;}"
    marker="${marker%\\}"
    spec="$spec ;$marker"   # pip evaluates the marker and ignores a non-matching pin
  fi

  before="$(count_wheels)"
  start=$SECONDS
  status=FAIL
  rc=0
  timeout "$PER_PKG_TIMEOUT" "$PY" -m pip wheel --no-deps -w "$WHEELS" "$spec" >/dev/null 2>&1 || rc=$?
  if [ "$rc" -eq 0 ]; then
    status=OK
  elif [ "$rc" -eq 124 ]; then
    status=TIMEOUT
  elif in_list "$name" "$NO_ISOLATION_PKGS"; then
    rc=0
    timeout "$PER_PKG_TIMEOUT" "$PY" -m pip wheel --no-deps --no-build-isolation \
      -w "$WHEELS" "$spec" >/dev/null 2>&1 || rc=$?
    if [ "$rc" -eq 0 ]; then status=OK_NO_ISOLATION; elif [ "$rc" -eq 124 ]; then status=TIMEOUT; fi
  fi
  if [ "$status" = OK ] && [ "$(count_wheels)" = "$before" ]; then
    status=SKIP   # pip exited 0 without producing a wheel: marker did not match
  fi
  case "$status" in FAIL|TIMEOUT) failed=1 ;; esac
  printf '%s\t%s\t%s\n' "$name" "$status" "$((SECONDS - start))" >> "$RESULTS"
done < "$REQ"

if [ "$(count_wheels)" -gt 0 ]; then
  (cd "$WHEELS" && sha256sum -- *.whl > ../SHA256SUMS)
fi
echo "platform: $(cat "$OUT/platform.txt")  wheels: $(count_wheels)  results: $RESULTS" >&2
[ "$failed" -eq 0 ] || exit 2
