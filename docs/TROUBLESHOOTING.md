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

**Limitation:** Classic **Word 97-2003 binary** `.doc` (OLE compound file) is **not** a ZIP; mammoth typically cannot open it, so **content sample stays empty** and only the name/path contributes to findings. If you need compliance evidence from those bodies, convert them to `.docx` (or another supported format) upstream, or plan a separate ingestion path — the product does not shell out to LibreOffice (see issue/plan scope for this slice).

---

## Docker: connecting to remote data from the container

Many deployments use the **Docker image**. The container must be able to reach your databases, file shares (NFS/SMB), and APIs.

- **Remote databases:** Use the **host IP or FQDN** of the DB server in config (not `localhost` unless the DB runs in the same container). From the host, test with `psql`, `mysql`, or similar; from the container, ensure the container network can reach that host (no extra host networking required unless you use `host.docker.internal` or similar).
- **NFS / SMB from container:** Two common approaches: (1) **Mount the share on the host** and bind-mount that path into the container (e.g. `-v /mnt/nfs-share:/data/shares`), then point a **filesystem** target at `/data/shares`; (2) **Use NFS/SMB targets** in config and ensure the container network can reach the NFS/SMB server (install `.[shares]` in the image, open firewall for NFS/SMB ports). For step-by-step and pitfalls, see [TROUBLESHOOTING_DOCKER_DEPLOYMENT.md](ops/TROUBLESHOOTING_DOCKER_DEPLOYMENT.md).
- **DNS:** If config uses hostnames, the container must resolve them (same DNS as host or `--dns`). See [TROUBLESHOOTING_DOCKER_DEPLOYMENT.md](ops/TROUBLESHOOTING_DOCKER_DEPLOYMENT.md).

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
