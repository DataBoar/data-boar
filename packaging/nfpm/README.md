# Native packages (nfpm) — channel (a) Enterprise / air-gapped

**Decision:** [ADR-0084](../../docs/adr/ADR-0084-native-package-embedded-cpython-by-channel.md) (Accepted).

**Plan:** [PLAN_NATIVE_PACKAGES.md](../../docs/plans/PLAN_NATIVE_PACKAGES.md) · Issue [#1403](https://github.com/DataBoar/data-boar/issues/1403).

## What this directory is

Foundation for **deb / rpm / apk / archlinux (pacman)** packages. **xbps** is [#1404](https://github.com/DataBoar/data-boar/issues/1404) — not here.

| Artifact | Role |
| -------- | ---- |
| `native_subpackages.toml` | Package name → pyproject **extra** name (naming contract only) |
| `generated/*.yaml` | **Generated** nfpm configs — do not hand-edit |
| `staging/` | Placeholder tree for contents until CI fills the real embed/wheelhouse |

## Regenerate (required after extras / version / map changes)

```bash
uv run python scripts/generate_nfpm_packages.py --write
```

CI / `tests/test_native_nfpm_foundation.py` fails if `generated/` drifts from the generator + `EXTRAS_MANIFEST`.

## Layers

1. **Vendored + pinned** — core, detection stack, `boar_fast_filter` (abi3) from wheelhouse.
2. **Distro `Depends:`** — libc / OpenSSL / zlib / libffi / tesseract / p7zip via nfpm `overrides` per packager.
3. **Connector subpackages** — generated from `EXTRAS_MANIFEST` extras (`mssql-pymssql`, `nosql`, …).

Embedded CPython is **`cp314t`** under `/usr/lib/data-boar/` (no `Depends: python3`). Registered on the native EXTRAS_MANIFEST as `embedded_interpreter`.

## Commercial protection (ADR-0084)

Presence of freethreaded CPython **does not** unlock Enterprise. Runtime gates remain worker caps (#551) and `pro_prefilter_accel`.

## Out of scope here

Real CI `nfpm package` builds, lab metal matrix, xbps.
