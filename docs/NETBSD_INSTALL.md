# NetBSD 11.1 Installation Recipe

**Português (Brasil):** [NETBSD_INSTALL.pt_BR.md](NETBSD_INSTALL.pt_BR.md)

## Summary

Validated installation of Data Boar 1.8.0 on NetBSD 11.1 amd64. This recipe documents the proven steps for installing Data Boar on NetBSD systems using the pkgsrc package manager.

## Installation

NetBSD uses the `pkgsrc` binary package system via `pkgin`. The key steps are:

```bash
# Install Data Boar dependencies via pkgin
pkgin install py312-numpy py312-scipy py312-pandas py312-cmake py312-ninja

# Alternative: use pkgsrc from source if binary packages are unavailable
# cd /usr/pkgsrc/devel/ninja && make install

# Install Data Boar via pip in a virtual environment with system packages enabled
python -m venv --system-site-packages ~/databoar-venv
pip install data-boar
```

## Verified Results

- **pkgin** binary package repository: `.../packages/NetBSD/amd64/11.1/All`
- **CDN note**: `cdn.netbsd.org` returns **503** for packages outside cache; use `ftp.netbsd.org`
- **VM network note**: No IPv6 supported; use `dhcpcd -4` and `ipv6=off` in QEMU
- **Available binary packages**: `py312-numpy/scipy/pandas/scikit-learn(1.8.0)/cryptography`, `rust`, `py312-torch-2.8.0`
- **Unavailable via pkgsrc**: `pymongo`, `py7zr`, `transformers`, `tokenizers`, `safetensors`, `sentence-transformers` (come from PyPI)

## Available Extras via Binary

| Extra/Module | Status | Notes |
|---|---|---|
| `core` | ✅ Works | Base installation |
| `--demo` | ✅ Works | Demo mode |
| `compressed` | ✅ Works | Via pkg installation |
| `nosql` | ✅ Works | Via pkg installation |
| `dataformats` | ✅ Works | Via pkg installation |
| `dl` | ❌ Not available | Requires PyPI packages (safetensors, sentence-transformers etc.) |

## Installation Trap (IPv6)

VM without IPv6 (operator's network discards it): QEMU `ipv6=off` + `dhcpcd -4`. Always test with IPv4 only.

## Missing Package Workaround

For packages unavailable via pkgsrc, install from PyPI inside the venv with `--system-site-packages`. Example:

```bash
pip install py7zr sentence-transformers
```

Note: Some packages may fail to build without compilers/Rust toolchain available in the VM.