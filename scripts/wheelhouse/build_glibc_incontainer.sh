#!/bin/bash
# build_glibc_incontainer.sh — port of vault build-v1-glibc.sh for CI (#1379).
# Runs INSIDE quay.io/pypa/manylinux_2_28_x86_64. Args: cp312|cp313|cp314
# Pins/gates from env (recipe-manifest.yaml via host).
set -euo pipefail
CPTAG="${1:?usage: build_glibc_incontainer.sh cp312|cp313|cp314}"
: "${NUMPY_SPEC:?}" "${SCIPY_SPEC:?}" "${SKLEARN_SPEC:?}" "${PANDAS_SPEC:?}"
: "${PURE_WHEELS:?}" "${NUMPY_MESON_PIP_ARGS:?}"
: "${GATE_POPCNT_MAX:?}" "${GATE_UMATH_MAX_BYTES:?}"
: "${AUDITWHEEL_PLAT:?}"

PYBIN="/opt/python/${CPTAG}-${CPTAG}/bin/python"
[ -x "$PYBIN" ] || { echo "FATAL: $PYBIN missing"; ls /opt/python; exit 1; }
echo "=== manylinux_2_28 | glibc $(ldd --version | head -1 | awk '{print $NF}') | $($PYBIN -V) ==="
export TMPDIR="${TMPDIR:-/var/tmp/data-boar-build}"
mkdir -p "$TMPDIR" /out

"$PYBIN" -m venv /v && . /v/bin/activate
pip install --no-cache-dir -q Cython meson-python ninja pythran pybind11 setuptools auditwheel
pip uninstall -y scipy-openblas64 scipy-openblas32 >/dev/null 2>&1 || true
dnf -q -y install epel-release >/dev/null 2>&1 || true
dnf -q -y --enablerepo=crb install openblas-devel binutils >/dev/null 2>&1 \
  || dnf -q -y --enablerepo=powertools install openblas-devel binutils >/dev/null 2>&1
rpm -q openblas-devel || { echo "FATAL: no system openblas-devel"; exit 1; }

echo "=== [1/4] numpy x86-64-v1 ==="; date
# shellcheck disable=SC2086
pip wheel --no-deps --no-binary numpy --no-cache-dir --no-build-isolation "$NUMPY_SPEC" \
  $NUMPY_MESON_PIP_ARGS -w /out

echo "=== GATE: objdump on numpy-core ==="
rm -rf /gate && mkdir -p /gate
python -c "import zipfile,glob; zipfile.ZipFile(sorted(glob.glob('/out/numpy-*.whl'))[0]).extractall('/gate')"
CORE=$(find /gate -name "_multiarray_umath*.so" | head -1)
POPCNT=$(objdump -d "$CORE" | grep -c popcnt || true)
echo "    $(basename "$CORE") = $(stat -c%s "$CORE") bytes | popcnt=$POPCNT"
if [ "$POPCNT" -ne "$GATE_POPCNT_MAX" ]; then
  echo "FAIL GATE: popcnt=$POPCNT (expected $GATE_POPCNT_MAX)."
  exit 1
fi
echo "OK GATE: numpy-core popcnt=$POPCNT"

pip install --no-cache-dir --no-index --find-links /out numpy

echo "=== [2/4] scipy ==="; date
# shellcheck disable=SC2086
pip wheel --no-deps --no-binary scipy --no-cache-dir --no-build-isolation "$SCIPY_SPEC" \
  -C setup-args=-Dblas=openblas -C setup-args=-Dlapack=openblas -w /out
pip install --no-cache-dir --no-index --find-links /out scipy

echo "=== [3/4] scikit-learn ==="; date
pip wheel --no-deps --no-binary scikit-learn --no-cache-dir --no-build-isolation "$SKLEARN_SPEC" -w /out

echo "=== [4/4] pandas + pure wheels ==="; date
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

echo "=== GATE FINAL: staged numpy + scipy ==="
rm -rf /gate2 && mkdir -p /gate2
python -c "import zipfile,glob; zipfile.ZipFile(sorted(glob.glob('/out/staged/numpy-*.whl'))[0]).extractall('/gate2')"
CORE=$(find /gate2 -name "_multiarray_umath*.so" | head -1)
SZ=$(stat -c%s "$CORE")
PC=$(objdump -d "$CORE" | grep -c popcnt || true)
echo "    staged numpy: $SZ bytes | popcnt=$PC"
if [ "$PC" -ne "$GATE_POPCNT_MAX" ] || [ "$SZ" -gt "$GATE_UMATH_MAX_BYTES" ]; then
  echo "FAIL GATE FINAL: staged numpy looks like PyPI."
  exit 1
fi
SW=$(ls /out/staged/scipy-*.whl | head -1)
if python -c "
import zipfile, sys
sys.exit(0 if any('libscipy_openblas' in n for n in zipfile.ZipFile(sys.argv[1]).namelist()) else 1)
" "$SW"; then
  echo "FAIL GATE FINAL: staged scipy embeds libscipy_openblas."
  exit 1
fi
echo "OK GATE FINAL: numpy $SZ B popcnt=0 · scipy without libscipy_openblas"

SAFE="/out/repaired/.staging/${CPTAG}"
mkdir -p "$SAFE" && cp /out/staged/*.whl "$SAFE"/
pip install --no-cache-dir --no-index --find-links /out/staged --force-reinstall \
  numpy scipy scikit-learn pandas
python -c "import numpy,scipy,sklearn,pandas; print('CONTAINER OK', numpy.__version__, scipy.__version__)"
cp /out/staged/*.whl /out/repaired/
echo "GLIBC_${CPTAG}_DONE"
