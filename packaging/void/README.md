# Native packages (xbps / Void) — channel (a) Enterprise / air-gapped

**Decision:** [ADR-0084](../../docs/adr/ADR-0084-native-package-embedded-cpython-by-channel.md) (Accepted).

**Issue:** [#1404](https://github.com/DataBoar/data-boar/issues/1404). nfpm does **not** emit xbps — this overlay is a `void-packages` `template` consumed by `xbps-src`.

Operator runbook: [docs/ops/VOID_XBPS_PACKAGING.md](../../docs/ops/VOID_XBPS_PACKAGING.md) ([pt-BR](../../docs/ops/VOID_XBPS_PACKAGING.pt_BR.md)).

## What this directory is

| Artifact | Role |
| -------- | ---- |
| `files/data-boar/run` | Canonical **runit** service (`/etc/sv/data-boar/run`) — systemd-coupling canary |
| `generated/srcpkgs/data-boar/template` | **Generated** void-packages template — do not hand-edit |
| `generated/srcpkgs/SUBPACKAGE_LINKS.txt` | Subpackage names; the validate script creates `srcpkgs/<name> → data-boar` |
| `generated/PACKAGES.meta.json` | Sidecar inventory (packager, extras, embed) |

Connector names reuse [../nfpm/native_subpackages.toml](../nfpm/native_subpackages.toml). Dependency *lists* come from `EXTRAS_MANIFEST`, never a hand list.

**Home of the template:** this product repo. Upstream merge into [void-linux/void-packages](https://github.com/void-linux/void-packages) is **out of scope** for #1404.

## Regenerate

```bash
uv run python scripts/generate_void_xbps_packages.py --write
uv run python scripts/generate_void_xbps_packages.py --check
```

## Validate (Podman Void — not lab metal)

```bash
# Template parse (glibc image, then musl image):
bash scripts/void-xbps-podman-validate.sh --show
bash scripts/void-xbps-podman-validate.sh --show --libc musl

# Full ./xbps-src pkg (needs populated glibc staging — same tree as nfpm):
bash scripts/native-nfpm-populate-staging.sh
bash scripts/void-xbps-podman-validate.sh --build
```

musl `--build` needs a **musl** staging tree. Do not install the glibc embed onto musl.

## Layers (same as nfpm)

1. Vendored + pinned `cp314t` + wheelhouse (#1182) under `/usr/lib/data-boar`.
2. Distro `depends=` — `openssl zlib libffi tesseract-ocr` (no `python3`, no `p7zip*`).
3. Connector subpackages generated from `EXTRAS_MANIFEST`.

Presence of freethreaded CPython **does not** unlock Enterprise (worker caps + `pro_prefilter_accel`).
