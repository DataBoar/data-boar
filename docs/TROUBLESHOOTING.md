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

This decision is tracked at GitHub issue [#671](https://github.com/FabioLeitao/data-boar/issues/671). No ADR is required — this is a won't-fix scope boundary, not an architectural trade-off.

---

## Docker: connecting to remote data from the container

Many deployments use the **Docker image**. The container must be able to reach your databases, file shares (NFS/SMB), and APIs.

- **Remote databases:** Use the **host IP or FQDN** of the DB server in config (not `localhost` unless the DB runs in the same container). From the host, test with `psql`, `mysql`, or similar; from the container, ensure the container network can reach that host (no extra host networking required unless you use `host.docker.internal` or similar).
- **NFS / SMB from container:** Two common approaches: (1) **Mount the share on the host** and bind-mount that path into the container (e.g. `-v /mnt/nfs-share:/data/shares`), then point a **filesystem** target at `/data/shares`; (2) **Use NFS/SMB targets** in config and ensure the container network can reach the NFS/SMB server (install `.[shares]` in the image, open firewall for NFS/SMB ports). For step-by-step and pitfalls, see [TROUBLESHOOTING_DOCKER_DEPLOYMENT.md](ops/TROUBLESHOOTING_DOCKER_DEPLOYMENT.md).
- **DNS:** If config uses hostnames, the container must resolve them (same DNS as host or `--dns`). See [TROUBLESHOOTING_DOCKER_DEPLOYMENT.md](ops/TROUBLESHOOTING_DOCKER_DEPLOYMENT.md).

---

## PyPI/pipx onboarding edge cases (Linux)

On **Debian/Ubuntu** and **Fedora** hosts that already provide **Python >=3.12**, `pipx install data-boar` is usually frictionless.

Two Linux paths currently need one extra step:

### RHEL9-family (AlmaLinux/Rocky/Oracle 9): default `python3` may still be 3.9

When `pipx` resolves to system `python3=3.9`, install can fail with:

- `ERROR: Ignored ... Requires-Python >=3.12`
- `ERROR: No matching distribution found for data-boar`

Use Python 3.12 explicitly:

```bash
sudo dnf install -y python3.12
pipx install --python python3.12 data-boar
```

### Alpine/musl: source-build fallback needs a toolchain

In this path, `scikit-learn` can fall back to source build on musl. Without build tools, `pipx install data-boar` may fail with `metadata-generation-failed`.

Install toolchain prerequisites first:

```bash
apk add build-base gfortran openblas-dev
pipx install data-boar
```

This extra Alpine step is expected to improve once the musllinux no-AVX wheelhouse effort lands ([#929](https://github.com/DataBoar/data-boar/issues/929)).

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
