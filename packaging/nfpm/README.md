# Native packages (nfpm) — channel (a) Enterprise / air-gapped

**Decision:** [ADR-0084](../../docs/adr/ADR-0084-native-package-embedded-cpython-by-channel.md) (Accepted).

**Plan:** [PLAN_NATIVE_PACKAGES.md](../../docs/plans/PLAN_NATIVE_PACKAGES.md) · Issues [#1403](https://github.com/DataBoar/data-boar/issues/1403) (foundation) · [#1437](https://github.com/DataBoar/data-boar/issues/1437) (CI build) · [#1408](https://github.com/DataBoar/data-boar/issues/1408) (Release assets).

## What this directory is

**deb / rpm / apk / archlinux (pacman)** package definitions. **xbps** is [#1404](https://github.com/DataBoar/data-boar/issues/1404) — overlay under [`../void/`](../void/README.md).

| Artifact | Role |
| -------- | ---- |
| `native_subpackages.toml` | Package name → pyproject **extra** name (naming contract only) |
| `generated/*.yaml` | **Generated** nfpm configs — do not hand-edit |
| `staging/` | Tree for nfpm `contents:` — CI fills real embed/wheelhouse |

## Regenerate (required after extras / version / map changes)

```bash
uv run python scripts/generate_nfpm_packages.py --write
```

CI / `tests/test_native_nfpm_foundation.py` fails if `generated/` drifts from the generator + `EXTRAS_MANIFEST`.

## CI build (x86-64 glibc) — #1437 / #1408

Workflow: [`.github/workflows/native-packages.yml`](../../.github/workflows/native-packages.yml)

Air-gap verify on the product Release: [docs/ops/NATIVE_PACKAGE_RELEASE.md](../../docs/ops/NATIVE_PACKAGE_RELEASE.md).

```bash
# Local (Linux x86-64; downloads cp314t + wheelhouse — fail-closed):
bash scripts/native-nfpm-populate-staging.sh
# Then, with nfpm installed:
cd packaging/nfpm && nfpm package --config generated/data-boar.yaml --packager deb
```

1. `scripts/native-nfpm-populate-staging.sh` embeds `cp314t` under `staging/usr/lib/data-boar/python3.14t`, installs product + requirements, applies hosted wheelhouse tag `wheelhouse-x86-64-v1-2026-07-29` (layer 1 overlay — not free PyPI).
2. `nfpm package` emits **deb + rpm + apk + archlinux (pacman)** for core `data-boar` from the **same glibc** staging tree.
3. Install-smoke jobs: debian bookworm (`.deb`) and Rocky 9 (`.rpm`). apk/pacman filenames follow packager convention; musl/arm64 metal remains later.
4. Artifacts: `native-packages-x86_64-glibc`. On a **`v*`** GitHub Release, `attach-release` uploads the same files + `SHA256SUMS` + `release-manifest.json` `native_packages[]` beside the SBOMs. The hand-built recipe-proof `.deb` is never uploaded.

The real interpreter tree is **not** committed (repo `.gitignore` `lib/` + explicit staging ignore). Placeholders must never ship in the final artifact.

## Layers

1. **Vendored + pinned** — core, detection stack, `boar_fast_filter` (cp314t) from wheelhouse.
2. **Distro `Depends:`** — libc / OpenSSL / zlib / libffi / tesseract via nfpm `overrides` per packager (no `p7zip*` — `.7z` is optional `py7zr` in `[compressed]`).
3. **Connector subpackages** — generated from `EXTRAS_MANIFEST` extras (`mssql-pymssql`, `nosql`, …).

Embedded CPython is **`cp314t`** under `/usr/lib/data-boar/` (no `Depends: python3`). Registered on the native EXTRAS_MANIFEST as `embedded_interpreter`.

## Commercial protection (ADR-0084)

Presence of freethreaded CPython **does not** unlock Enterprise. Runtime gates remain worker caps (#551) and `pro_prefilter_accel`.

## Out of scope here

apk/musl + arm64, pacman metal, five-host matrix, signed repo **index** publish (#1405). xbps lives in [`../void/`](../void/README.md). #1408 attaches the same package files to the product Release; #1405 must not rebuild them.
