#!/usr/bin/env bash
# Apply hosted x86-64-v1 / cp314t wheelhouse ML wheels over a PyPI install (#1387).
#
# Why: `pip install -r requirements.txt` pulls PyPI numpy/scipy with x86-64-v2+
# (popcnt). The published GIL image must run on alpine-emachines (Celeron 900 /
# SSSE3-only, gate #821). `--find-links` alone does not prefer wheelhouse —
# force-reinstall with --no-index is required (same contract as pipx path).
#
# Image is glibc (python:*-slim → distroless cc-debian13): use manylinux
# cells matching the builder interpreter ABI from
# DataBoar/data-boar-site release wheelhouse-x86-64-v1-*.
#
# Free-threaded (no-GIL / cp314t): abi3 boar_fast_filter does NOT load; use the
# dedicated cp314t wheel. popcnt==0 gate does NOT apply — numpy cp314t is
# intentionally x86-64-v2+ (operator decision; Celeron is not a nogil target).
#
# Usage (inside builder stage, after pip install -r requirements.txt):
#   bash scripts/docker/apply_wheelhouse_v1.sh
#
# Optional env:
#   WHEELHOUSE_TAG   default wheelhouse-x86-64-v1-2026-07-29
#   WHEELHOUSE_DIR   if set and non-empty, skip download and use that folder
#   SKIP_POPCNT_GATE set to 1 to skip objdump gate (auto for free-threaded)
set -euo pipefail

WHEELHOUSE_TAG="${WHEELHOUSE_TAG:-wheelhouse-x86-64-v1-2026-07-29}"
BASE_URL="${WHEELHOUSE_BASE_URL:-https://github.com/DataBoar/data-boar-site/releases/download/${WHEELHOUSE_TAG}}"

# Derive platform / ABI tags from the builder interpreter.
# GIL 3.14 → py_tag=cp314 abi_tag=cp314; free-threaded → abi_tag=cp314t.
# Never hardcode: wrong ABI installs the wrong wheel or fails force-reinstall.
eval "$(
  python - <<'PY'
import sys
import sysconfig

maj, minor = sys.version_info.major, sys.version_info.minor
py_tag = f"cp{maj}{minor}"
soabi = sysconfig.get_config_var("SOABI") or ""
gil_disabled = bool(sysconfig.get_config_var("Py_GIL_DISABLED"))
freethreaded = gil_disabled or (f"{maj}{minor}t" in soabi)
abi_tag = f"cp{maj}{minor}t" if freethreaded else py_tag
print(f"PY_TAG={py_tag}")
print(f"ABI_TAG={abi_tag}")
print(f"FREETHREADED={'1' if freethreaded else '0'}")
print(f"CP={abi_tag}")
PY
)"

WORKDIR="${WHEELHOUSE_DIR:-/tmp/wheelhouse-v1-glibc-${CP}}"

if [[ "${FREETHREADED}" == "1" ]]; then
  # Free-threaded: dedicated boar_fast_filter cp314t (abi3 does not load).
  WHEELS=(
    "numpy-2.5.1-${PY_TAG}-${ABI_TAG}-manylinux_2_27_x86_64.manylinux_2_28_x86_64.whl"
    "scipy-1.18.0-${PY_TAG}-${ABI_TAG}-manylinux_2_27_x86_64.manylinux_2_28_x86_64.whl"
    "scikit_learn-1.9.0-${PY_TAG}-${ABI_TAG}-manylinux_2_27_x86_64.manylinux_2_28_x86_64.whl"
    "pandas-3.0.5-${PY_TAG}-${ABI_TAG}-manylinux_2_24_x86_64.manylinux_2_28_x86_64.whl"
    "boar_fast_filter-0.1.0-${PY_TAG}-${ABI_TAG}-manylinux_2_28_x86_64.whl"
  )
  # Operator contract: cp314t numpy has popcnt≠0 (x86-64-v2+). Do not force v1.
  SKIP_POPCNT_GATE="${SKIP_POPCNT_GATE:-1}"
else
  # GIL: abi3 boar_fast_filter serves all CPython 3.8+.
  WHEELS=(
    "numpy-2.5.1-${PY_TAG}-${ABI_TAG}-manylinux_2_27_x86_64.manylinux_2_28_x86_64.whl"
    "scipy-1.18.0-${PY_TAG}-${ABI_TAG}-manylinux_2_27_x86_64.manylinux_2_28_x86_64.whl"
    "scikit_learn-1.9.0-${PY_TAG}-${ABI_TAG}-manylinux_2_27_x86_64.manylinux_2_28_x86_64.whl"
    "pandas-3.0.5-${PY_TAG}-${ABI_TAG}-manylinux_2_24_x86_64.manylinux_2_28_x86_64.whl"
    "boar_fast_filter-0.1.0-cp38-abi3-manylinux_2_28_x86_64.whl"
  )
fi

