# Optional Extras in Native Packages

**Português (Brasil):** [PACKAGING_EXTRAS.pt_BR.md](PACKAGING_EXTRAS.pt_BR.md)

## Summary

Documentation of the supported recipe for optional extras when installing Data Boar via native packages (.rpm, .deb, .apk, .pkg.tar.zst). The native package contains only the core Python embedding; optional extras require a venv with `--system-site-packages` over the embedded Python.

## Supported Recipe

The documented approach is to create a venv over the embedded Python and install extras there:

```bash
# Create venv with system site packages over the embedded Python
python3 -m venv --system-site-packages ~/databoar-xvenv

# Activate the venv
source ~/databoar-xvenv/bin/activate

# Install Data Boar extras with documented status
pip install "data-boar[nosql]"       # installs pymongo, redis
pip install "data-boar[dataformats]" # installs pyarrow, fastavro, dbfread
pip install "data-boar[compressed]"  # may fail: brotli build dependency
pip install "data-boar[dl]"          # may fail: safetensors, Rust build

# Run Data Boar from the venv
data-boar scan
```

## Extra × Status Table (Evidence from AlmaLinux 9.8, data-boar-1.8.0.x86_64.rpm)

| Extra | Result in venv | System Dependencies |
|---|---|---|
| `nosql` (pymongo 4.19.0, redis 8.1.0) | ✅ Installs and imports | — |
| `dataformats` (pyarrow 26.0.1, fastavro 1.13.1, dbfread 2.0.7) | ✅ Installs and imports | — |
| `mssql` (pymssql 2.3.13) | ✅ Installs, ❌ import fails | `libsybdb.so.5` (FreeTDS library; dnf/EPEL not tested) |
| `compressed` (py7zr) | ❌ Fails | `brotli` fails in source build (no cp314t wheel; no gcc/cmake in VM) |
| `dl` (sentence-transformers) | ❌ Fails | `safetensors` fails in source build (no Rust in VM) |

**Not tested**: `richmedia`, `shares`, `detection-fuzzy`, `bigdata`

## System Dependencies by Extra

| Extra | System Dependency | Install Method |
|---|---|---|
| `mssql` | FreeTDS (`libsybdb.so.5`) | dnf/EPEL or source compile |
| `compressed` | brotli development | gcc/cmake for source build, or prebuilt wheel |
| `dl` | Rust toolchain | `dnf install rust` or build from source |

## Format Coverage

Currently documented and tested on: **AlmaLinux 9.8 (RPM format)**

Not yet tested: `.deb` (Debian/Ubuntu), `.apk` (Alpine), `.pkg.tar.zst` (Arch)

**Decision required** (see PLAN_PACKAGING_EXTRAS.md): Publish subpackages as release assets, maintain venv-only recipe, or both. Strategy for `compressed` and `dl` extras (cp314t wheels or document compiler prerequisite).

## Running Scans from the Venv

To confirm a scan uses the venv modules (not just import works):

```bash
# Activate venv
source ~/databoar-xvenv/bin/activate

# Verify modules are importable
python -c "import pymongo; import pyarrow; import py7zr"  # check each extra

# Run Data Boar scan
data-boar scan -- --demo
```

Record the exact command used and verify the scan picks up the extra modules.