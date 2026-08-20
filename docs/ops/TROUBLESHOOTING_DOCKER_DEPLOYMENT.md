# Troubleshooting: Docker deployment and container networking

**Português (Brasil):** [TROUBLESHOOTING_DOCKER_DEPLOYMENT.pt_BR.md](TROUBLESHOOTING_DOCKER_DEPLOYMENT.pt_BR.md)

**See also:** [TROUBLESHOOTING.md](../TROUBLESHOOTING.md) (overview and quick hints).

This document helps when Data Boar runs **inside a Docker or Podman container** and must connect to **remote databases**, **NFS/SMB shares**, or **APIs**. It covers network reachability from the container, DNS, and how to use host-mounted shares vs NFS/SMB targets. Podman-specific hostnames and rootless networking are in **§ 6**. Image **`HEALTHCHECK`** / Compose `healthcheck` (distroless `GET /health` on loopback **8088**) is **§ 7**.

---

## 1. Remote databases from inside the container

**Scenario:** Config has a database target (PostgreSQL, MySQL, etc.) but the scan fails with **unreachable** or connection refused.

### 1.1 Use hostname or IP that the container can resolve and reach

- **Do not** use `localhost` in config for a DB that runs on the **host** or another machine. From inside the container, `localhost` is the container itself.
- Use the **host’s IP** on the Docker bridge (e.g. `172.17.0.1` on default bridge) or the **hostname** of the DB server. On Docker Desktop (Windows/Mac), you can often use **`host.docker.internal`** as the DB host so the container reaches a service on the host.
- **Example:** DB on host, port 5432. Config: `host: host.docker.internal`, `port: 5432` (or use the host’s real IP). Ensure the DB server listens on an address the container can reach (e.g. `0.0.0.0` or the bridge IP), not only `127.0.0.1`.

### 1.2 Checklist

1. From the **host**, test: `psql -h <host> -p 5432 -U <user> -d <db>` (or equivalent). If it fails, fix DB and firewall on the host first.
1. From **inside the container**: the published image is **distroless** (no `/bin/sh`, no `nc`). `docker exec <container> sh -c 'nc -zv …'` **fails** on `fabioleitao/data_boar`. Use a throwaway debug container on the **same network**, or test from the host (`docker inspect`, `docker port`). See **§ 6** and **§ 7**.
1. **DNS:** If config uses a hostname, the container must resolve it. Use the same DNS as the host (`--dns 8.8.8.8` or host’s DNS) or run with `--network host` (Linux) so the container shares the host’s network (and DNS).

### 1.3 Steps to fix

- Set `host` in config to an IP or hostname that the container can reach (`host.docker.internal` for host services on Docker Desktop; or the DB server’s FQDN/IP).
- Ensure the DB server allows connections from the container’s IP (or Docker bridge subnet).
- If resolution fails, fix container DNS (`--dns`) or use IP instead of hostname.

---

## 2. NFS or SMB from the container (two approaches)

**Scenario:** You want to scan files on an NFS or SMB share. Two common patterns:

### 2.1 Approach A: Mount the share on the host, bind-mount into the container (recommended when possible)

- **On the host:** Mount the NFS or SMB share (e.g. `/mnt/nfs-audit` or `C:\Mounts\SMBShare`).
- **Run the container** with a bind mount of that path, e.g. `-v /mnt/nfs-audit:/data/shared`.
- **In config:** Use a **filesystem** target with `path: /data/shared` (and optional `recursive: true`). No NFS/SMB target type needed; the app just reads files under that path.
- **Pros:** No need for NFS/SMB client inside the container; no extra firewall from container to NFS/SMB server. Works the same on Linux and Windows (host has the mount).
- **Cons:** The host must have the share mounted before starting the container; host must have NFS/SMB client tools.

### 2.2 Approach B: NFS/SMB target in config (container talks directly to the share)

