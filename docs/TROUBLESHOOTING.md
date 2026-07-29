# Troubleshooting Data Boar

**Português (Brasil):** [TROUBLESHOOTING.pt_BR.md](TROUBLESHOOTING.pt_BR.md)

This page gives **short hints** for common problems. For **root-cause analysis and step-by-step fixes**, use the linked deep-dive docs. Operators (including consultants and customers who license the app) can use this to resolve connectivity, credential, and deployment issues before the next scan.

---

## Where to see what went wrong

- **Excel report — "Scan failures" sheet:** Each failed target has **Target**, **Reason** (e.g. `unreachable`, `auth_failed`, `timeout`), **Details** (exception message), and **Suggested next step** (a short hint from the application). Start here after a run.
- **Dashboard:** The "Scan failures" count and recent sessions; download the report for the session to open the Scan failures sheet.
- **Audit log:** `audit_YYYYMMDD.log` (path in config or under report output). Download via **Reports → session → Download log** or API `GET /logs/{session_id}`. Contains connection and failure entries with target name and error text.
- **API responses:** `POST /scan` returns 409 if a scan is already in progress; 429 if rate limits are exceeded. Session/report endpoints return 404 with a clear message when the session or report is missing.

The application maps failure **reasons** to a **Suggested next step** in the report (e.g. "Target did not respond. Check network connectivity…"). If that is not enough, use the deep-dive docs below.

---

## Quick hints by failure reason

| Reason (in report)                          | What to check first                                                                                                                                                         | Deep-dive doc                                                                                            |
| --------------------                        | ---------------------                                                                                                                                                       | ----------------                                                                                         |
| **unreachable**                             | Network from audit host/container to target: DNS, routing, firewall, VPN. For Docker: see [TROUBLESHOOTING_DOCKER_DEPLOYMENT.md](ops/TROUBLESHOOTING_DOCKER_DEPLOYMENT.md). | [Connectivity](TROUBLESHOOTING_CONNECTIVITY.md) · [Docker](ops/TROUBLESHOOTING_DOCKER_DEPLOYMENT.md)     |
| **auth_failed** / **authentication_failed** | Credentials (user/pass, token, OAuth client_id/secret). Avoid sending the same credential in both header and body.                                                          | [Credentials and auth](TROUBLESHOOTING_CREDENTIALS_AND_AUTH.md)                                          |
| **permission_denied**                       | Scanner needs read access to the resource (share path, DB, API). Run as a user/service account that has access, or adjust permissions.                                      | [Connectivity](TROUBLESHOOTING_CONNECTIVITY.md)                                                          |
| **timeout**                                 | Target slow or unreachable; timeout value too low. Increase timeout in config (per target or global); retry during off-peak.                                                | [Connectivity](TROUBLESHOOTING_CONNECTIVITY.md)                                                          |
| **error** (generic)                         | See **Details** in the report. Often config (missing host, port, URL) or missing optional dependency (e.g. `.[shares]` for SMB).                                            | [Connectivity](TROUBLESHOOTING_CONNECTIVITY.md) · [Credentials](TROUBLESHOOTING_CREDENTIALS_AND_AUTH.md) |

---

## Legacy `.doc` files: filename vs body text

Filesystem scans always use **path and filename**. **Body text** for the `.doc` extension uses the optional **`mammoth`** library (install the **`legacy-doc`** extra: `pip install -e ".[legacy-doc]"` or `uv sync --extra legacy-doc`).

**What you get:** Mammoth reads **Office Open XML packaged as a ZIP** (the same container family as `.docx`). That covers some real-world `.doc` files that are actually OOXML, or were renamed.

**Limitation:** Classic **Word 97-2003 binary** `.doc` (OLE compound file) is **not** a ZIP; mammoth typically cannot open it, so **content sample stays empty** and only the name/path contributes to findings.

### `.doc` OLE/CFBF native body extraction — won't-fix decision

Data Boar **will not** implement native body extraction for OLE2/CFBF (Compound File Binary Format) `.doc` files via LibreOffice shell-out or a similar heavyweight converter. This is an **explicit, permanent scope decision**, not a temporary gap.

**Rationale:**

