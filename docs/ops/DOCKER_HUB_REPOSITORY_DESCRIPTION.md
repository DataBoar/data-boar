# Docker Hub — repository description (copy/paste source)

**Purpose:** The [Docker Hub UI](https://hub.docker.com/r/fabioleitao/data_boar) **Short description** and **Full description** are **not** stored in Git. This file is the **canonical text** to paste after each release so Hub stays aligned with **`pyproject.toml`**, [docs/deploy/DEPLOY.md](../deploy/DEPLOY.md), and [docs/releases/](../releases/).

**When to update:** Immediately after you push **`fabioleitao/data_boar:<semver>`** and **`latest`** for a **stable** / **`.postN`** image publish. Bump the **Current release** lines below to match the published tags. **Docker Hub does not read this file** — you must open **Repository → General → Edit** and paste; otherwise the public page can stay stuck for months.

**Portuguese twin (choice section):** [DOCKER_HUB_REPOSITORY_DESCRIPTION.pt_BR.md](DOCKER_HUB_REPOSITORY_DESCRIPTION.pt_BR.md)

**Operator ritual:** [DOCKER_IMAGE_RELEASE_ORDER.pt_BR.md](DOCKER_IMAGE_RELEASE_ORDER.pt_BR.md) **passo 9 (Hub UI)** — after push, paste **Short** + **Full** from this file (replace the entire Full description).

---

## Short description (Docker Hub field — ~100 characters)

Use one line (adjust version when you bump):

```text
Data Boar — PII discovery. Image: cp314t; no-GIL only with Enterprise license.
```

---

## Full description (Docker Hub — Markdown)

The **1.8.0** image is already on Hub (`latest` and `1.8.0`, same digest, **2026-11-01**). Copy the block below into **Repository → Edit** on Docker Hub when you refresh the public page.

```markdown
## Data Boar

**Compliance-aware discovery** of personal and sensitive data across databases, files, APIs, and more — **data soup** in, structured findings out. Open-source Python stack with optional ML/DL; aligns with **LGPD**, **GDPR**, **CCPA**, and other frameworks via config.

**Current Hub image (release `1.8.0`):** **`latest`** and **`1.8.0`** resolve to the **same digest** (Linux/amd64, pushed **2026-11-01**):

`sha256:1f7a8a32b2fced12969382579721d6311a6b4f3fd98d2e6ffca921da47ec6ebc` (~**281 MB** compressed on Hub).

**One published image, free-threaded CPython (`cp314t`).** **No-GIL at runtime is Enterprise-only**: the container entrypoint sets `PYTHON_GIL=1` for every other license tier. Do not force `PYTHON_GIL=0`.

**CPU requirement changed:** this image targets **x86-64-v2 or newer** (SSE4.2 / POPCNT). It does **not** run on older CPUs without POPCNT (for example Celeron 900-class machines). For those hosts, pin **`1.7.4.post12`** (GIL image, runs on any x86-64).

**Runtime shape:** multi-stage build → **`python:3.14-slim`** + free-threaded CPython 3.14 (installed with `uv`) → **`gcr.io/distroless/cc-debian13:nonroot`** (uid **65532**, no shell / no apt). **`boar_fast_filter`** (Rust accelerator) is **embedded** in the image. SQLAlchemy is pure-Python here (no C extension), so importing it does not re-enable the GIL.

**Release:** [GitHub Release v1.8.0](https://github.com/DataBoar/data-boar/releases/tag/v1.8.0) · PyPI [`data-boar 1.8.0`](https://pypi.org/project/data-boar/1.8.0/). Confirm **`pyproject.toml`** and **[GitHub Releases](https://github.com/DataBoar/data-boar/releases)** for the exact pairing.

### Copyright and maintainer

- **Author / copyright:** **Fabio Leitao** — [LICENSE](https://github.com/DataBoar/data-boar/blob/main/LICENSE) (BSD-3-Clause).
- **Professional profile:** Add your LinkedIn URL in the Hub **Full description** editor when publishing (do not embed personal profile URLs in this tracked file).
- **Security:** Vulnerability reporting — [SECURITY.md](https://github.com/DataBoar/data-boar/blob/main/SECURITY.md).

### Supported tags

| Tag | Role |
| --- | ---- |
| **`fabioleitao/data_boar:latest`** | Newest published build (same digest as **`1.8.0`**) |
| **`fabioleitao/data_boar:1.8.0`** | Current immutable release image (free-threaded **`cp314t`** / distroless / **x86-64-v2+**) |
| **`fabioleitao/data_boar:1.7.4.post12`** | Previous image: GIL, runs on any x86-64 (**popcnt=0**); pin it for older CPUs |
| **`fabioleitao/data_boar:1.7.4`** | June 2026 GA image (historical) |

### Quick start (web API + dashboard on port 8088)

Prepare a directory with `config.yaml` and mount it at `/data`:

```bash
docker pull fabioleitao/data_boar:latest
docker run -d -p 8088:8088 -v "$(pwd)/data:/data" -e CONFIG_PATH=/data/config.yaml fabioleitao/data_boar:latest
```
```



---

## Maintainer checklist (anti-drift)

1. Push image tags per [DOCKER_IMAGE_RELEASE_ORDER.md](DOCKER_IMAGE_RELEASE_ORDER.md) (**stable** / **`.postN`** customer-pullable tags — **`-beta`** / **`-rc`** preview pushes do **not** require updating the public Hub marketing text).
2. In Docker Hub **Repository → General → Edit**: paste **Short** (one line) + **Full** (entire fenced block from [Full description](#full-description-docker-hub--markdown) above). **Replace the whole Full description**, do not patch a paragraph in the middle — old custom sections survive otherwise.
3. After paste, open the public repo page and **visually confirm** the **Which image should I pull?** section (not only the tag table), plus Short preview.
4. Refresh [today-mode/PUBLISHED_SYNC.md](today-mode/PUBLISHED_SYNC.md) ([pt-BR](today-mode/PUBLISHED_SYNC.pt_BR.md)) — guarded by **`tests/test_published_sync.py`**.
5. Sweep **customer-facing** copy: [README.md](../../README.md) / [README.pt_BR.md](../../README.pt_BR.md) **Current release** line, [VERSIONING.md](../VERSIONING.md) checklist, milestone/social drafts that cite a version (see **§ Distribution** in VERSIONING).
