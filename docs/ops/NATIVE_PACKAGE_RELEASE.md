# Native packages on the product GitHub Release (air-gap)

**Português (Brasil):** [NATIVE_PACKAGE_RELEASE.pt_BR.md](NATIVE_PACKAGE_RELEASE.pt_BR.md)

**Issue:** [#1408](https://github.com/DataBoar/data-boar/issues/1408) · **Plan:** `docs/plans/PLAN_NATIVE_PACKAGES.md` · **ADR:** [0084](../adr/ADR-0084-native-package-embedded-cpython-by-channel.md), [0089](../adr/ADR-0089-native-package-signed-repository-hosting-keys-and-community-boundary.md)

This is the **offline / air-gap** path: download the product `.deb` / `.rpm` / `.apk` / `.pkg.tar.zst` **from the same GitHub Release** as the SBOMs. The **signed repository** ([#1405](https://github.com/DataBoar/data-boar/issues/1405)) is the day-to-day install channel and **consumes these same files** — it must not rebuild them.

Layer-1 wheels come from the hosted wheelhouse ([#1182](https://github.com/DataBoar/data-boar/issues/1182)), not free PyPI resolution. The hand-built recipe-proof `.deb` from #1408 is **not** a publishable artifact (unsigned, unreproducible, unaudited layer 1).

Assets appear on a **`v*`** GitHub Release after `native-packages.yml` runs on `release: published`. They are **not** on every historic tag.

`attach-release` and the SBOM upload **never** `--clobber` `release-manifest.json` with an empty stub. If the existing manifest cannot be downloaded, the job **fails** instead of wiping `files[]` or `native_packages[]`. Re-run attach after the SBOM workflow has published the licensing manifest.

## Filename convention (do not rename)

Each packager parses the filename. A hyphen-only `.deb` without arch **breaks** `apt` / `reprepro` / `aptly`.

```text
data-boar_<version>_amd64.deb                 deb
data-boar-<version>-<release>.x86_64.rpm      rpm
data-boar-<version>-r<rel>.apk                apk
data-boar-<version>-<rel>-x86_64.pkg.tar.zst  pacman
```

Current CI payload is **x86-64 glibc** (debian / Rocky smokes). musl / arm64 remain later slices.

## Offline verification

```bash
TAG=v1.8.0   # use the real release tag — do not invent one
mkdir -p ~/data-boar-native && cd ~/data-boar-native
gh release download "$TAG" --repo DataBoar/data-boar \
  --pattern 'data-boar*' --pattern 'SHA256SUMS*' --pattern 'release-manifest.json'

sha256sum -c SHA256SUMS

# When SHA256SUMS.asc is present (packaging key from #1405):
# gpg --verify SHA256SUMS.asc SHA256SUMS

# Confirm the release-manifest lists the same hashes:
python3 -c "import json; print(json.load(open('release-manifest.json'))['native_packages'])"
```

Install one packager (example Debian/Ubuntu):

```bash
sudo apt-get install -y ./data-boar_*_amd64.deb
data-boar --version
```

Post-install checks (same gates as CI smoke):

```bash
test -f /usr/lib/data-boar/python3.14t/lib/python3.14t/EXTERNALLY-MANAGED
python3.14t -c 'import sys; assert sys._is_gil_enabled() is False'
# or:
/usr/lib/data-boar/python3.14t/bin/python3.14t -c \
  'import sys, sqlalchemy; assert sys._is_gil_enabled() is False'
```

`DISABLE_SQLALCHEMY_CEXT=1` is set by the `/usr/bin/data-boar` wrapper. Do **not** `pip install` into `/usr/lib/data-boar/python3.14t` — PEP 668 blocks that on purpose.

Layer 1 (numpy / scipy / scikit-learn / pandas / `boar_fast_filter`) is **force-reinstalled from the hosted wheelhouse** (`apply_wheelhouse_v1.sh --no-index`). That is the #1182 contract — not free PyPI resolution.

## SHA256SUMS signature

`SHA256SUMS` is always attached. Detached `SHA256SUMS.asc` is written only when the repository secret `NATIVE_PACKAGE_GPG_PRIVATE_KEY` is present (packaging key ceremony on [#1405](https://github.com/DataBoar/data-boar/issues/1405) / ADR-0089). The pipeline does **not** invent a signature. Package bytes stay the same before and after the key lands.

## Same files for the signed repo

`#1405` / ADR-0089 indexes **these** Release assets. Copy or fetch them; do not `nfpm package` again for the public repo. Parity is hash equality (`SHA256SUMS` ↔ `release-manifest.json` `native_packages[]` ↔ apt/dnf/apk/pacman index).

## Related

- [packaging/nfpm/README.md](../../packaging/nfpm/README.md) — generator + local build
- [RELEASE_INTEGRITY.md](../RELEASE_INTEGRITY.md) — SBOM + licensing `files[]` (distinct from `native_packages[]`)
- [INTEGRITY_HUB.md](INTEGRITY_HUB.md)
