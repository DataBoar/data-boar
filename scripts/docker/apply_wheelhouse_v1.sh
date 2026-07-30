#!/usr/bin/env bash
# Apply hosted x86-64-v1 wheelhouse ML wheels over a PyPI install (#1387).
#
# Why: `pip install -r requirements.txt` pulls PyPI numpy/scipy with x86-64-v2+
# (popcnt). The published image must run on alpine-emachines (Celeron 900 /
# SSSE3-only, gate #821). `--find-links` alone does not prefer wheelhouse —
# force-reinstall with --no-index is required (same contract as pipx path).
#
# Image is glibc (python:3.13-slim → distroless cc-debian13): use manylinux
# cp313 cells from DataBoar/data-boar-site release wheelhouse-x86-64-v1-*.
#
# Usage (inside builder stage, after pip install -r requirements.txt):
#   bash scripts/docker/apply_wheelhouse_v1.sh
#
# Optional env:
#   WHEELHOUSE_TAG   default wheelhouse-x86-64-v1-2026-07-29
#   WHEELHOUSE_DIR   if set and non-empty, skip download and use that folder
#   SKIP_POPCNT_GATE set to 1 to skip objdump gate (not for release builds)
set -euo pipefail

WHEELHOUSE_TAG="${WHEELHOUSE_TAG:-wheelhouse-x86-64-v1-2026-07-29}"
BASE_URL="${WHEELHOUSE_BASE_URL:-https://github.com/DataBoar/data-boar-site/releases/download/${WHEELHOUSE_TAG}}"
WORKDIR="${WHEELHOUSE_DIR:-/tmp/wheelhouse-v1-glibc-cp313}"

# Filenames must match the hosted release assets (manylinux / cp313).
WHEELS=(
  "numpy-2.5.1-cp313-cp313-manylinux_2_27_x86_64.manylinux_2_28_x86_64.whl"
  "scipy-1.18.0-cp313-cp313-manylinux_2_27_x86_64.manylinux_2_28_x86_64.whl"
  "scikit_learn-1.9.0-cp313-cp313-manylinux_2_27_x86_64.manylinux_2_28_x86_64.whl"
  "pandas-3.0.5-cp313-cp313-manylinux_2_24_x86_64.manylinux_2_28_x86_64.whl"
  "boar_fast_filter-0.1.0-cp38-abi3-manylinux_2_28_x86_64.whl"
)

# Expected sha256 from release SHA256SUMS (wheelhouse-x86-64-v1-2026-07-29).
declare -A EXPECTED_SHA=(
  ["numpy-2.5.1-cp313-cp313-manylinux_2_27_x86_64.manylinux_2_28_x86_64.whl"]="d301efd02e390bd2d135205c25cd7b7fc82ec353aa3985528745601bfb67c2d6"
  ["scipy-1.18.0-cp313-cp313-manylinux_2_27_x86_64.manylinux_2_28_x86_64.whl"]="a9c3a1ae4de02b8eff37b87a7d5af19bfdbb029cc62b855fd8813acc2775c5bf"
  ["scikit_learn-1.9.0-cp313-cp313-manylinux_2_27_x86_64.manylinux_2_28_x86_64.whl"]="0d28c1b992d7a6c0951869560d0090c24ccfe44282fb2f5d7b3814b4232de418"
  ["pandas-3.0.5-cp313-cp313-manylinux_2_24_x86_64.manylinux_2_28_x86_64.whl"]="4b11c36e218331d0387cbe3a0a5f75162357a1d92d57b2b08a336ff94b19b2be"
  ["boar_fast_filter-0.1.0-cp38-abi3-manylinux_2_28_x86_64.whl"]="f664cb016fed2d530e94fa9946bb783c294e052ef19ceae4dd80bd6d12a9125a"
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
  echo "=== downloading ${WHEELHOUSE_TAG} manylinux cp313 wheels ==="
  for whl in "${WHEELS[@]}"; do
    if [[ ! -f "$whl" ]]; then
      curl -fsSL -o "$whl" "${BASE_URL}/${whl}"
    fi
  done
fi

echo "=== verifying wheel sha256 ==="
for whl in "${WHEELS[@]}"; do
  got="$(sha256sum "$whl" | awk '{print $1}')"
  want="${EXPECTED_SHA[$whl]}"
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
import boar_fast_filter
import numpy
import pandas
import scipy
import sklearn

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
    "boar_fast_filter",
    boar_fast_filter.__file__,
)
PY

# rapidfuzz ships baseline + *_avx2*.so CPU-dispatch siblings. The AVX2 modules
# contain popcnt and would fail the all-.so gate; runtime selects by CPU feature
# detector, so removing AVX2 leaves the baseline modules (same pattern as not
# shipping an ISA we refuse to execute on alpine-emachines / #821).
SITE="$(python -c 'import site; print(site.getsitepackages()[0])')"
echo "=== strip rapidfuzz *_avx2*.so under ${SITE} ==="
find "$SITE" -type f -name '*_avx2*.so' -print -delete

if [[ "${SKIP_POPCNT_GATE:-0}" == "1" ]]; then
  echo "SKIP_POPCNT_GATE=1 — skipping ISA gate (not for release)"
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
