# Docker Hub — repository description (copy/paste source)

**Purpose:** The [Docker Hub UI](https://hub.docker.com/r/fabioleitao/data_boar) **Short description** and **Full description** are **not** stored in Git. This file is the **canonical text** to paste after each release so Hub stays aligned with **`pyproject.toml`**, [docs/deploy/DEPLOY.md](../deploy/DEPLOY.md), and [docs/releases/](../releases/).

**When to update:** Immediately after you push **`fabioleitao/data_boar:<semver>`** and **`latest`** for a **stable** / **`.postN`** image publish. Bump the **Current release** line and **Supported tags** below to match [CHANGELOG.md](../../CHANGELOG.md) / the published tag. **Docker Hub does not read this file** — you must open **Repository → General → Edit** and paste; otherwise the public page can stay stuck for months.

**Portuguese pointer:** [DOCKER_HUB_REPOSITORY_DESCRIPTION.pt_BR.md](DOCKER_HUB_REPOSITORY_DESCRIPTION.pt_BR.md)

**Operator ritual:** [DOCKER_IMAGE_RELEASE_ORDER.pt_BR.md](DOCKER_IMAGE_RELEASE_ORDER.pt_BR.md) **passo 9 (Hub UI)** — after push, paste **Short** + **Full** from this file (replace the entire Full description).

---

## Short description (Docker Hub field — ~100 characters)

Use one line (adjust version when you bump):

```text
Data Boar — PII discovery (LGPD/GDPR). 3.14-slim distroless, popcnt=0. Tags: latest, 1.7.4.post12.
```

---

## Full description (Docker Hub — Markdown)

Copy from the block below into **Repository → Edit** on Docker Hub.



```markdown
## Data Boar

**Compliance-aware discovery** of personal and sensitive data across databases, files, APIs, and more — **data soup** in, structured findings out. Open-source Python stack with optional ML/DL; aligns with **LGPD**, **GDPR**, **CCPA**, and other frameworks via config.

**Current Hub image:** **`latest`** and **`1.7.4.post12`** resolve to the **same digest** (Linux/amd64, measured **2026-07-30**):

`sha256:ab8f5dad3e33618e5c0dbb6d880ddafa11fc0e39c8372d5f0f1a2316d8597842` (~**309 MB** compressed on Hub).

**Runtime shape:** multi-stage build → **`python:3.14-slim`** (Debian 13 / trixie, digest-pinned) → **`gcr.io/distroless/cc-debian13:nonroot`** (uid **65532**, no shell / no apt). ML stack force-reinstalled from the hosted **x86-64-v1** wheelhouse (`wheelhouse-x86-64-v1-2026-07-29`) so **`popcnt=0`** on site-packages `.so` — runs on **any x86-64**, including Celeron-class CPUs without AVX. **`boar_fast_filter`** (Rust accelerator) is **embedded** in the image.

**Also on Hub (historical, not `latest`):** immutable June GA tag **`1.7.4`** (`sha256:04b4cd7d…`) — left untouched when post12 published. Prefer **`1.7.4.post12`** / **`latest`** for new deploys unless you intentionally pin the June digest.

Confirm **`pyproject.toml`** and **[GitHub Releases](https://github.com/DataBoar/data-boar/releases)** for the exact pairing. Free-threaded (**no-GIL** / **`cp314t`**) wheels for lab / Enterprise foresight live in the **[wheelhouse release](https://github.com/DataBoar/data-boar-site/releases/tag/wheelhouse-x86-64-v1-2026-07-29)** (not inside this container — image uses GIL **`cp314`**).

### Copyright and maintainer

- **Author / copyright:** **Fabio Leitao** — [LICENSE](https://github.com/DataBoar/data-boar/blob/main/LICENSE) (BSD-3-Clause).
- **Professional profile:** Add your LinkedIn URL in the Hub **Full description** editor when publishing (do not embed personal profile URLs in this tracked file).
- **Security:** Vulnerability reporting — [SECURITY.md](https://github.com/DataBoar/data-boar/blob/main/SECURITY.md).

### Supported tags

| Tag | Role |
| --- | ---- |
| **`fabioleitao/data_boar:latest`** | Newest published build (same digest as **`1.7.4.post12`**) |
| **`fabioleitao/data_boar:1.7.4.post12`** | Current immutable post-release image (Python **3.14** / distroless / **popcnt=0**) |
| **`fabioleitao/data_boar:1.7.4`** | June 2026 GA image (historical; **not** retagged by post12) |

### Quick start (web API + dashboard on port 8088)

Prepare a directory with `config.yaml` and mount it at `/data`:

```bash
docker pull fabioleitao/data_boar:latest
docker run -d -p 8088:8088 -v "$(pwd)/data:/data" -e CONFIG_PATH=/data/config.yaml fabioleitao/data_boar:latest
```

Create `data/config.yaml` from the repo’s `deploy/config.example.yaml` if you do not have one.

### CLI one-shot (override container command)

Distroless entrypoint is **`/usr/local/bin/python3.14`** (symlink **`python3`** / **`python`** also present):

```bash
docker run --rm -v "$(pwd)/data:/data" fabioleitao/data_boar:latest \
  python3 main.py --config /data/config.yaml
```

### Documentation

- **Usage / CLI / config:** [https://github.com/DataBoar/data-boar/blob/main/docs/USAGE.md](https://github.com/DataBoar/data-boar/blob/main/docs/USAGE.md)
- **Deploy (Docker Compose, Swarm, Kubernetes):** [https://github.com/DataBoar/data-boar/blob/main/docs/deploy/DEPLOY.md](https://github.com/DataBoar/data-boar/blob/main/docs/deploy/DEPLOY.md)
- **Releases:** [https://github.com/DataBoar/data-boar/releases](https://github.com/DataBoar/data-boar/releases)
- **Wheelhouse (x86-64-v1 + cp314t):** [https://github.com/DataBoar/data-boar-site/releases/tag/wheelhouse-x86-64-v1-2026-07-29](https://github.com/DataBoar/data-boar-site/releases/tag/wheelhouse-x86-64-v1-2026-07-29)

**Source:** [https://github.com/DataBoar/data-boar](https://github.com/DataBoar/data-boar)

### Build and push (maintainers)

From the repo root, after tests pass and you are logged in to Docker Hub (daemonless ritual on Linux):

```bash
# Canonical local ritual (build → smoke → grype --fail-on high --only-fixed → push)
~/.local/bin/build-push-podman.sh 1.7.4.post12 --debug
```

Windows / Docker Desktop path: see [DOCKER_IMAGE_RELEASE_ORDER.md](https://github.com/DataBoar/data-boar/blob/main/docs/ops/DOCKER_IMAGE_RELEASE_ORDER.md). After push, **replace the entire Full description** on Hub from this file so **Supported tags** stay in sync with the **Tags** tab.
```



---

## Maintainer checklist (anti-drift)

1. Push image tags per [DOCKER_IMAGE_RELEASE_ORDER.md](DOCKER_IMAGE_RELEASE_ORDER.md) (**stable** / **`.postN`** customer-pullable tags — **`-beta`** / **`-rc`** preview pushes do **not** require updating the public Hub marketing text).
2. In Docker Hub **Repository → General → Edit**: paste **Short** (one line) + **Full** (entire fenced block from [Full description](#full-description-docker-hub--markdown) above). **Replace the whole Full description**, do not patch a paragraph in the middle — old custom sections survive otherwise.
3. After paste, open the public repo page and **visually confirm** **Current release**, **Supported tags** / semver examples, and the **Short description** preview — no stale pinned version.
4. Refresh [today-mode/PUBLISHED_SYNC.md](today-mode/PUBLISHED_SYNC.md) ([pt-BR](today-mode/PUBLISHED_SYNC.pt_BR.md)) — guarded by **`tests/test_published_sync.py`**.
5. Sweep **customer-facing** copy: [README.md](../../README.md) / [README.pt_BR.md](../../README.pt_BR.md) **Current release** line, [VERSIONING.md](../VERSIONING.md) checklist, milestone/social drafts that cite a version (see **§ Distribution** in VERSIONING).
