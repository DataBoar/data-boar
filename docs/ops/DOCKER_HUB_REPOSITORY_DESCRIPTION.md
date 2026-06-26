# Docker Hub — repository description (copy/paste source)

**Purpose:** The [Docker Hub UI](https://hub.docker.com/r/fabioleitao/data_boar) **Short description** and **Full description** are **not** stored in Git. This file is the **canonical text** to paste after each release so Hub stays aligned with **`pyproject.toml`**, [docs/deploy/DEPLOY.md](../deploy/DEPLOY.md), and [docs/releases/](../releases/).

**When to update:** Immediately after you push **`fabioleitao/data_boar:<semver>`** and **`latest`** for a **stable** release (final **`X.Y.Z`**, not **`-beta`** / **`-rc`** images). Bump the **Current release** line and **Supported tags** below to match [CHANGELOG.md](../../CHANGELOG.md) / the published tag. **Docker Hub does not read this file** — you must open **Repository → General → Edit** and paste; otherwise the public page can stay stuck for years (e.g. old **## Tags** still showing **1.6.5**).

**Portuguese pointer:** [DOCKER_HUB_REPOSITORY_DESCRIPTION.pt_BR.md](DOCKER_HUB_REPOSITORY_DESCRIPTION.pt_BR.md)

---

## Short description (Docker Hub field — ~100 characters)

Use one line (adjust version when you bump):

```text
Data Boar — PII/sensitive data discovery (LGPD/GDPR-aware). OSS by Fabio Leitao. Tags: latest, 1.7.4. Docs on GitHub.
```

---

## Full description (Docker Hub — Markdown)

Copy from the block below into **Repository → Edit** on Docker Hub.



```markdown
## Data Boar

**Compliance-aware discovery** of personal and sensitive data across databases, files, APIs, and more — **data soup** in, structured findings out. Open-source Python stack with optional ML/DL; aligns with **LGPD**, **GDPR**, **CCPA**, and other frameworks via config.

**Current Hub image tags:** **`latest`** and **`1.7.4`** resolve to the **same digest** (Linux/amd64). Pin **`1.7.4`** for an immutable semver pull string. The prior **golden** tag **`v1.7.2-safe`** may still appear under **Tags** for historical audit — prefer **`1.7.4`** or **`latest`** for new deploys unless you intentionally pin the golden digest. Confirm **`pyproject.toml`** and **[GitHub Releases](https://github.com/FabioLeitao/data-boar/releases)** for the exact pairing.

### Copyright and maintainer

- **Author / copyright:** **Fabio Leitao** — [LICENSE](https://github.com/FabioLeitao/data-boar/blob/main/LICENSE) (BSD-3-Clause).
- **Professional profile:** Add your LinkedIn URL in the Hub **Full description** editor when publishing (do not embed personal profile URLs in this tracked file).
- **Security:** Vulnerability reporting — [SECURITY.md](https://github.com/FabioLeitao/data-boar/blob/main/SECURITY.md).

### Supported tags

- **`fabioleitao/data_boar:latest`** — newest published build
- **`fabioleitao/data_boar:1.7.4`** — immutable semver tag (same image as **`latest`** at last stable publish)

### Quick start (web API + dashboard on port 8088)

Prepare a directory with `config.yaml` and mount it at `/data`:

```bash
docker pull fabioleitao/data_boar:latest
docker run -d -p 8088:8088 -v "$(pwd)/data:/data" -e CONFIG_PATH=/data/config.yaml fabioleitao/data_boar:latest
```

Create `data/config.yaml` from the repo’s `deploy/config.example.yaml` if you do not have one.

### CLI one-shot (override container command)

Use **`python main.py`** (legacy `run.py` was removed in 1.6.7):

```bash
docker run --rm -v "$(pwd)/data:/data" fabioleitao/data_boar:latest \
  python main.py --config /data/config.yaml
```

### Documentation

- **Usage / CLI / config:** [https://github.com/FabioLeitao/data-boar/blob/main/docs/USAGE.md](https://github.com/FabioLeitao/data-boar/blob/main/docs/USAGE.md)
- **Deploy (Docker Compose, Swarm, Kubernetes):** [https://github.com/FabioLeitao/data-boar/blob/main/docs/deploy/DEPLOY.md](https://github.com/FabioLeitao/data-boar/blob/main/docs/deploy/DEPLOY.md)
- **Releases:** [https://github.com/FabioLeitao/data-boar/releases](https://github.com/FabioLeitao/data-boar/releases)

**Source:** [https://github.com/FabioLeitao/data-boar](https://github.com/FabioLeitao/data-boar)

### Build and push (maintainers)

From the repo root, after tests pass and you are logged in to Docker Hub:

```bash
uv run pytest -v -W error
docker build -t fabioleitao/data_boar:latest .
docker tag fabioleitao/data_boar:latest fabioleitao/data_boar:1.7.4
docker login
docker push fabioleitao/data_boar:latest
docker push fabioleitao/data_boar:1.7.4
```

For the next formal release, bump **`pyproject.toml`** / **`core/about.py`** per [VERSIONING.md](https://github.com/FabioLeitao/data-boar/blob/main/docs/VERSIONING.md), publish semver tags per [DOCKER_IMAGE_RELEASE_ORDER.md](https://github.com/FabioLeitao/data-boar/blob/main/docs/ops/DOCKER_IMAGE_RELEASE_ORDER.md), then **replace the entire Full description** on Hub from this file so **Supported tags** and the **`docker tag`** lines stay in sync with the **Tags** tab (no partial edits).
```



---

## Maintainer checklist (anti-drift)

1. Push image tags per [DOCKER_IMAGE_RELEASE_ORDER.md](DOCKER_IMAGE_RELEASE_ORDER.md) (**stable** semver only for this description refresh — **`-beta`** / **`-rc`** preview pushes do **not** require updating the public Hub marketing text).
2. In Docker Hub **Repository → General → Edit**: paste **Short** (one line) + **Full** (entire fenced block from [Full description](#full-description-docker-hub--markdown) above). **Replace the whole Full description**, do not patch a paragraph in the middle — old custom sections (e.g. legacy **## Tags** listing **1.6.5**) survive otherwise.
3. After paste, open the public repo page and **visually confirm** **Current release**, **Supported tags** / semver examples, and the **Short description** preview — no stale pinned version.
4. Refresh [today-mode/PUBLISHED_SYNC.md](today-mode/PUBLISHED_SYNC.md) ([pt-BR](today-mode/PUBLISHED_SYNC.pt_BR.md)).
5. Sweep **customer-facing** copy: [README.md](../../README.md) / [README.pt_BR.md](../../README.pt_BR.md) **Current release** line, [VERSIONING.md](../VERSIONING.md) checklist, milestone/social drafts that cite a version (see **§ Distribution** in VERSIONING).

