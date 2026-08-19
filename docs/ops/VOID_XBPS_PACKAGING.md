# Void xbps native packages (#1404)

**Português (Brasil):** [VOID_XBPS_PACKAGING.pt_BR.md](VOID_XBPS_PACKAGING.pt_BR.md)

nfpm does **not** support xbps. The native Enterprise channel (ADR-0084) ships a `void-packages` overlay under [`packaging/void/`](../../packaging/void/README.md). Validation is **Podman Void** (glibc and musl images) — not lab metal.

Upstream submission to `void-packages` is **out of scope** here.

## Install by distro (Void)

After `./xbps-src pkg data-boar` in a void-packages clone that contains this overlay:

```bash
sudo xbps-install --repository=hostdir/binpkgs data-boar
sudo ln -s /etc/sv/data-boar /var/service/data-boar
```

The service is **runit** (`/etc/sv/data-boar/run`). It execs the embedded `cp314t` with `--web` via **`chpst -u databoar`** (xbps `system_accounts`, not root). The product does **not** call `systemctl`. An optional systemd unit lives at `packaging/init/data-boar.service` (`DynamicUser=yes`) for other packagers and is not required.

Layer 2 distro packages: `openssl zlib libffi tesseract-ocr`. No `Depends: python3`.

Connector extras (`data-boar-mssql`, …) match the nfpm map and `EXTRAS_MANIFEST`.

## Build overlay (maintainers)

```bash
uv run python scripts/generate_void_xbps_packages.py --write
uv run python scripts/generate_void_xbps_packages.py --check
```

```bash
# Parse only (glibc, then musl):
bash scripts/void-xbps-podman-validate.sh --show
bash scripts/void-xbps-podman-validate.sh --show --libc musl

# Full package (glibc staging from the same populate path as nfpm):
bash scripts/native-nfpm-populate-staging.sh
bash scripts/void-xbps-podman-validate.sh --build
```

musl `--build` needs a musl-populated staging tree. Do **not** reuse glibc embed bytes on musl.

The validator and CI `xbps-src show` jobs install `bash` (shebang), `util-linux` (`getopt` + `runuser`, confirmed with `xbps-query -o /usr/bin/getopt`), and `shadow` (`useradd`), then run `./xbps-src` as a non-root `builder` user — `xbps-src` refuses root.

## Finding parity

Install the `.xbps`, then run the same reference corpus used for deb/rpm/apk install-smoke. Finding count must match. The launcher is the same embed + wheelhouse tree (`/usr/lib/data-boar/.../python3.14t -m data_boar`).

## Commercial clause

Embedded `cp314t` does **not** unlock Enterprise. Gates remain worker caps (#551) and `pro_prefilter_accel`.

See also: [OS_COMPATIBILITY_TESTING_MATRIX.md](OS_COMPATIBILITY_TESTING_MATRIX.md) (Void `pipx` / wheelhouse notes) · [USAGE.md](../USAGE.md) (install + process managers).