- **In config:** Add a target with `type: nfs` or `type: smb` and the appropriate `host`, `path`, `share`, credentials, etc. (see [USAGE.md](../USAGE.md) and [ADDING_CONNECTORS.md](../ADDING_CONNECTORS.md)).
- **Image:** The image must include the optional **shares** extra (NFS/SMB client libraries). The pre-built image may or may not include it; if you get "smbprotocol not installed" or similar, build a custom image with `pip install -e ".[shares]"` (or use the image that documents shares support).
- **Network:** The **container** must be able to reach the NFS server (ports 2049, 111, etc.) or SMB server (445). Open outbound firewall from the container network to those ports; ensure DNS resolution if you use hostnames.
- **Pros:** No host mount; config is self-contained. Good when the container runs in a cluster and can reach the share directly.
- **Cons:** Requires correct container network and firewall; image must include shares support.

### 2.3 What to look for when it fails

- **"Missing host" / "Missing share name":** Fill in `host`, `share` (SMB), and path in config.
- **"unreachable":** Container cannot reach NFS/SMB server. Check firewall (outbound from container to server ports); test with `docker exec <container> nc -zv <server> 445` (SMB) or `2049` (NFS).
- **"smbprotocol not installed" (or NFS client missing):** Install optional dependency and rebuild image; see [TECH_GUIDE.md](../TECH_GUIDE.md) and [USAGE.md](../USAGE.md).
- **"auth_failed":** Wrong credentials for the share; see [TROUBLESHOOTING_CREDENTIALS_AND_AUTH.md](../TROUBLESHOOTING_CREDENTIALS_AND_AUTH.md).

### 2.4 Steps to fix

- **Approach A:** Mount share on host; bind-mount into container; use filesystem target. Verify the path is readable inside the container (`docker exec <container> ls /data/shared`).
- **Approach B:** Ensure image has shares support; open firewall from container to NFS/SMB; fix host/share/path and credentials in config; re-run and check Scan failures sheet and audit log.

---

## 3. DNS from inside the container

- If config uses **hostnames** (DB host, API base_url, NFS/SMB server), the container must resolve them. By default the container may use the host’s DNS or a default gateway DNS.
- **Symptom:** "unreachable" or "name or service not known" with a hostname in Details.
- **Fix:** Run with `--dns <your-dns-ip>` (e.g. `8.8.8.8` or the corporate DNS), or use **IPs** in config instead of hostnames for testing. In Compose/Kubernetes, set `dns` in the service spec.

---

## 4. Volumes and config path

- Config must be available **inside** the container. Typical setup: host dir `./data` with `config.yaml` → mount as `-v "$(pwd)/data:/data"` and set `CONFIG_PATH=/data/config.yaml`.
- **sqlite_path** and **report.output_dir** should be under the mounted volume (e.g. `/data/audit_results.db`, `/data/reports`) so data persists and you can read reports from the host.
- If the app reports "config not found" or wrong targets, check that `CONFIG_PATH` points to the file inside the container and that the mount is correct (`docker exec <container> cat /data/config.yaml`).

---

## 5. Summary table

| Goal                              | Recommended approach                                                                                                                                            | Doc reference   |
| ------                            | ----------------------                                                                                                                                          | --------------- |
| Scan DB on host from container    | Use `host.docker.internal` (or host IP) as DB host; ensure DB listens and firewall allows container.                                                            | § 1             |
| Scan files on NFS/SMB             | A) Mount share on host, bind-mount into container, use filesystem target. B) Use NFS/SMB target in config; image with `.[shares]`; container network to server. | § 2             |
| Container cannot resolve hostname | Set `--dns` or use IP in config.                                                                                                                                | § 3             |
| Config or reports not found       | Mount volume at `/data`; set `CONFIG_PATH=/data/config.yaml`; set sqlite_path and report.output_dir under `/data`.                                              | § 4             |
| Host DB from **Podman**           | Use `host.containers.internal` (not `host.docker.internal`); rootless uses slirp4netns/pasta, not the Docker bridge.                                             | § 6             |
| Container status **unhealthy**    | Probe is `GET http://127.0.0.1:8088/health` inside the container (stdlib `urllib`, JSON exec). Keep the process listening on **8088** in-container.              | § 7             |

---

## 6. Podman differences (rootless and rootful)

If you run Data Boar with **Podman** instead of Docker Engine, most of the guidance above still applies. Run/pull examples: [DEPLOY.md](../deploy/DEPLOY.md) §10 ([pt-BR](../deploy/DEPLOY.pt_BR.md)).

