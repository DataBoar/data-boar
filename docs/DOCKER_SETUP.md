# Docker Setup: MCP, Build, Push, Deploy

**Português (Brasil):** [DOCKER_SETUP.pt_BR.md](DOCKER_SETUP.pt_BR.md)

Run these steps in a terminal where **Docker** is available (e.g. PowerShell or CMD after starting Docker Desktop).

**Pre-built image:** The application is published on Docker Hub as `fabioleitao/data_boar:latest` ([hub.docker.com/r/fabioleitao/data_boar](https://hub.docker.com/r/fabioleitao/data_boar)). You can `docker pull` and run that image instead of building from source (see [README](../README.md) and [deploy/DEPLOY.md](deploy/DEPLOY.md) ([pt-BR](deploy/DEPLOY.pt_BR.md))). The image includes the latest features (hybrid regex + ML + optional DL sensitivity detection; configurable ML/DL training terms via `ml_patterns_file`, `dl_patterns_file`, or `sensitivity_detection` in config — see [SENSITIVITY_DETECTION.md](SENSITIVITY_DETECTION.md)).

## Data persistence (`/data` volume)

The default image sets **`CONFIG_PATH=/data/config.yaml`**. Session **SQLite**, **Excel reports**, **heatmaps**, and **audit logs** are written to paths taken from that configuration (typically under `/data` when paths are relative to the config file). **Without a bind mount**, those files live in the container layer and are **lost** when the container is removed. Always use **`-v <host_dir>:/data`** with the same host directory for config and outputs (the examples below use `${PWD}/data:/data`). Compose overrides should mount the same host path — see [deploy/DEPLOY.md](deploy/DEPLOY.md).

**Upgrading your local image:** To refresh Docker Desktop with the current version from the repository, pull the image and restart your container(s):

```powershell
docker pull fabioleitao/data_boar:latest
# If you run a single container
docker stop data-boar-audit
docker rm data-boar-audit
docker run -d --name data-boar-audit -p 8088:8088 -v "${PWD}/data:/data" -e CONFIG_PATH=/data/config.yaml fabioleitao/data_boar:latest

# If you use Compose
docker compose -f deploy/docker-compose.yml -f deploy/docker-compose.override.yml pull
docker compose -f deploy/docker-compose.yml -f deploy/docker-compose.override.yml up -d
```

Repeat this whenever you want to pick up a new version pushed to Docker Hub (e.g. after releases or updates to the repo).

## Extras and pool licensing (`/extras` + `DATA_BOAR_MACHINE_SEED`)

The published image is **lean on purpose**: it installs only the **base SQL groups** from `pyproject.toml` — **`sql-community`**, **`mssql`** (pyodbc), and **`oracle`**. It does **not** ship all optional extras (no fat image, no image matrix, no `FROM` our image + rebuild for each customer pack).

| In the image (base) | Via runtime mount |
| ------------------- | ----------------- |
| `sql-community`, `mssql`, `oracle` (and their packages) | `nosql`, `shares`, `mssql-pymssql`, `compressed`, `dataformats`, `richmedia`, `dl`, `bigdata`, `grc-dashboard`, … |

**Runtime extension (no shell, no pip in the image):**

1. Build an ABI-compatible wheel pack on a host that matches the image Python (e.g. **cp314** for the GIL image, **cp314t** for `-nogil`) — typically `pip install --target ./extras-pack 'data-boar[nosql,shares,…]'` or equivalent wheels from the project wheelhouse channel.
2. Mount read-only: `-v /path/to/extras-pack:/extras:ro` (nonroot uid **65532**; no `--user 0`).
3. The image sets **`PYTHONPATH=/extras`** and **`VOLUME ["/extras"]`**.

**Diagnose first:** `python main.py --check-extras` (or the same flag as container entrypoint override) lists each extra × status × origin (image vs `/extras`). Post-build smoke (`scripts/docker/docker-image-smoke.sh`) **fails** if any extra marked `in_artifact: true` in `EXTRAS_MANIFEST.json` cannot import.

**ABI mismatch:** a pack built for the wrong CPython minor/variant fails **loud at startup** (fail-closed), not as a silent missing connector.

**`DATA_BOAR_MACHINE_SEED`:** declared on the image (empty by default). Set a stable secret for **Enterprise** container pools so fingerprint does not change every `docker run`. Leave empty for **Pro / Pro+** machine-count binding (hostname-derived). See [LICENSING_SPEC.md](LICENSING_SPEC.md).

Related GitHub issues: **#1400**, **#1401**, **#1399**, **#1402**.

---

## 1. Connect Cursor to Docker Desktop MCP

### Option A – Docker Desktop built-in MCP (if available)

1. Open **Docker Desktop** → **Settings** → **Features in development** (or **Beta**).
1. Enable **MCP** / **MCP Toolkit** if present.
1. Note the MCP endpoint (e.g. `npipe://...` on Windows).
1. In **Cursor** → **Settings** → **MCP** → **Add server**:
   - Name: `docker`
   - Command / URL: use the endpoint from Docker Desktop (or `docker-mcp` if it provides a CLI).

### Option B – Cursor MCP installer

```powershell
npm install -g @cursor/mcp-installer
cursor-mcp init
cursor-mcp install docker
cursor-mcp list
```

Then add the Docker MCP server in Cursor Settings → MCP using the path shown by `cursor-mcp list`.

### Option C – Manual Docker MCP

If you use a community Docker MCP (e.g. `cursor-docker-mcp`), add it in Cursor Settings → MCP with the server's command/args.

### Docker Hub MCP (recommended for pre-push checks, no manual browsing)

If you already created a dedicated Docker Hub **Personal Access Token (PAT)** (with an expiry like 90 days), a **Docker Hub** MCP can be used for fast checks such as:

- which **namespaces** you can access,
- whether a **repository** exists,
- which **tags** exist (and which architectures/OS they cover),
- tag metadata (digest, last pushed, etc.).

This is useful for token-aware operator workflows (fewer clicks, less copy/paste): before pushing, confirm the expected tag isn’t already present; after pushing, validate it showed up.

**Security notes:**

- Do **not** store PATs in tracked files (`docs/`, `scripts/`, versioned `.env`). Use the MCP **secrets storage** (Cursor/Docker Desktop) or local environment variables.
- Rotate PATs on the agreed cadence (e.g. 90 days) and keep scope minimal.
- **Recommended least privilege:** `read/write` is usually enough for checks and publishing; avoid `delete` (as you did) to reduce accidental deletion risk.

If you’re using Docker’s MCP catalog, the server is commonly named **`dockerhub`** and typically requires:

- `dockerhub.username` (public, e.g. your Docker Hub username)
- secret `dockerhub.pat_token` (the PAT — **never** commit)

**Secret format:** in some integrations, `dockerhub.pat_token` must be provided as `namespace:PAT` (e.g. `fabioleitao:<pat>`). If a namespace check fails with “missing part #2”, it’s a strong sign the MCP only received one of the two parts.

---

## 2. Build the image (web API mode)

The Dockerfile uses a multi-stage build (minimal runtime image; build tools only in the builder stage). From the **project root**:

```powershell
cd c:\Users\<username>\Documents\dev\data-boar

docker build -t data_boar:latest .
```

Default: web API + frontend. CLI remains available via `--entrypoint` override (see [deploy/DEPLOY.md](deploy/DEPLOY.md) ([pt-BR](deploy/DEPLOY.pt_BR.md))).

---

## 3. Tag and push to Docker Hub (fabioleitao)

Use your Docker Hub credentials (username `fabioleitao` and password or Access Token).

```powershell
# Tag for Docker Hub
docker tag data_boar:latest fabioleitao/data_boar:latest

# Log in (use your Docker Hub username and Access Token as password)
docker login
# Username: fabioleitao
# Password: <your password or Access Token>

# Push
docker push fabioleitao/data_boar:latest
```

Optional: push a version tag (e.g. 1.7.3):

```powershell
docker tag data_boar:latest fabioleitao/data_boar:1.7.3
docker push fabioleitao/data_boar:1.7.3
```

Non-interactive login with token:

```powershell
echo YOUR_ACCESS_TOKEN | docker login -u fabioleitao --password-stdin
docker push fabioleitao/data_boar:latest
```

---

## 4. Deploy a local container (web API)

Config is in `data/config.yaml`. Run:

```powershell
cd c:\Users\<username>\Documents\dev\data-boar

docker run -d --name data-boar-audit `
  -p 8088:8088 `
  -v "${PWD}/data:/data" `
  -e CONFIG_PATH=/data/config.yaml `
  data_boar:latest
```

Or with **Docker Compose** (alternative to single-container run):

```powershell
copy deploy\docker-compose.override.example.yml deploy\docker-compose.override.yml
docker compose -f deploy/docker-compose.yml -f deploy/docker-compose.override.yml up -d
```

(Ensure `./data/config.yaml` exists; the override mounts `./data` at `/data`.) For **Docker Swarm** or **Kubernetes**, see [deploy/DEPLOY.md](deploy/DEPLOY.md) ([pt-BR](deploy/DEPLOY.pt_BR.md)).

---

## 5. Access

- **Dashboard:** <http://localhost:8088/>
- **API docs:** <http://localhost:8088/docs>
- **Health:** <http://localhost:8088/health>

---

## 6. Stop and remove

```powershell
docker stop data-boar-audit
docker rm data-boar-audit
```

Or with Compose: `docker compose -f deploy/docker-compose.yml -f deploy/docker-compose.override.yml down`

---

## 7. Local smoke tests: container hygiene (keep it small)

Repeated `docker run` / `docker build` during smoke tests or homelab checks can leave **many stopped containers** on Docker Desktop. That complicates ports, volumes, and knowing which image is “current.”

## Policy (project convention)

1. Prefer **one** primary local container (e.g. `--name data-boar-audit`) or **one** Compose stack.
1. Allow **at most two** named containers **only when** you need an explicit **A/B** (e.g. `fabioleitao/data_boar:latest` vs a locally built `data_boar:lab`). Use clear names; avoid ad-hoc unnamed containers.
1. When a throwaway test is done, **stop and remove** extras: `docker rm -f <name>` (after confirming you do not need that instance).

## List likely leftovers

```powershell
docker ps -a --filter "name=data-boar"
```

1. **Image tags (avoid sprawl):** You do **not** need a **new tag for every smoke run** (e.g. `data_boar:smoke-post93`, `data_boar:smoke-xyz`). Each extra tag makes it harder to see what matters and can leave **many large layer stacks** referenced until you prune. Prefer **one mutable local tag** you **overwrite** on each build, e.g. **`docker build -t data_boar:lab .`** — same name as [HOMELAB_VALIDATION.md](ops/HOMELAB_VALIDATION.md) step 1.3. Only add a **second** tag when you truly need A/B (e.g. `data_boar:lab-a` vs `data_boar:lab-b`, or Hub `fabioleitao/data_boar:latest` **pulled** vs local `data_boar:lab`).
1. **Disk / retention:** After smoke, keep roughly **two** useful image lines locally (e.g. Hub **`latest`** + **`data_boar:lab`**, or latest + one older semver). **Remove** stale smoke tags and run **`docker image prune`** / **`docker builder prune`** as needed — see [BRANCH_AND_DOCKER_CLEANUP.md](ops/BRANCH_AND_DOCKER_CLEANUP.md) §4.

1. **Automation (Windows):** From repo root, **`.\scripts\docker-hub-pull.ps1`** (pull Hub `latest` + semver + previous patch), **`.\scripts\docker-lab-build.ps1`** (build **`data_boar:lab`**, optional **`lab-prev`** / **`smoke`**), **`.\scripts\docker-prune-local.ps1 -WhatIf`** then without `-WhatIf` to drop extra tags. Details: [scripts/docker/README.md](../scripts/docker/README.md).

Agent/automation guidance for this workflow lives in **`.cursor/rules/docker-local-smoke-cleanup.mdc`** and **`.cursor/skills/docker-smoke-container-hygiene/SKILL.md`** (optional for contributors using Cursor).

See also: [HOMELAB_VALIDATION.md](ops/HOMELAB_VALIDATION.md) (lab baseline uses `docker run --rm` where possible).