# Expected sha256 from release assets (wheelhouse-x86-64-v1-2026-07-29).
# Note: release SHA256SUMS may lag new cells — digests below measured from assets.
declare -A EXPECTED_SHA=(
  ["numpy-2.5.1-cp313-cp313-manylinux_2_27_x86_64.manylinux_2_28_x86_64.whl"]="d301efd02e390bd2d135205c25cd7b7fc82ec353aa3985528745601bfb67c2d6"
  ["scipy-1.18.0-cp313-cp313-manylinux_2_27_x86_64.manylinux_2_28_x86_64.whl"]="a9c3a1ae4de02b8eff37b87a7d5af19bfdbb029cc62b855fd8813acc2775c5bf"
  ["scikit_learn-1.9.0-cp313-cp313-manylinux_2_27_x86_64.manylinux_2_28_x86_64.whl"]="0d28c1b992d7a6c0951869560d0090c24ccfe44282fb2f5d7b3814b4232de418"
  ["pandas-3.0.5-cp313-cp313-manylinux_2_24_x86_64.manylinux_2_28_x86_64.whl"]="4b11c36e218331d0387cbe3a0a5f75162357a1d92d57b2b08a336ff94b19b2be"
  ["numpy-2.5.1-cp314-cp314-manylinux_2_27_x86_64.manylinux_2_28_x86_64.whl"]="0277af072c85878e95f14e6f5b5ac7f32b4376cfa007f0bf08bbeb9f09a6f600"
  ["scipy-1.18.0-cp314-cp314-manylinux_2_27_x86_64.manylinux_2_28_x86_64.whl"]="096c50481f7e78353d82ce1cdd01256ac379443d8b5b9a5b0a1408cbf990000a"
  ["scikit_learn-1.9.0-cp314-cp314-manylinux_2_27_x86_64.manylinux_2_28_x86_64.whl"]="1f2c048e96ad44db5775adc80d7d0c1f3db7c5c7e837950b4b0a42afa28ffdcb"
  ["pandas-3.0.5-cp314-cp314-manylinux_2_24_x86_64.manylinux_2_28_x86_64.whl"]="9e94c2c5ca43bd3ca32bf64d32308887b65e5f9bfd8023ea52755107a999f93b"
  ["boar_fast_filter-0.1.0-cp38-abi3-manylinux_2_28_x86_64.whl"]="f664cb016fed2d530e94fa9946bb783c294e052ef19ceae4dd80bd6d12a9125a"
  ["numpy-2.5.1-cp314-cp314t-manylinux_2_27_x86_64.manylinux_2_28_x86_64.whl"]="99d5095fa265a0c4152e7bb12759e14381ef5496152f1ce58f44bdf55c44beb4"
  ["scipy-1.18.0-cp314-cp314t-manylinux_2_27_x86_64.manylinux_2_28_x86_64.whl"]="945c1761b93f38d7f99ae81ae80c63e621471608c7eeead563f6df025585cd58"
  ["scikit_learn-1.9.0-cp314-cp314t-manylinux_2_27_x86_64.manylinux_2_28_x86_64.whl"]="5bad8f8b9950321b54c965fdcbac6c6c55e79e16646b49977bcf3668d3870a1a"
  ["pandas-3.0.5-cp314-cp314t-manylinux_2_24_x86_64.manylinux_2_28_x86_64.whl"]="ef01af4d8dc6cd2c8d6c7736f149574ef93fe043811eeb5e445f2647154b5040"
  ["boar_fast_filter-0.1.0-cp314-cp314t-manylinux_2_28_x86_64.whl"]="a28588c4fabe3c7e41e142b9477facc814d658a972f0d314c5104fedfc37af68"
)

UMATH_MAX_BYTES="${NUMPY_UMATH_SO_MAX_BYTES:-8000000}"
POPCNT_MAX="${NUMPY_POPCNT_MAX:-0}"

mkdir -p "$WORKDIR"
cd "$WORKDIR"

need_download=0
for whl in "${WHEELS[@]}"; do
  if [[ ! -f "$whl" ]]; then
    need_download=1
    break
  fi
done

if [[ "$need_download" -eq 1 ]]; then
  echo "=== downloading ${WHEELHOUSE_TAG} manylinux ${PY_TAG}/${ABI_TAG} wheels (freethreaded=${FREETHREADED}) ==="
  for whl in "${WHEELS[@]}"; do
    if [[ ! -f "$whl" ]]; then
      curl -fsSL -o "$whl" "${BASE_URL}/${whl}"
    fi
  done
fi

echo "=== verifying wheel sha256 ==="
for whl in "${WHEELS[@]}"; do
  got="$(sha256sum "$whl" | awk '{print $1}')"
  want="${EXPECTED_SHA[$whl]:-}"
  if [[ -z "$want" ]]; then
    echo "FATAL: no EXPECTED_SHA entry for $whl (ABI ${ABI_TAG})" >&2
    exit 1
  fi
  if [[ "$got" != "$want" ]]; then
    echo "FATAL: sha256 mismatch for $whl" >&2
    echo "  want $want" >&2
    echo "  got  $got" >&2
    exit 1
  fi
  echo "OK $whl"
done