| Topic | Docker | Podman |
| ----- | ------ | ------ |
| Host services from the container | `host.docker.internal` (Docker Desktop; Linux often needs extra host-gateway) | `host.containers.internal` (typical Podman — **do not** assume `host.docker.internal`) |
| Networking | Bridge via `dockerd` | Rootless: **slirp4netns** or **pasta**; rootful: netavark/CNI |
| Port binding below 1024 | Usually needs root | Rootless: raise `net.ipv4.ip_unprivileged_port_start` or use a port ≥ 1024 (Data Boar default **8088** is fine) |
| Volumes | `-v /host/path:/container/path` | Same syntax; rootless often needs `:Z`/`:z` (SELinux) and sometimes `--userns=keep-id` so image UID **65532** can read bind-mounted files |

**Common fix:** A database on the **host** is unreachable from a **rootless** Podman container when config still uses `host.docker.internal`. Set the target `host` to **`host.containers.internal`**, or to an IP the container can route to (host LAN / gateway from `podman inspect` — **not** `localhost`).

The published Data Boar image is **distroless**: there is **no** `/bin/sh` and no `ip`/`nc` inside the container. Do **not** expect `podman exec <name> ip route` or `sh -c 'nc …'` to work on `data_boar`. Debug from the **host** (`podman port`, `podman inspect`) or use a throwaway debug container on the same network.

Lab **completão** / Maestro hosts that run Podman use the same hostname-in-config and volume patterns; substitute `podman` / `podman-compose` for `docker` / `docker compose`.

---

## 7. Image HEALTHCHECK vs “unhealthy” (distroless)

The published image declares a Docker **`HEALTHCHECK`** (`Dockerfile`). Compose repeats the same probe in `deploy/docker-compose.yml` (`healthcheck.test`). Both call **stdlib `urllib`** — **not** `curl`, **not** a shell — because distroless has no `/bin/sh`.

**What the probe does:** `GET http://127.0.0.1:8088/health` from **inside** the container. `GET /health` stays **public** even when `api.require_api_key` is true ([USAGE.md](../USAGE.md)). Mapping a **host** port (`-p 9002:8088`) does **not** change the probe: it still hits **8088 on loopback**.

| Source | Interval | Timeout | Start period | Retries |
| ------ | -------- | ------- | ------------ | ------- |
| Image `HEALTHCHECK` | 30s | 10s (probe HTTP timeout 8s) | 15s | 3 |
| Compose `healthcheck` | 15s | 5s | 20s | 3 |

### Common “unhealthy” causes

1. **CMD is not the dashboard on 8088.** The default `CMD` is `main.py --web --port 8088`. A one-shot CLI override (`--config …` without `--web`), `--check-extras`, or `--port` other than **8088** leaves nothing on the probe URL. Docker still marks the container unhealthy while the CLI process may be doing useful work.
1. **Process not listening yet.** Respect `start-period` / `start_period`. A slow bind-mount or first-run SQLite create can miss the first probes.
1. **You expected `docker exec … curl /health`.** That binary is **not** in the image. From the host: `curl http://127.0.0.1:<published-port>/health` (after port publish). From another container on the same network: curl the **service name** and **8088**.
1. **Shell-form HEALTHCHECK in a custom Dockerfile.** `HEALTHCHECK CMD curl …` fails on distroless. Keep JSON exec form with `/usr/local/bin/python3.14` as in the repo `Dockerfile`.

**How to confirm:** `docker inspect --format '{{.State.Health.Status}}' <name>` (or `podman inspect`). Then `curl` `/health` on the **published** host port. Expected JSON includes `"status"` (typically `"ok"`) — see [DOCKER_SETUP.md](../DOCKER_SETUP.md) and [deploy/DEPLOY.md](../deploy/DEPLOY.md).

---

**Documentation index:** [README.md](../README.md) · [README.pt_BR.md](../README.pt_BR.md). **Overview:** [TROUBLESHOOTING.md](../TROUBLESHOOTING.md). **Deploy:** [deploy/DEPLOY.md](../deploy/DEPLOY.md).
