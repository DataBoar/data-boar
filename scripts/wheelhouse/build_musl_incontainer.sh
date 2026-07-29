#!/bin/sh
# build_musl_incontainer.sh — port of vault build-v1-musl.sh for CI (#1379).
# Runs INSIDE docker.io/library/python:X.Y-alpine.
# Package pins and gates come from env (loaded from recipe-manifest.yaml on the host).
set -e
: "${NUMPY_SPEC:?}" "${SCIPY_SPEC:?}" "${SKLEARN_SPEC:?}" "${PANDAS_SPEC:?}"
: "${PURE_WHEELS:?}" "${NUMPY_MESON_PIP_ARGS:?}"
: "${GATE_POPCNT_MAX:?}" "${GATE_UMATH_MAX_BYTES:?}"
: "${AUDITWHEEL_PLAT:?}"

PYV="$(python3 -c 'import sys;print("%d.%d"%sys.version_info[:2])')"
echo "=== alpine $(cat /etc/alpine-release) | python $PYV | nproc=$(nproc) ==="
export TMPDIR="${TMPDIR:-/var/tmp/data-boar-build}"
mkdir -p "$TMPDIR" /out

apk add --no-cache build-base openblas openblas-dev gfortran patchelf binutils >/dev/null
python3 -m venv /v && . /v/bin/activate
pip install --no-cache-dir -q Cython meson-python ninja pythran pybind11 setuptools auditwheel
# CRITICAL: block PyPI scipy-openblas so the build links SYSTEM OpenBLAS (DYNAMIC_ARCH).
pip uninstall -y scipy-openblas64 scipy-openblas32 >/dev/null 2>&1 || true

echo "=== [1/4] numpy x86-64-v1 (cpu-baseline=none) ==="; date
# --no-build-isolation is MANDATORY: with isolation, -Dcpu-baseline=none never
# reaches meson → wheel byte-identical to PyPI (popcnt≈1453, SIGILL on v1).
# Measured 2026-06 and again 2026-07-28.
# shellcheck disable=SC2086
pip wheel --no-deps --no-binary numpy --no-cache-dir --no-build-isolation "$NUMPY_SPEC" \
  $NUMPY_MESON_PIP_ARGS -w /out

echo "=== GATE: objdump on numpy-core (intermediate) ==="
rm -rf /gate && mkdir -p /gate
python -c "import zipfile,glob; zipfile.ZipFile(sorted(glob.glob('/out/numpy-*.whl'))[0]).extractall('/gate')"
CORE=$(find /gate -name "_multiarray_umath*.so" | head -1)
# grep -c exits 1 when count is 0 → with set -e that kills the script EXACTLY
# when the gate passes. || true is mandatory here.
POPCNT=$(objdump -d "$CORE" | grep -c popcnt || true)
echo "    $(basename "$CORE") = $(stat -c%s "$CORE") bytes | popcnt=$POPCNT"
if [ "$POPCNT" -ne "$GATE_POPCNT_MAX" ]; then
  echo "FAIL GATE: popcnt=$POPCNT (expected $GATE_POPCNT_MAX). -Dcpu-baseline=none did not apply."
  exit 1
fi
echo "OK GATE: numpy-core popcnt=$POPCNT"

pip install --no-cache-dir --no-index --find-links /out numpy

echo "=== [2/4] scipy x86-64-v1 ==="; date
# --no-deps MANDATORY: otherwise pip wheel scipy drops PyPI numpy into /out
# and auditwheel overwrite poisons the published artifact.
# shellcheck disable=SC2086
pip wheel --no-deps --no-binary scipy --no-cache-dir --no-build-isolation "$SCIPY_SPEC" \
  -C setup-args=-Dblas=openblas -C setup-args=-Dlapack=openblas -w /out
pip install --no-cache-dir --no-index --find-links /out scipy

echo "=== [3/4] scikit-learn x86-64-v1 ==="; date
pip wheel --no-deps --no-binary scikit-learn --no-cache-dir --no-build-isolation "$SKLEARN_SPEC" -w /out

echo "=== [4/4] pandas + pure wheels (offline closure) ==="; date
pip download --only-binary :all: --no-deps "$PANDAS_SPEC" -d /out
# shellcheck disable=SC2086
pip download --only-binary :all: --no-deps -d /out $PURE_WHEELS

echo "=== auditwheel repair -> $AUDITWHEEL_PLAT ==="; date
mkdir -p /out/staged /out/repaired
for w in /out/*.whl; do
  case "$w" in
    *linux_x86_64.whl)
      case "$w" in
        *musllinux*|*manylinux*) cp "$w" /out/staged/ ;;
        *) auditwheel repair --plat "$AUDITWHEEL_PLAT" -w /out/staged "$w" ;;
      esac ;;
    *) cp "$w" /out/staged/ ;;
  esac
done

# ─── FINAL GATE — on the artifact that would be published ───
# Cicatriz 2026-07-28: gating the intermediate /out/numpy-*.whl is not enough;
# PyPI numpy can overwrite after scipy. Gate /out/staged only.
echo "=== GATE FINAL: staged numpy + scipy ==="
rm -rf /gate2 && mkdir -p /gate2
python -c "import zipfile,glob; zipfile.ZipFile(sorted(glob.glob('/out/staged/numpy-*.whl'))[0]).extractall('/gate2')"
CORE=$(find /gate2 -name "_multiarray_umath*.so" | head -1)
SZ=$(stat -c%s "$CORE")
PC=$(objdump -d "$CORE" | grep -c popcnt || true)
echo "    staged numpy: $SZ bytes | popcnt=$PC"
if [ "$PC" -ne "$GATE_POPCNT_MAX" ] || [ "$SZ" -gt "$GATE_UMATH_MAX_BYTES" ]; then
  echo "FAIL GATE FINAL: staged numpy looks like PyPI (need popcnt=$GATE_POPCNT_MAX and size <= $GATE_UMATH_MAX_BYTES)."
  exit 1
fi
SW=$(ls /out/staged/scipy-*.whl | head -1)
if python -c "
import zipfile, sys
sys.exit(0 if any('libscipy_openblas' in n for n in zipfile.ZipFile(sys.argv[1]).namelist()) else 1)
" "$SW"; then
  echo "FAIL GATE FINAL: staged scipy embeds libscipy_openblas (= PyPI wheel)."
  exit 1
fi
echo "OK GATE FINAL: numpy $SZ B popcnt=0 · scipy without libscipy_openblas"

# Publish only after gates; import-test must not own the artifact (cicatriz).
SAFE="/out/repaired/.staging/$(python -c 'import sys;print("%d%d"%sys.version_info[:2])')"
mkdir -p "$SAFE" && cp /out/staged/*.whl "$SAFE"/

echo "=== import-test (offline, staged) ==="
pip install --no-cache-dir --no-index --find-links /out/staged --force-reinstall \
  numpy scipy scikit-learn pandas
python -c "import numpy,scipy,sklearn,pandas; print('CONTAINER OK', numpy.__version__, scipy.__version__, sklearn.__version__, pandas.__version__)"

cp /out/staged/*.whl /out/repaired/
echo "MUSL_${PYV}_DONE"
