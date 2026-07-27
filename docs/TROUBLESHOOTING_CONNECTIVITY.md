# Troubleshooting: Connectivity and timeouts

**Português (Brasil):** [TROUBLESHOOTING_CONNECTIVITY.pt_BR.md](TROUBLESHOOTING_CONNECTIVITY.pt_BR.md)

**See also:** [TROUBLESHOOTING.md](TROUBLESHOOTING.md) (overview and quick hints).

This document helps you diagnose and fix **unreachable**, **timeout**, and **permission_denied** failures when scanning databases, APIs, or file shares (including NFS/SMB). It applies to both host and Docker deployments; for Docker-specific network and volume setup, see [TROUBLESHOOTING_DOCKER_DEPLOYMENT.md](ops/TROUBLESHOOTING_DOCKER_DEPLOYMENT.md).

---

## 1. What the report and app tell you

- **Scan failures sheet:** Columns **Target**, **Reason**, **Details**, **Suggested next step**. The **Reason** is one of `unreachable`, `auth_failed`, `permission_denied`, `timeout`, or `error`. The **Suggested next step** is generated from that reason; **Details** contains the raw exception message.
- **failure_hint (in code):** The app maps these reasons to short, actionable text (e.g. for `timeout`: "Operation timed out. Check for high latency… Consider increasing timeout values…"). If the hint is not enough, use this doc.

---

## 2. Unreachable (target did not respond)

**What to look for:** Reason `unreachable`; Details often show connection refused, no route to host, or name resolution failure.

### 2.1 Checklist

1. **Reachability from the audit host (or container):** Can you ping or connect from the same machine/container that runs Data Boar? If you run in Docker, test from inside the container (e.g. `docker exec <container> ping <db-host>` or `docker exec <container> nc -zv <host> <port>`).
1. **DNS:** If config uses a hostname, resolve it from the audit host/container: `getent hosts <hostname>` or `nslookup <hostname>`. If it fails, fix DNS or use the target IP in config.
1. **Firewall:** Outbound from audit host/container to target port (e.g. 5432 PostgreSQL, 445 SMB, 443 HTTPS). Inbound on the target server must allow the audit host/container IP (or network).
1. **VPN:** If the target is only reachable over VPN, ensure the VPN is up on the host (or that the container uses host network if the VPN is on the host and you accept that setup).
1. **Wrong host/port/path in config:** Typo in `host`, `port`, `base_url`, or `path`. Compare config to the target’s real address.

### 2.2 Steps to fix

- Fix DNS (use IP or correct DNS server).
- Open firewall for the required port (DB, SMB, NFS, HTTPS) from audit host/container to target.
- Correct `host`, `port`, or URL in config; restart or re-run scan.
- If running in Docker and target is on the host or another container, see [TROUBLESHOOTING_DOCKER_DEPLOYMENT.md](ops/TROUBLESHOOTING_DOCKER_DEPLOYMENT.md) (host networking, `host.docker.internal`, etc.).

---

## 3. Timeout

**What to look for:** Reason `timeout`; Details may show httpx/connection timeout or similar.

### 3.1 Checklist

1. **Target slow or overloaded:** High latency or load on DB/API; try again during off-peak.
1. **Timeout too low in config:** REST/API targets support a `timeout` (seconds). Default is often 30; increase if the target is slow (e.g. `timeout: 60` or 120).
1. **Network latency:** Cross-region or congested path; increase timeout or run the scanner closer to the target.
1. **Large discovery:** Some connectors (e.g. Power BI, Dataverse) do many API calls; total time can exceed a single-request timeout. Increase timeout and/or reduce scope if possible.
1. **Fragile production database under parallel scan:** If the host has little memory or no swap, high `scan.max_workers` can amplify latency or look like DoS. Try `scan.adaptive_rate_limit: true` with a realistic `target_latency_ms` (default 200) so the engine throttles target concurrency from observed latency — see [USAGE.md](USAGE.md) § *Adaptive rate limiting (ARL)*. Fixed `max_workers: 1` remains the manual alternative.

### 3.2 Steps to fix

- In config, set a higher `timeout` for the failing target (see [USAGE.md](USAGE.md) for target schema).
- Re-run during off-peak or from a host/region closer to the target.
- Check the audit log for which operation timed out (e.g. connect vs read); that tells you whether to focus on network or target performance.

---

## 4. Permission denied

**What to look for:** Reason `permission_denied`; Details often "access denied" or "forbidden".

### 4.1 Checklist

1. **Credentials:** Wrong user/password or token; or token expired. See [TROUBLESHOOTING_CREDENTIALS_AND_AUTH.md](TROUBLESHOOTING_CREDENTIALS_AND_AUTH.md).
1. **Read access:** The account used by the scanner must have **read** access to the resource (DB tables/views, share path, API endpoints). No write required.
1. **Filesystem/share path:** On NFS/SMB, the mounted path or share path must be readable by the user running the app (or the container user). Check mount options and share permissions.
1. **API scope:** OAuth or API key may need a scope that includes read for the endpoints you scan.

### 4.2 Steps to fix

- Grant the scanner account read-only access to the target (DB, share, API).
- Fix credentials or token in config; avoid duplicate auth (e.g. same key in header and body). See [TROUBLESHOOTING_CREDENTIALS_AND_AUTH.md](TROUBLESHOOTING_CREDENTIALS_AND_AUTH.md).
- For shares: ensure the path exists and the process (or container user) can list and read files.

---

## 5. Generic "error" (config or dependency)

**What to look for:** Reason `error`; Details vary (missing host, missing URL, "module not found", etc.).

### 5.1 Common causes

- **Missing required field:** e.g. `host`, `port`, `base_url`, `share` (SMB). Add the correct value in config.
- **Optional dependency not installed:** SMB/NFS/WebDAV need `.[shares]`; MongoDB/Redis need `.[nosql]`. Install the extra and rebuild or reinstall (e.g. `uv pip install -e ".[shares]"`). In Docker, use an image that includes those extras or build a custom image.
- **Invalid URL or driver:** Malformed `base_url` or unsupported `driver` for SQL. Check [USAGE.md](USAGE.md) and [TECH_GUIDE.md](TECH_GUIDE.md) for supported drivers and URL format.

### 5.2 Steps to fix

- Read **Details** in the Scan failures sheet; it usually points to the missing or invalid value.
- Install optional extras if the connector requires them; fix config and re-run.

---

**Documentation index:** [README.md](README.md) · [README.pt_BR.md](README.pt_BR.md). **Overview:** [TROUBLESHOOTING.md](TROUBLESHOOTING.md).
