# FreeBSD 15.1 Installation Recipe

**Português (Brasil):** [FREEBSD_INSTALL.pt_BR.md](FREEBSD_INSTALL.pt_BR.md)

## Summary

Validated installation of Data Boar 1.8.0 on FreeBSD 15.1 amd64 in a KVM VM (4 vCPU, 5 GB RAM). This recipe documents the proven steps for installing Data Boar on FreeBSD systems.

## Installation

The key step is installing native packages **before** attempting pip installation:

```bash
# Install required system packages first
pkg install cmake ninja

# Then install Data Boar via pip in a virtual environment with system packages enabled
python -m venv --system-site-packages ~/databoar-venv
pip install data-boar
```

## Verified Results

- **52 of 67 dependencies** resolved via `pkg` (FreeBSD package manager)
- **Outside pin range**: `pandas>=3.0.3`, `starlette==1.9.0`, `fastapi>=0.143` and others
- **3 wheels generated**: `freebsd_15_1_release_p6_amd64` with SHA256 checksums
- **Total build time**: ~1h30m for sdist compilation

## Known Issues & Workarounds

| Extra/Module | Status | Notes |
|---|---|---|
| `compressed` | ✅ Works | Via pkg installation |
| `nosql` | ✅ Works | Via pkg installation |
| `dataformats` | ✅ Works | Via pkg installation |
| `shares` | ✅ Works | Via pkg installation |
| `dl` (torch) | ✅ Works | Via pkg (py312-torch) |
| `py312-py7zr` | ❌ Fails | pkg version 0.22.0 reprova 7 testes; use pip 1.1.4 |
| `grpcio` | ✅ Works | Use py312-grpcio from pkg |
| `pymssql` | ⚠ Compile only | Requires FreeTDS library |

## Rust Pre-filter Benchmark

Isolated Rust pre-filter benchmark on FreeBSD VM (200k lines, 2 warmup + 5 measurements):

- **8.59× speedup** vs Python-only baseline
- `host_profile: freebsd-amd64`, KVM `-cpu host`
- Profile `official_pro_v1` shows 0.574× (Pro slower)
- Currently pin artifact as `linux-x86_64` (4.69×); pending re-pin with `freebsd-amd64` profile

## IPv6/CDN Trap (VM testing)

When testing in VM with IPv6-filtered network:

- `cdn.netbsd.org` returns **503** for cached packages off-cache
- Use `ftp.netbsd.org` instead
- Network drops IPv6 silently; use `dhcpcd -4` and `ipv6=off`

## Performance Note

Published numbers should carry the freebsd-amd64 profile disclaimer: single host, new profile, pin artifact after commit fix and profile application.