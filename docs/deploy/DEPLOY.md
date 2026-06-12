# Deploy Data Boar (Docker, Compose, Swarm, Kubernetes)

**Português:** [DEPLOY.pt_BR.md](DEPLOY.pt_BR.md)

You can run the application with **plain Docker** (`docker run`), **Docker Compose**, **Docker Swarm**, or **Kubernetes** — choose the option that fits your environment. All options use the same image; default behaviour is web API + frontend on port 8088.

## Default: Web API and frontend

When you run the image **without** overriding the command (e.g. `docker run ... image`, Compose, Swarm, or Kubernetes with no `command`/`args`), the container starts the **web API and frontend**:

- **Dashboard:** `http://<host>:8088/` (status, **Start scan** button, recent sessions, download reports). The **Start scan** button runs a **full audit of all targets** defined in `/data/config.yaml` (same as the CLI one-shot with that config).
- **Reports:** `http://<host>:8088/reports`
- **Configuration:** `http://<host>:8088/config`
- **API docs:** `http://<host>:8088/docs`
- **Health:** `http://<host>:8088/health`

Port **8088** is exposed. Config and persistent data (SQLite, reports) live under **`/data`** (mount a volume or bind mount with `config.yaml`).

## CLI one-shot (override)

To run a **single audit from the CLI** instead of the API, override the container command and pass config (and optional `--tenant` / `--technician`):

```bash
# Bind mount a dir that contains config.yaml at /data
docker run --rm -v "$(pwd)/data:/data" \
  YOUR_IMAGE \
  python main.py --config /data/config.yaml --tenant "Acme" --technician "Ops"
```

Or with `--entrypoint`:

```bash
docker run --rm -v "$(pwd)/data:/data" \
  --entrypoint python \
  YOUR_IMAGE \
  main.py --config /data/config.yaml
```

The report is written under `report.output_dir` in config (e.g. `/data`); copy it out from the volume or bind-mounted dir. Do **not** use `--web` in these overrides.

## Pre-built image on Docker Hub

You can run the application **without cloning the repository** by using the published image on Docker Hub:

- **Docker Hub:** [hub.docker.com/r/fabioleitao/data_boar](https://hub.docker.com/r/fabioleitao/data_boar) — **`fabioleitao/data_boar:latest`** and **`fabioleitao/data_boar:1.7.3`**

Example:

```bash
docker pull fabioleitao/data_boar:latest
docker run -d -p 8088:8088 -v "$(pwd)/data:/data" -e CONFIG_PATH=/data/config.yaml fabioleitao/data_boar:latest
```

Ensure `/data/config.yaml` exists (e.g. copy from `deploy/config.example.yaml` in the repo or create a minimal config). This lets users choose to run an instanced container from Docker Hub instead of building from Git.

**Upgrading when new versions are pushed:** To refresh your local image so it matches the current version on Docker Hub, run `docker pull fabioleitao/data_boar:latest`, then restart your container or stack (e.g. `docker stop`/`docker rm` and `docker run` again, or `docker compose pull` and `docker compose up -d`). Do this whenever you want to pick up the latest image from the repository.

## Image (build from source)

- **Dockerfile** at repo root. Build (Data Boar branding): `docker build -t fabioleitao/data_boar:latest .` or a local tag: `docker build -t data_boar:latest .`
- **Public image**: You can also push to GitHub Container Registry (ghcr.io) or your own Docker Hub account and use that name in Compose/Swarm/Kubernetes.

**Image footprint:** The Dockerfile uses a **multi-stage build** on **`python:3.13-slim`** (see repo `Dockerfile`; aligns with `requires-python >=3.12` and CI on 3.12/3.13). The first stage installs build tools (gcc, dev headers) and compiles Python extensions; the final stage copies only the installed packages and app code and installs **runtime** libraries (e.g. `libpq5`, `libffi8`, `unixodbc`, `libmariadb3`). Build tools and `-dev` packages are not included in the final image, reducing size and attack surface while keeping the same behaviour (all DB connectors, reports, API).

## 1. Build and push image (public repository)

### Option A – GitHub Container Registry (ghcr.io)

```bash
# From repo root (Data Boar image name)
docker build -t ghcr.io/fabioleitao/data_boar:latest .
docker login ghcr.io   # Use a GitHub Personal Access Token with read:packages, write:packages
docker push ghcr.io/fabioleitao/data_boar:latest
```

### Option B – Docker Hub (e.g. fabioleitao)

```bash
# From repo root
docker build -t fabioleitao/data_boar:latest -t fabioleitao/data_boar:1.7.3 .
docker login
# Username: fabioleitao (or your Docker Hub username)
# Password: your Docker Hub password or Access Token
docker push fabioleitao/data_boar:latest
docker push fabioleitao/data_boar:1.7.3
```

Then in `deploy/docker-compose.yml` set `image:` to your pushed image (e.g. `fabioleitao/data_boar:latest` or `ghcr.io/fabioleitao/...`).

**Releasing to Docker Hub (fabioleitao):** From repo root, run the test suite (`uv run pytest -v -W error`), then build, log in with your Docker Hub credentials, and push the branded image:

```bash
uv run pytest -v -W error
docker build -t fabioleitao/data_boar:latest -t fabioleitao/data_boar:1.7.3 .
docker login              # username: fabioleitao, password: your token
docker push fabioleitao/data_boar:latest
docker push fabioleitao/data_boar:1.7.3
```

See also [DOCKER_SETUP.md](../DOCKER_SETUP.md).

## 2. Prepare config

The app expects **config at `/data/config.yaml`** inside the container. Use the same schema as in the repo (see [USAGE.md](../USAGE.md)). Minimum for API-only:

- `targets: []`
- `report.output_dir: /data`
- `sqlite_path: /data/audit_results.db`
- `api.port: 8088`

**Sensitivity detection (ML/DL):** You can configure training terms for pattern and sensitivity detection via `ml_patterns_file`, `dl_patterns_file`, or inline `sensitivity_detection.ml_terms` / `sensitivity_detection.dl_terms` in config. Mount your terms file(s) under `/data` (e.g. `/data/ml_terms.yaml`) and set the paths in config. See [SENSITIVITY_DETECTION.md](../SENSITIVITY_DETECTION.md) and `deploy/config.example.yaml` for examples. The image includes regex + ML (TF-IDF + RandomForest); optional DL (sentence embeddings) requires installing the `.[dl]` extra when building a custom image.

Copy `deploy/config.example.yaml` and edit, then either:

- **Volume**: Create a volume and put `config.yaml` into it before first run, or
- **Bind mount**: Mount a host dir that contains `config.yaml` at `/data`.

Example with bind mount (host dir `./data`):

```bash
mkdir -p data
cp deploy/config.example.yaml data/config.yaml
# Edit data/config.yaml (targets, etc.)
```

### Resource and I/O tuning (production)

In production the main bottlenecks are **network I/O** (database and API targets) and **filesystem I/O** (file scans, SQLite, report generation). The default resource settings balance minimal footprint with enough headroom for these I/O-bound operations.

- **Memory:** Reservations/requests of **256Mi** and limits of **1Gi** are default. Use at least 256Mi so the process does not get OOM-killed; 1Gi allows report generation (Excel, heatmaps) and concurrent scans. Increase limits if you run many parallel targets or large reports.
- **CPU:** A small **request** (e.g. 0.25 in Compose, 100m in Kubernetes) helps the scheduler place the container/pod; **CPU limits are left unset or high** so short CPU bursts (e.g. report generation) are not throttled. The workload is I/O-bound, so CPU is not the bottleneck.
- **api.workers:** Default **1** keeps footprint minimal. Set **2** (or more) in config if you need to serve many concurrent API requests while scans run; each worker is a separate process.
- **scan.max_workers:** Default **1** (sequential targets). Set **2–4** when you have many targets and want parallel scan threads; I/O (DB/FS) remains the bottleneck, so this improves throughput without requiring much more CPU.
- **Storage for /data:** Use **fast storage** (SSD, local NVMe) for the volume that holds SQLite and report output; this reduces write latency and speeds up report generation and dashboard reads.
- **Timeouts:** REST/API connectors use configurable timeouts (see [USAGE.md](../USAGE.md)). Increase them in target config if your network or APIs are slow to avoid false timeouts.

### Security and hardening (optional)

The following are **optional** practices to harden deployments. They do not replace securing the app at the reverse proxy (TLS, auth, WAF). See also [SECURITY.md](../../SECURITY.md).

### Docker

- **Non-root:** The image already runs as user `appuser` (UID 1000). To enforce at runtime: `docker run --user 1000 ...` (or keep the Dockerfile `USER appuser`).
- **Resource limits:** Use `--cpus` and `--memory` for plain Docker (e.g. `--memory 1g`). In Compose, set `deploy.resources.limits` (e.g. `cpus: '1'`, `memory: 1G`).
- **Healthchecks:** The image can be used with Docker `HEALTHCHECK`; for API mode, probe `GET /health`. Compose and Kubernetes examples in this repo already use `/health` for liveness/readiness. For observability, SLO/SLI/SLA, and SRE alignment (runbooks, error budgets, optional metrics), see [OBSERVABILITY_SRE.md](../OBSERVABILITY_SRE.md).
- **DevSecOps:** Combine with API key (`api.require_api_key`), rate limiting (`rate_limit` in config), and CSP/security headers (see [SECURITY.md](../../SECURITY.md)). Run behind a reverse proxy with TLS and, when exposed externally, consider a WAF. **For production, set `api.require_api_key: true` and use a strong key from an environment variable** (e.g. `api.api_key_from_env: "AUDIT_API_KEY"`) so credentials are not stored in the config file.

### Kubernetes (optional examples)

You can tighten the Deployment with a **securityContext** and add a **NetworkPolicy** and **PodDisruptionBudget** for production. The base manifests in `deploy/kubernetes/` do not include these by default; below are optional snippets and example files.

- **Deployment securityContext** (add under `spec.template.spec` in your Deployment):

```yaml
      securityContext:
        runAsNonRoot: true
        runAsUser: 1000
        seccompProfile:
          type: RuntimeDefault
      containers:

        - name: data-boar

          securityContext:
            allowPrivilegeEscalation: false
            readOnlyRootFilesystem: true
            capabilities:
              drop:

                - ALL

          # ... rest of container spec; ensure /data is a writable volumeMount so the app can write SQLite and reports
```

The image runs as UID 1000 (`appuser`). Use a writable volume for `/data` (e.g. PVC or emptyDir) so SQLite and report output work with `readOnlyRootFilesystem: true`.

- **NetworkPolicy:** To restrict ingress to the API (e.g. only from an ingress controller or a specific namespace), use an example like `deploy/kubernetes/network-policy.example.yaml`. Apply it only if your cluster supports NetworkPolicy.

- **PodDisruptionBudget (PDB):** When running multiple replicas, a PDB can ensure at least one replica remains during voluntary disruptions. See `deploy/kubernetes/pdb.example.yaml`. Apply only if you run more than one replica.

- **Resource requests/limits:** The default Deployment already sets memory request/limit and CPU request; see "Resource and I/O tuning" above for guidance.

## 3. Run as a single container (docker run)

```bash
# From repo root; image built locally (Data Boar)
docker build -t data_boar:latest .

# Run with a bind mount for /data (config.yaml must be in ./data)
mkdir -p data
cp deploy/config.example.yaml data/config.yaml
# Edit data/config.yaml as needed

docker run -d --name data-boar-audit \
  -p 8088:8088 \
  -v "$(pwd)/data:/data" \
  -e CONFIG_PATH=/data/config.yaml \
  data_boar:latest
```

Access: <http://localhost:8088/> (dashboard), <http://localhost:8088/docs> (API). In Docker and Kubernetes examples, the service is exposed via container/Service port bindings, so it is safe to keep the internal API binding on `0.0.0.0` inside the container while still using `127.0.0.1` as the default when running the CLI directly on a workstation. To stop: `docker stop data-boar-audit && docker rm data-boar-audit`.

## 4. Run with Docker Compose

Docker Compose is a simple alternative to Swarm for single-host or small setups. Use the Compose file in `deploy/` and optionally an override to bind-mount your config.

### 4.1 Prepare config

From the **repository root**:

```bash
mkdir -p data
cp deploy/config.example.yaml data/config.yaml
# Edit data/config.yaml (targets, report.output_dir, etc.)
```

### 4.2 Optional: bind mount for `/data`

By default `deploy/docker-compose.yml` uses a named volume `data-boar-data`. To use a host directory (e.g. `./data`) instead, use the override file:

```bash
cp deploy/docker-compose.override.example.yml deploy/docker-compose.override.yml
# deploy/docker-compose.override.yml already sets volumes: - ./data:/data
```

If you use the named volume, ensure `config.yaml` is placed inside it (e.g. via a one-off container) before the first run.

### 4.3 Start the stack

```bash
# From repo root
docker compose -f deploy/docker-compose.yml -f deploy/docker-compose.override.yml up -d
```

If you did not create an override, use:

```bash
docker compose -f deploy/docker-compose.yml up -d
```

(Then populate the `data-boar-data` volume with `config.yaml` if needed.)

### 4.4 Access and manage

- **Dashboard:** <http://localhost:8088/>
- **API docs:** <http://localhost:8088/docs>
- **Health:** <http://localhost:8088/health>

```bash
# View logs
docker compose -f deploy/docker-compose.yml logs -f data-boar

# Stop and remove
docker compose -f deploy/docker-compose.yml -f deploy/docker-compose.override.yml down
```

### 4.5 Using the pre-built image (no local build)

In `deploy/docker-compose.yml` set `image: fabioleitao/data_boar:latest` (or your registry) and remove or comment out the `build:` block. Then run the same `docker compose ... up -d` commands.

## 5. Deploy with Docker Swarm

Docker Swarm is an alternative for orchestrating the service across a cluster. Use the same Compose file with `docker stack deploy`.

### 5.1 Initialize Swarm (if not already)

```bash
docker swarm init
```

### 5.2 Use the stack (Compose file is Swarm-compatible)

From the **repository root**:

```bash
# Ensure config is available to the service. Option 1: bind mount a host dir
mkdir -p data
cp deploy/config.example.yaml data/config.yaml
# Edit data/config.yaml

# Override volume to bind mount ./data into the service (create override from the example first)
cp deploy/docker-compose.override.example.yml deploy/docker-compose.override.yml
docker stack deploy -c deploy/docker-compose.yml -c deploy/docker-compose.override.yml data-boar-audit
```

If you use the default **named volume** `data-boar-data`, the first time the service starts the container will see an empty `/data`. You must put `config.yaml` into that volume (e.g. run a one-off container that mounts the volume and copies a file in, or use a config mount). Easiest for local: **bind mount**.

Create `deploy/docker-compose.override.yml` (or a fragment) to bind mount without editing the main file:

```yaml
# deploy/docker-compose.override.yml (optional, for bind mount)
version: "3.8"
services:
  data-boar:
    volumes:

      - ./data:/data

```

Then from repo root:

```bash
docker stack deploy -c deploy/docker-compose.yml -c deploy/docker-compose.override.yml data-boar-audit
```

If you don't use an override, ensure the stack's `data-boar-data` volume is populated with `config.yaml` (e.g. via a one-off container).

### 5.3 Check the service

```bash
docker service ls
docker service ps data-boar-audit_data-boar
docker service logs data-boar-audit_data-boar
```

### 5.4 Access

- Dashboard: <http://localhost:8088/>
- API: <http://localhost:8088/docs>

Port 8088 is exposed by the Compose file.

### 5.5 Remove the stack

```bash
docker stack rm data-boar-audit
```

## 6. Deploy with Kubernetes

Kubernetes is an alternative to Docker Swarm for running the app in a cluster. The same image runs with default command (web API + frontend). Manifests are in `deploy/kubernetes/`.

### 6.1 Prerequisites

- **kubectl** and access to a cluster.
- **Image:** Set the image in `deploy/kubernetes/deployment.yaml` (e.g. `fabioleitao/data_boar:latest` or your registry).
- **Config:** The included ConfigMap provides a minimal `config.yaml`. Replace or extend it for production (see `deploy/kubernetes/README.md`).

### 6.2 Apply the manifests

From the **repository root**:

```bash
# Optional: set image via env (or edit deploy/kubernetes/deployment.yaml)
export IMAGE=fabioleitao/data_boar:latest

kubectl apply -f deploy/kubernetes/
```

This creates the Deployment, Service (ClusterIP on 8088), and ConfigMap. For full details (NodePort, LoadBalancer, Ingress, persistence) see **deploy/kubernetes/README.md**.

### 6.3 Access

Expose the service via NodePort, LoadBalancer, or Ingress to port 8088. Then:

- **Dashboard:** <http://\<external\>:8088/>
- **API docs:** <http://\<external\>:8088/docs>
- **Health:** <http://\<external\>:8088/health>

### 6.4 CLI one-shot (Job)

To run a single audit from the CLI in the cluster, use a **Job** that overrides the container command. Example and details are in `deploy/kubernetes/README.md`.

## 7. Using the public image (no local build)

1. In `deploy/docker-compose.yml` set `image:` to your published image (e.g. `fabioleitao/data_boar:latest`) and remove or comment out the `build:` block.
1. Prepare `/data/config.yaml` as in section 2 (volume or bind mount).
1. Run with **docker run** (section 3), **Docker Compose** (section 4), **Docker Swarm** (section 5), or **Kubernetes** (section 6) as above.

## 8. Docker Hub: supported tags and retiring old images

**Why this matters:** Public tags remain **pullable** until you delete them on Docker Hub. Cleaning up **obsolete** tags reduces casual reuse of old builds (CVEs, wrong defaults) and aligns docs with what you actually support.

1. **Inventory:** In [Docker Hub](https://hub.docker.com/r/fabioleitao/data_boar/tags) list all tags; note which CI, partners, or docs pin each tag (e.g. `latest`, `1.6.5`).
1. **Decide support policy:** Typically keep **`latest`** plus **current semver** (and optionally one previous semver for rollback). Document the supported set here; maintainers may also mirror the matrix under **Internal and reference** in [README.md](../README.md) or [SECURITY.md](../SECURITY.md) when useful.
1. **Delete on Hub:** Hub → repository → **Tags** → delete tags you no longer support. **Warning:** Anyone who already pulled a tag still has that image locally; deletion only stops *new* pulls from Hub.
1. **Update automation:** Adjust CI/CD and `docker-compose` / Kubernetes manifests so nothing references removed tags.
1. **Commercial / IP note:** Tag hygiene is **not** a substitute for licensing or private issuer repos; it complements them. See [CODE_PROTECTION_OPERATOR_PLAYBOOK.md](../CODE_PROTECTION_OPERATOR_PLAYBOOK.md).

**Português (Brasil):** [DEPLOY.pt_BR.md §8](DEPLOY.pt_BR.md#8-docker-hub-tags-suportadas-e-descontinuar-imagens-antigas).

## 9. Backup and restore (persistent data)

Typical deployments keep all durable state under **`/data`** (volume or bind mount): **`config.yaml`**, the **SQLite** file from `sqlite_path` (default **`/data/audit_results.db`**), and **report output** under `report.output_dir` (often `/data` or a subdirectory). Optional files such as ML/DL term YAMLs belong in the same tree if referenced by config.

#### What to back up

- Copy or snapshot the **entire** host directory or volume you mount at **`/data`** (or the Kubernetes PVC contents), so you preserve config, database, reports, and any auxiliary files paths in `config.yaml` point to.

#### How to restore

1. Stop the container, Compose stack, Swarm service, or scale the Kubernetes Deployment to zero.
1. Restore files onto a new volume or directory at the same mount path (`/data` inside the container).
1. Ensure **file ownership** is compatible with the image user (**UID 1000** / `appuser`) when using bind mounts on Linux hosts.
1. Start the workload again; verify **`GET /health`**, then run a short scan or open the dashboard to confirm SQLite and reports are visible.

#### Operational notes

- Prefer **API keys from environment** (`api.api_key_from_env`) so secrets are not only in files you include in file-level backups—see [SECURITY.md](../../SECURITY.md).
- For long-term recovery, record the **image tag or digest** you ran (e.g. `fabioleitao/data_boar:1.7.3`) alongside the data backup so you can match behaviour when restoring.

**Português (Brasil):** [DEPLOY.pt_BR.md §9](DEPLOY.pt_BR.md#9-backup-e-restore-dados-persistentes).

## 10. Run with Podman (rootless, LMDE / Debian / Fedora)

[Podman](https://podman.io) is an alternative container runtime to Docker with a similar CLI. It runs **rootless by default**, which means containers do not require root privileges on the host. This section covers the basic deployment pattern; it does not document lab-specific private configurations.

### Key differences from Docker

| Topic | Docker | Podman |
| ----- | ------ | ------ |
| Default mode | Root (unless rootless configured) | Rootless (per-user) |
| Daemon | Background daemon required | Daemonless (fork/exec) |
| Compose | Docker Compose v2 (`docker compose`) | `podman-compose` or `podman kube play` |
| Socket path | `/var/run/docker.sock` | `/run/user/<UID>/podman/podman.sock` |
| Image compat | OCI images (same format) | OCI images (compatible) |

### Pull and run (rootless)

```bash
# Pull the image from Docker Hub (same image as Docker deployments)
podman pull fabioleitao/data_boar:latest

# Run as API + frontend (port 8088) with a bind mount for persistent data
podman run -d \
  --name data-boar \
  -p 8088:8088 \
  -v ./data:/data:Z \
  -e CONFIG_PATH=/data/config.yaml \
  fabioleitao/data_boar:latest
```

> **Note:** The `:Z` suffix on the volume mount sets the SELinux label for rootless Podman on Fedora/RHEL-based systems. On Debian/LMDE it is ignored safely.

### CLI one-shot with Podman

```bash
podman run --rm \
  -v ./data:/data:Z \
  fabioleitao/data_boar:latest \
  python main.py --config /data/config.yaml --output /data/report.xlsx
```

### Manage the container

```bash
# Check status
podman ps

# View logs
podman logs -f data-boar

# Stop and remove
podman stop data-boar && podman rm data-boar
```

### Persistent user service (systemd)

On systems with systemd (LMDE, Debian, Fedora), you can generate a systemd unit from the running container so it starts automatically on login:

```bash
podman generate systemd --name data-boar --files --new
mkdir -p ~/.config/systemd/user
mv container-data-boar.service ~/.config/systemd/user/
systemctl --user enable --now container-data-boar.service
```

### Compose with Podman

`podman-compose` accepts the same `docker-compose.yml` format:

```bash
pip install podman-compose        # or use your distro package
podman-compose -f deploy/docker-compose.yml up -d
```

### Lessons learned

Operational lessons from lab deployments (LAB-NODE-02, LMDE 7) will be documented in [`docs/ops/LAB_LESSONS_LEARNED.md`](../ops/LAB_LESSONS_LEARNED.md) as they accumulate. Check that file for host-specific troubleshooting tips.

**Português (Brasil):** [DEPLOY.pt_BR.md §10](DEPLOY.pt_BR.md#10-executar-com-podman-rootless-lmde--debian--fedora).

## Summary

| Goal                     | Command / step                                                                                                                             |
| ------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------ |
| Default (API + frontend) | Run image with no command override: `docker run`, Compose, Swarm, or Kubernetes                                                            |
| CLI one-shot             | Override command: `docker run ... --entrypoint python IMAGE main.py --config /data/config.yaml`                                            |
| Build image              | `docker build -t data_boar:latest .` or `docker build -t fabioleitao/data_boar:latest .`                                                   |
| Push to registry         | `docker tag ... fabioleitao/data_boar:latest` then `docker login` and `docker push fabioleitao/data_boar:latest`                           |
| **Single container**     | `docker run -d -p 8088:8088 -v ./data:/data data_boar:latest` (section 3)                                                                  |
| **Docker Compose**       | `docker compose -f deploy/docker-compose.yml -f deploy/docker-compose.override.yml up -d` — prepare `./data/config.yaml` first (section 4) |
| **Docker Swarm**         | `docker stack deploy -c deploy/docker-compose.yml -c deploy/docker-compose.override.yml data-boar-audit` (section 5)                            |
| **Kubernetes**           | `kubectl apply -f deploy/kubernetes/` — see `deploy/kubernetes/README.md` for image and config (section 6)                                 |
| **Backup / restore**     | Persisted data under `/data` (section 9): back up the mounted volume or bind mount; restore with the same layout, then verify `/health`        |
| **Podman (rootless)**    | `podman pull fabioleitao/data_boar:latest` then `podman run -d -p 8088:8088 -v ./data:/data:Z ...` (section 10)                                |

You can use **Docker Compose** or **Kubernetes** as alternatives to Docker Swarm; same image and config layout apply. All paths and image names assume you are in the repo root or in `deploy/` as indicated.

## Behind NAT, load balancer, or reverse proxy

The application runs correctly when placed behind **NAT**, a **load balancer**, or a **reverse proxy** (nginx, Traefik, Caddy, or similar). No code or config change is required for basic operation.

- **TLS at the proxy:** If HTTPS is terminated at the proxy (recommended), set **X-Forwarded-Proto: https** on requests to the app so that security headers (e.g. HSTS) and scheme detection work correctly. See [SECURITY.md](../../SECURITY.md) for HTTP security headers.
- **Client IP and host:** If you need the real client IP or original host in logs or logic, configure your proxy to send **X-Forwarded-For** and **X-Forwarded-Host**; the app can be extended to trust these when needed.
- **Subpath:** If the app is served under a path prefix (e.g. <https://example.com/audit/>), configure the proxy to strip or rewrite the prefix so the app still sees paths starting at `/`; or use the proxy's rewrite rules to map `/audit/` to the container root.

**Documentation index** (all topics, both languages): [../README.md](../README.md) · [../README.pt_BR.md](../README.pt_BR.md). **Technical guide:** [../TECH_GUIDE.md](../TECH_GUIDE.md) · [../TECH_GUIDE.pt_BR.md](../TECH_GUIDE.pt_BR.md).