| Concern | Detail |
| ------- | ------ |
| **Dependency weight** | LibreOffice installs ~400 MB of binaries and fonts into the scan environment; unacceptable for a lightweight data-scanning container. |
| **Attack surface / RCE vectors** | Shelling out to an office suite to parse untrusted binary documents is a well-known RCE risk class. Parsing malformed OLE binaries with LibreOffice exposes the host to its full vulnerability surface. |
| **Memory and isolation** | LibreOffice is not designed for high-concurrency headless invocations; process leaks and OOM crashes have been observed in production scanning environments. |
| **Format prevalence** | Classic Word 97-2003 binary `.doc` files represent a shrinking fraction of enterprise corpora; most modern document management systems already normalize to `.docx` or PDF on ingestion. |

**What to do instead:**

- **Convert upstream:** Run `libreoffice --headless --convert-to docx your.doc` (or a managed document-conversion service) on the files **before** scanning. Data Boar then reads the resulting `.docx` natively.
- **Use `.docx` output from your DMS:** Configure your Document Management System to export in `.docx`/PDF when feeding Data Boar.
- **Filename path already scanned:** Even without body content, Data Boar still flags the file via its path and filename if PII is present there (e.g. `CPF_000000000-00_contract.doc`).

This decision is tracked at GitHub issue [#671](https://github.com/DataBoar/data-boar/issues/671). No ADR is required — this is a won't-fix scope boundary, not an architectural trade-off.

---

## Docker: connecting to remote data from the container

Many deployments use the **Docker image**. The container must be able to reach your databases, file shares (NFS/SMB), and APIs.

- **Remote databases:** Use the **host IP or FQDN** of the DB server in config (not `localhost` unless the DB runs in the same container). From the host, test with `psql`, `mysql`, or similar; from the container, ensure the container network can reach that host (no extra host networking required unless you use `host.docker.internal` or similar).
- **NFS / SMB from container:** Two common approaches: (1) **Mount the share on the host** and bind-mount that path into the container (e.g. `-v /mnt/nfs-share:/data/shares`), then point a **filesystem** target at `/data/shares`; (2) **Use NFS/SMB targets** in config and ensure the container network can reach the NFS/SMB server (install `.[shares]` in the image, open firewall for NFS/SMB ports). For step-by-step and pitfalls, see [TROUBLESHOOTING_DOCKER_DEPLOYMENT.md](ops/TROUBLESHOOTING_DOCKER_DEPLOYMENT.md).
- **DNS:** If config uses hostnames, the container must resolve them (same DNS as host or `--dns`). See [TROUBLESHOOTING_DOCKER_DEPLOYMENT.md](ops/TROUBLESHOOTING_DOCKER_DEPLOYMENT.md).

---

## PyPI/pipx onboarding edge cases (Linux)

On **Debian/Ubuntu**, **Fedora**, and **RHEL/Alma/Rocky/Oracle 10**, the default `pipx install data-boar` path is currently frictionless when the host already resolves Python >=3.12.

For other Linux paths, use the split below (no overclaim):

### RHEL 8 and RHEL 9 (including Alma): force Python 3.12 in `pipx`

These hosts can still resolve default `python3` below the package floor and fail with:

- `ERROR: Ignored ... Requires-Python >=3.12`
- `ERROR: No matching distribution found for data-boar`

Use Python 3.12 explicitly:

```bash
sudo dnf install -y python3.12
pipx install --python python3.12 data-boar
```

### Void-glibc vs Void-musl

- **Void-glibc:** currently passes in the default path (`pipx install data-boar`) because PyPI publishes a compatible `cp314` wheel.
- **Void-musl:** upstream publishes **no** `scikit-learn` musllinux wheel on any CPython tag. Step 1 below still needs a local wheel folder (or a **direct `.whl` URL** — not a GitHub release page). Step 2 is required for the ML stack; on **x86-64-v1** CPUs step 2 is also required to replace PyPI numpy (see [x86-64-v1 / wheelhouse install](#x86-64-v1--wheelhouse-install-musl-no-avx-and-min-spec-hosts)).

### Alpine/musl: wheelhouse or build toolchain

In this path, `scikit-learn` can fall back to source build on musl. Without build tools, `pipx install data-boar` may fail with `metadata-generation-failed`.

A local **toolchain build** (`apk add build-base gfortran openblas-dev`) fixes musl gaps but **does not** fix **x86-64-v1** CPUs — PyPI numpy/scipy wheels still SIGILL there. For pre-2011 x86 hardware, use the [wheelhouse path](#x86-64-v1--wheelhouse-install-musl-no-avx-and-min-spec-hosts) instead of assuming a successful compile equals a working binary stack.

If no wheelhouse is available and the CPU is modern, install prerequisites first:

```bash
apk add build-base gfortran openblas-dev
pipx install data-boar
```

See [#929](https://github.com/DataBoar/data-boar/issues/929) and [#1182](https://github.com/DataBoar/data-boar/issues/1182) for wheelhouse evolution.

### x86-64-v1 / wheelhouse install (musl, no-AVX, and min-spec hosts)

Use this when **any** of the following apply:

- **musl** (Alpine, Void-musl) and you need the full ML stack without a local Fortran toolchain.
- **Pre-2011 x86 CPUs** where `import numpy` dies with **`Illegal instruction`** (Intel Core 2 / Celeron / Pentium class — `ssse3` only, no SSE4.2/POPCNT). The floor is **`x86-64-v1`**, not merely “no AVX”: PyPI wheels target **`x86-64-v2`** or higher; environment variables (`NPY_DISABLE_CPU_FEATURES`, `OPENBLAS_CORETYPE`) do **not** help because the crash is in **compiled baseline** code, not runtime dispatch ([#929](https://github.com/DataBoar/data-boar/issues/929)).
- **Air-gapped** or egress-restricted installs that must resolve offline.

**Hosted release (verified):** [wheelhouse-x86-64-v1-2026-07-29](https://github.com/DataBoar/data-boar-site/releases/tag/wheelhouse-x86-64-v1-2026-07-29) on `DataBoar/data-boar-site` — 41 wheels, `SHA256SUMS` attached. Full install/verification prose also ships in the release `README.md` asset.

**`boar_fast_filter` is not on PyPI.** The published `data-boar` wheel is `py3-none-any` with **zero** compiled extensions — every PyPI-only install uses the pure-Python pre-filter fallback. The wheelhouse is today the **only** distribution channel for the Rust accelerator (`cp38-abi3`, one wheel per libc).

#### `--find-links` adds an index; it does not prefer

Filenames match PyPI (`numpy-2.5.1-cp312-cp312-musllinux_1_2_x86_64.whl`, etc.), so pip can still pick the **upstream** wheel on step 1. The install is **two forced steps** after download (plus accelerator inject):

- `--find-links` accepts a **local directory**, a **direct URL to a `.whl`**, or an **HTML page of links** — **not** a GitHub **release** page. With ~40 wheels, download to a folder first.

```bash
TAG=wheelhouse-x86-64-v1-2026-07-29
mkdir -p ~/wheelhouse-v1
gh release download "$TAG" --repo DataBoar/data-boar-site \
  --pattern '*musllinux*' --pattern '*-none-any.whl' --dir ~/wheelhouse-v1
# glibc hosts: swap *musllinux* for *manylinux*
# without gh: download the same assets from the release page (browser or curl -LO)

# tmpfs trap — see below before any pip step that may compile
export TMPDIR="${TMPDIR:-/var/tmp/data-boar-build}"
mkdir -p "$TMPDIR"

pipx install data-boar --pip-args="--find-links $HOME/wheelhouse-v1"
pipx runpip data-boar install --no-index --find-links $HOME/wheelhouse-v1 \
  --force-reinstall numpy scipy scikit-learn pandas
pipx inject data-boar boar_fast_filter --pip-args="--no-index --find-links $HOME/wheelhouse-v1"
```

**Single-wheel `--find-links`** (one missing musllinux cell only) can unblock step 1 but does **not** replace PyPI numpy on v1 CPUs — you still need the offline `--force-reinstall` step.

#### `TMPDIR` on tmpfs (min-spec hosts)

If install fails with `[Errno 28] No space left on device` while root disk has free space, check whether `/tmp` is a small **tmpfs** (default: half of RAM). A `scikit-learn` source build may not fit even on hosts with hundreds of GB on disk. Point pip scratch space at real storage **before** step 1:

```bash
export TMPDIR=/var/tmp/data-boar-build && mkdir -p "$TMPDIR"
```

**Interaction with `--demo`:** demo report output goes to **`$TMPDIR/data_boar_demo`**. If you set `TMPDIR` for install, look for the report there — not only under `/tmp`.

#### Verify the swap worked

```bash
python -c "from core import detector; print(detector._ML_AVAILABLE)"   # must print True
python -c "
import glob, os, numpy
so = glob.glob(os.path.join(numpy.__path__[0], '_core', '_multiarray_umath*.so'))[0]
print(os.path.getsize(so), 'bytes')
"
# this wheelhouse: ~5–5.3 MB; PyPI numpy on same tag: ~10.8 MB (SIGILL on v1)
objdump -d "$(python -c 'import glob,os,numpy;print(glob.glob(os.path.join(numpy.__path__[0],"_core","_multiarray_umath*.so"))[0])')" \
  | grep -c popcnt   # must print 0
```

**Field parity (1.7.4.post10, `--demo`):** **26 findings**, `_ML_AVAILABLE=True` — same count as Debian/Fedora/Alma glibc paths when the harness waits for the report (see matrix doc). On metal: Intel Celeron 900, Alpine/musl, offline wheelhouse path.

#### `--demo` automation traps

- **`data-boar --demo` does not exit** after the scan — it starts the API on **`127.0.0.1:8088`** and stays in **LISTEN**. Wait for the **report** under `$TMPDIR/data_boar_demo`, not for the process to return.
- If you changed `TMPDIR` for install (tmpfs workaround), the demo report follows **`$TMPDIR`** — do not search only `/tmp/data_boar_demo`.

### no-AVX hosts (pointer)

Do not assume a smooth default PyPI path. Use the [x86-64-v1 wheelhouse install](#x86-64-v1--wheelhouse-install-musl-no-avx-and-min-spec-hosts) or Docker.

### RHEL 7 / CentOS 7 (EOL)

Treat native `pipx` install as unsupported for current builds (EOL repositories and unreachable Python floor). Use Docker.

---

## Is Data Boar helpful for your organization?

- **With a trained consultant:** A consultant can install, configure, and tune Data Boar in your network; set credentials and targets; run scans and interpret reports. This is the lowest-risk way to get value when IT/compliance/DPO maturity is still growing.
- **License only (self-service):** You can run the app yourself: follow [TECH_GUIDE](TECH_GUIDE.md), [USAGE](USAGE.md), and [deploy/DEPLOY](deploy/DEPLOY.md). Use this troubleshooting guide and the deep-dive docs when you hit connectivity or credential issues. For complex environments (many sources, strict firewall, SSO/OAuth), consultant support is still recommended.
- **Docker:** Most deployments use the container; connecting to remote DBs and to NFS/SMB is documented in the deploy and troubleshooting docs above.

---

## Deep-dive documentation (root cause and fix steps)

| Topic                    | Description                                                                          | English                                                                            | Português (pt-BR)                                                                              |
| -------                  | -------------                                                                        | ---------                                                                          | -------------------                                                                            |
| **Connectivity**         | Network, DNS, firewall, timeouts; DB/API/share unreachable; permission_denied        | [TROUBLESHOOTING_CONNECTIVITY.md](TROUBLESHOOTING_CONNECTIVITY.md)                 | [TROUBLESHOOTING_CONNECTIVITY.pt_BR.md](TROUBLESHOOTING_CONNECTIVITY.pt_BR.md)                 |
| **Credentials and auth** | API key in header vs body; Basic/Bearer/OAuth; conflicting credentials; lockouts     | [TROUBLESHOOTING_CREDENTIALS_AND_AUTH.md](TROUBLESHOOTING_CREDENTIALS_AND_AUTH.md) | [TROUBLESHOOTING_CREDENTIALS_AND_AUTH.pt_BR.md](TROUBLESHOOTING_CREDENTIALS_AND_AUTH.pt_BR.md) |
| **Docker deployment**    | Running in container; NFS/SMB from container; remote DB from container; DNS; volumes | [TROUBLESHOOTING_DOCKER_DEPLOYMENT.md](ops/TROUBLESHOOTING_DOCKER_DEPLOYMENT.md)   | [TROUBLESHOOTING_DOCKER_DEPLOYMENT.pt_BR.md](ops/TROUBLESHOOTING_DOCKER_DEPLOYMENT.pt_BR.md)   |

**Documentation index:** [README.md](README.md) · [README.pt_BR.md](README.pt_BR.md).