echo "=== force-reinstall ML stack + boar_fast_filter from wheelhouse (--no-index) ==="
# --no-deps: do not resolve from PyPI; pure deps already present from requirements.txt.
python -m pip install --no-cache-dir --no-index --find-links "$WORKDIR" \
  --force-reinstall --no-deps \
  numpy scipy scikit-learn pandas boar_fast_filter

python - <<'PY'
import pathlib
import sysconfig

import boar_fast_filter
import numpy
import pandas
import scipy
import sklearn

pkg = pathlib.Path(boar_fast_filter.__file__).resolve().parent
sos = sorted(pkg.rglob("*.so"))
print(
    "imports_ok",
    "numpy",
    numpy.__version__,
    "scipy",
    scipy.__version__,
    "sklearn",
    sklearn.__version__,
    "pandas",
    pandas.__version__,
    "boar_fast_filter_pkg",
    pkg,
    "filter_sos",
    [p.name for p in sos],
    "SOABI",
    sysconfig.get_config_var("SOABI"),
)
if not sos:
    raise SystemExit(f"FATAL: no .so under boar_fast_filter package: {pkg}")
# Free-threaded must not ship abi3 filter; GIL expects abi3 or versioned .so.
if bool(sysconfig.get_config_var("Py_GIL_DISABLED")):
    if any("abi3" in p.name for p in sos):
        raise SystemExit(f"FATAL: free-threaded image loaded abi3 filter: {sos}")
    if not any("314t" in p.name for p in sos):
        raise SystemExit(f"FATAL: expected cpython-314t filter .so, got: {sos}")
PY

# rapidfuzz ships baseline + *_avx2*.so CPU-dispatch siblings. The AVX2 modules
# contain popcnt and would fail the all-.so gate; runtime selects by CPU feature
# detector, so removing AVX2 leaves the baseline modules (same pattern as not
# shipping an ISA we refuse to execute on alpine-emachines / #821).
SITE="$(python -c 'import site; print(site.getsitepackages()[0])')"
echo "=== strip rapidfuzz *_avx2*.so under ${SITE} ==="
find "$SITE" -type f -name '*_avx2*.so' -print -delete

if [[ "${SKIP_POPCNT_GATE:-0}" == "1" ]]; then
  if [[ "${FREETHREADED}" == "1" ]]; then
    echo "SKIP_POPCNT_GATE=1 — free-threaded / x86-64-v2+ contract (popcnt gate N/A)"
  else
    echo "SKIP_POPCNT_GATE=1 — skipping ISA gate (not for GIL release builds)"
  fi
  python -c 'import rapidfuzz; print("rapidfuzz_ok", rapidfuzz.__version__)'
  echo "OK GATE: wheelhouse applied (freethreaded=${FREETHREADED}, popcnt_gate=skipped)"
  exit 0
fi

if ! command -v objdump >/dev/null 2>&1; then
  echo "FATAL: objdump required for popcnt gate (install binutils)" >&2
  exit 1
fi

echo "=== ISA gate: umath size + popcnt==0 on ALL site-packages .so ==="
mapfile -t SOS < <(find "$SITE" -type f -name '*.so' | sort)

umath=""
nonzero=0
for so in "${SOS[@]}"; do
  base="$(basename "$so")"
  if [[ "$base" == _multiarray_umath*.so ]]; then
    umath="$so"
  fi
  count="$(objdump -d "$so" 2>/dev/null | grep -c popcnt || true)"
  if [[ "$count" -gt "$POPCNT_MAX" ]]; then
    echo "FATAL: popcnt=$count > max=$POPCNT_MAX in $so" >&2
    nonzero=$((nonzero + 1))
  fi
done

if [[ "$nonzero" -gt 0 ]]; then
  echo "FATAL: ${nonzero} .so file(s) with popcnt above max=${POPCNT_MAX}" >&2
  exit 1
fi

if [[ -z "$umath" ]]; then
  echo "FATAL: _multiarray_umath*.so not found after wheelhouse install" >&2
  exit 1
fi

sz="$(stat -c%s "$umath")"
echo "umath=$umath size=$sz scanned_so=${#SOS[@]} popcnt_max=$POPCNT_MAX"
if [[ "$sz" -ge "$UMATH_MAX_BYTES" ]]; then
  echo "FATAL: umath size $sz >= max $UMATH_MAX_BYTES (PyPI AVX signature)" >&2
  exit 1
fi
# Soft band from issue AC (~5.1–5.3 MB). Hard fail stays at UMATH_MAX_BYTES.
if [[ "$sz" -lt 5000000 || "$sz" -gt 5500000 ]]; then
  echo "WARN: umath size $sz outside expected ~5.1–5.3 MB band (still < $UMATH_MAX_BYTES)"
fi

# rapidfuzz must still import after AVX2 strip.
python -c 'import rapidfuzz; print("rapidfuzz_ok", rapidfuzz.__version__)'

echo "OK GATE: wheelhouse v1 applied — umath ${sz} B, popcnt=0 on ${#SOS[@]} site-packages .so"
