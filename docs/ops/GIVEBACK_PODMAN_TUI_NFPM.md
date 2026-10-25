# Give-back: nfpm packages for `podman-tui` (upstream)

**Português (Brasil):** [GIVEBACK_PODMAN_TUI_NFPM.pt_BR.md](GIVEBACK_PODMAN_TUI_NFPM.pt_BR.md)

**Issue:** [#1424](https://github.com/DataBoar/data-boar/issues/1424) · **Related:** native packages in this repo ([packaging/nfpm/README.md](../../packaging/nfpm/README.md), [#1403](https://github.com/DataBoar/data-boar/issues/1403)).

This is **not** a Data Boar package. `containers/podman-tui` publishes **zip** binaries on GitHub Releases. Distro users still unpack by hand. The same **nfpm** toolchain we use for Data Boar can emit **deb / rpm / apk / archlinux** from the Linux zip **plus** files that live only in the **source tree** (license, man, completions).

## What this repo ships

| Path | Role |
| ---- | ---- |
| [`giveback/podman-tui/nfpm.yaml.example`](giveback/podman-tui/nfpm.yaml.example) | Corrected nfpm config (license + `Maintainer: Nome <email>`) |
| This page | Contribution notes (DCO, do not attach unofficial `.deb` as the product) |

**Do not** attach locally built `.deb` / `.rpm` to a Data Boar Release. Upstream must build and **sign** their own artifacts.

## Defects the unofficial PoC had (do not repeat)

1. **No license file in the package** — zip contains the binary only. Debian Policy wants `/usr/share/doc/podman-tui/copyright` (copy `LICENSE` from the git tree).
2. **`Maintainer: unofficial build`** — invalid. Use `Full Name <email@domain>` (the person or team who will maintain the packaging in upstream).
3. **No man page / shell completions** — add them **if** the upstream tree generates them; do not invent docs.

## Suggested upstream layout

1. Fork [containers/podman-tui](https://github.com/containers/podman-tui).
1. Add `nfpm.yaml` (start from the example here). Stage:

   - `LICENSE` → `/usr/share/doc/podman-tui/copyright`
   - binary from the linux_amd64 zip (or `go build`) → `/usr/bin/podman-tui`
1. Extend `.github/workflows/releaes.yml` (filename is upstream’s) so a release job runs `nfpm package` for `deb`, `rpm`, `apk`, and `archlinux`, then `gh release upload`.
1. Read **DCO / sign-off** for the `containers/` org **before** opening the PR. Commits need `Signed-off-by:`.
1. Paste the PR URL on [#1424](https://github.com/DataBoar/data-boar/issues/1424).

## Lessons for Data Boar nfpm (#1403)

- Always ship **license text** in the package contents, not only `license:` in the YAML metadata.
- `maintainer:` must be a real `Name <email>` pair.
- Release zips are **not** a complete source of docs; pull man/completions from git.

## Verify an official linux zip (example)

Use the checksum file **from that GitHub Release**, not a copied hash from chat:

```bash
# Replace TAG with the release you are packaging (do not invent tags).
gh release download TAG --repo containers/podman-tui --pattern '*linux_amd64.zip*' --pattern '*sha256*'
sha256sum -c sha256sum   # or the filename upstream actually publishes
```
