# Docker Hub — repository description (copy/paste source)

**Purpose:** The [Docker Hub UI](https://hub.docker.com/r/fabioleitao/data_boar) **Short description** and **Full description** are **not** stored in Git. This file is the **canonical text** to paste after each release so Hub stays aligned with **`pyproject.toml`**, [docs/deploy/DEPLOY.md](../deploy/DEPLOY.md), and [docs/releases/](../releases/).

**When to update:** Immediately after you push **`fabioleitao/data_boar:<semver>`** and **`latest`** for a **stable** / **`.postN`** image publish (and after publishing a companion **`-nogil`** tag). Bump the **Current release** lines below to match the published tags. **Docker Hub does not read this file** — you must open **Repository → General → Edit** and paste; otherwise the public page can stay stuck for months.

**Portuguese twin (choice section):** [DOCKER_HUB_REPOSITORY_DESCRIPTION.pt_BR.md](DOCKER_HUB_REPOSITORY_DESCRIPTION.pt_BR.md)

**Operator ritual:** [DOCKER_IMAGE_RELEASE_ORDER.pt_BR.md](DOCKER_IMAGE_RELEASE_ORDER.pt_BR.md) **passo 9 (Hub UI)** — after push, paste **Short** + **Full** from this file (replace the entire Full description).

---

## Short description (Docker Hub field — ~100 characters)

Use one line (adjust version when you bump):

```text
Data Boar — PII discovery. Default: any x86-64. Optional -nogil: real parallelism (v2+).
```

---

## Full description (Docker Hub — Markdown)

Copy from the block below into **Repository → Edit** on Docker Hub.



```markdown
## Data Boar

**Compliance-aware discovery** of personal and sensitive data across databases, files, APIs, and more — **data soup** in, structured findings out. Open-source Python stack with optional ML/DL; aligns with **LGPD**, **GDPR**, **CCPA**, and other frameworks via config.

Two published image variants. **Pick by workload and CPU — not by tag name alone.**

### Which image should I pull?

#### `latest` / `1.7.4.post12` — universal default

This is the image you want unless you have a concrete reason to opt into free-threading.

- Python **3.14 with the GIL**, multi-stage → **`python:3.14-slim`** → **`gcr.io/distroless/cc-debian13:nonroot`** (uid **65532**, no shell / no apt).
- **`popcnt = 0`** on **540** site-packages `.so` files (measured) → runs on **any x86-64**, including a **2009 Celeron 900** without AVX.
- Full ML stack from the hosted x86-64-v1 wheelhouse: **numpy 2.5.1 · scipy 1.18.0 · scikit-learn 1.9.0 · pandas 3.0.5**.
- **`boar_fast_filter`** (Rust accelerator) via **`abi3`** (loads on GIL CPython 3.8+).
- Digest (measured **2026-07-30**): `sha256:ab8f5dad3e33618e5c0dbb6d880ddafa11fc0e39c8372d5f0f1a2316d8597842` (~**309 MB** compressed on Hub).

**Use this when:** you are unsure which to pick · hardware is old or mixed · on-prem fleet age is unknown · you need the guaranteed floor.

#### `1.7.4.post12-nogil` — real parallelism (opt-in)

- Python **3.14t free-threaded** (PEP 703). Inside the container: `sys._is_gil_enabled()` → **False** — **including after `import sqlalchemy`** (see below).
- Same ML versions, but wheels are **`cp314t`**. **`cp314` and `cp314t` are not interchangeable** (different `SOABI`).
- **`boar_fast_filter`** is built **native for `cp314t`** — the **`abi3`** wheel from the GIL image **does not load** here.
- **SQLAlchemy is pure-Python in this image** (`DISABLE_SQLALCHEMY_CEXT=1`, no `sqlalchemy/**/*.so`). The stock cyextension `.so` **re-enables the GIL** on import (undeclared free-threaded safety) and would cancel the point of `-nogil`. The GIL image (`latest` / `1.7.4.post12`) **keeps** the cext — correct there.
- **Requires x86-64-v2+.** Upstream **numpy cp314t** uses **`popcnt`** (**1477** hits measured). **Will not run** on CPUs without SSE4.2/POPCNT (e.g. alpine-emachines / Celeron 900).
- **`:latest` never points here.** Publishing `-nogil` must not retag `:latest` or the June GA `:1.7.4`.

**Use this when:** the host CPU is modern **and** you run **several workers** **and** detection is **regex-bound**.

**Do not use when:** hardware is old/unknown, or you run **one worker** (no parallelism to unlock).

#### What “faster” means here (measured microbenchmark + mechanism)

Mechanism ([#551](https://github.com/DataBoar/data-boar/issues/551)): workers in **pure-Python regex** (`core/detector.py`) are **serialized by the GIL** even with high `max_workers`; free-threaded removes that. **`boar_fast_filter`** (PyO3) **already releases the GIL** — smaller gain there. **I/O-bound** workers: marginal.

**Measured inside the nogil builder** (microbenchmark — **not** a substitute for a real `--demo` run):

| | SQLAlchemy **with** cext | SQLAlchemy **pure-Python** (`DISABLE_SQLALCHEMY_CEXT=1`) |
| --- | --- | --- |
| GIL after `import sqlalchemy` | **True** (defeats `-nogil`) | **False** |
| regex 8 threads vs 1 thread | **0.90×** (slower than 1 thread) | **5.30×** |
| sqlalchemy SELECT 300 rows | baseline | **+21%** wall |
| sqlalchemy INSERT 3k | unchanged | unchanged |

So the image pays a measured **~21%** on that SELECT path to keep **~5.3×** on the real detection bottleneck. Do **not** invent other multipliers. If you publish a full `--demo` comparison, include the exact command.

**Do not** force `PYTHON_GIL=0` / `-Xgil=0` to keep cext: that runs C extensions that did **not** declare free-threaded safety — silent data races on findings are worse than a slower SELECT.

#### License tier still caps workers

The free-threaded image is public, but **parallelism ceiling is a license concern**, not an image concern. Effective workers are `min(scan.max_workers, tier cap)` in `core/engine.py` (licensing worker cap / `#551`); open mode without a JWT uses `OPEN_MODE_WORKER_CAP`. Full benefit of many workers depends on the tier that allows them.

### Copyright and maintainer

- **Author / copyright:** **Fabio Leitao** — [LICENSE](https://github.com/DataBoar/data-boar/blob/main/LICENSE) (BSD-3-Clause).
- **Professional profile:** Add your LinkedIn URL in the Hub **Full description** editor when publishing (do not embed personal profile URLs in this tracked file).
- **Security:** Vulnerability reporting — [SECURITY.md](https://github.com/DataBoar/data-boar/blob/main/SECURITY.md).

### Supported tags (reference)

| Tag | What it is |
| --- | ---------- |
| **`fabioleitao/data_boar:latest`** | Same digest as **`1.7.4.post12`** (universal GIL). **Never** `-nogil`. |
| **`fabioleitao/data_boar:1.7.4.post12`** | Universal GIL image (any x86-64, `popcnt=0`) |
| **`fabioleitao/data_boar:1.7.4.post12-nogil`** | Free-threaded opt-in (x86-64-v2+ only) |
| **`fabioleitao/data_boar:1.7.4`** | June 2026 GA (historical; not retagged by post12) |

### Quick start (web API + dashboard on port 8088)

Prepare a directory with `config.yaml` and mount it at `/data`:

```bash
docker pull fabioleitao/data_boar:latest
docker run -d -p 8088:8088 -v "$(pwd)/data:/data" -e CONFIG_PATH=/data/config.yaml fabioleitao/data_boar:latest
```

Create `data/config.yaml` from the repo’s `deploy/config.example.yaml` if you do not have one.

Free-threaded (modern CPU only):

```bash
docker pull fabioleitao/data_boar:1.7.4.post12-nogil
docker run -d -p 8088:8088 -v "$(pwd)/data:/data" -e CONFIG_PATH=/data/config.yaml \
  fabioleitao/data_boar:1.7.4.post12-nogil
```

### CLI one-shot (override container command)

GIL image entrypoint: **`/usr/local/bin/python3.14`** (symlinks **`python3`** / **`python`**).  
`-nogil` entrypoint: **`/usr/local/bin/python3.14t`**.

```bash
docker run --rm -v "$(pwd)/data:/data" fabioleitao/data_boar:latest \
  python3 main.py --config /data/config.yaml
```

### Documentation

- **Usage / CLI / config:** [https://github.com/DataBoar/data-boar/blob/main/docs/USAGE.md](https://github.com/DataBoar/data-boar/blob/main/docs/USAGE.md)
- **Deploy:** [https://github.com/DataBoar/data-boar/blob/main/docs/deploy/DEPLOY.md](https://github.com/DataBoar/data-boar/blob/main/docs/deploy/DEPLOY.md)
- **Releases:** [https://github.com/DataBoar/data-boar/releases](https://github.com/DataBoar/data-boar/releases)
- **Wheelhouse (x86-64-v1 + cp314t):** [https://github.com/DataBoar/data-boar-site/releases/tag/wheelhouse-x86-64-v1-2026-07-29](https://github.com/DataBoar/data-boar-site/releases/tag/wheelhouse-x86-64-v1-2026-07-29)
- **Free-threading rationale:** [issue #551](https://github.com/DataBoar/data-boar/issues/551)

**Source:** [https://github.com/DataBoar/data-boar](https://github.com/DataBoar/data-boar)

### Build and push (maintainers)

```bash
# Universal GIL — ritual moves :latest
~/.local/bin/build-push-podman.sh 1.7.4.post12 --debug

# Free-threaded companion — validate locally; push ONLY :…-nogil (never :latest)
./scripts/docker/build-nogil-local.sh 1.7.4.post12-nogil
podman push localhost/data_boar:1.7.4.post12-nogil docker.io/fabioleitao/data_boar:1.7.4.post12-nogil
```

See [DOCKER_IMAGE_RELEASE_ORDER.md](https://github.com/DataBoar/data-boar/blob/main/docs/ops/DOCKER_IMAGE_RELEASE_ORDER.md). After any customer-pullable push, **replace the entire Full description** on Hub from this file.
```



---

## Maintainer checklist (anti-drift)

1. Push image tags per [DOCKER_IMAGE_RELEASE_ORDER.md](DOCKER_IMAGE_RELEASE_ORDER.md) (**stable** / **`.postN`** customer-pullable tags — **`-beta`** / **`-rc`** preview pushes do **not** require updating the public Hub marketing text).
2. In Docker Hub **Repository → General → Edit**: paste **Short** (one line) + **Full** (entire fenced block from [Full description](#full-description-docker-hub--markdown) above). **Replace the whole Full description**, do not patch a paragraph in the middle — old custom sections survive otherwise.
3. After paste, open the public repo page and **visually confirm** the **Which image should I pull?** section (not only the tag table), plus Short preview.
4. Refresh [today-mode/PUBLISHED_SYNC.md](today-mode/PUBLISHED_SYNC.md) ([pt-BR](today-mode/PUBLISHED_SYNC.pt_BR.md)) — guarded by **`tests/test_published_sync.py`**.
5. Sweep **customer-facing** copy: [README.md](../../README.md) / [README.pt_BR.md](../../README.pt_BR.md) **Current release** line, [VERSIONING.md](../VERSIONING.md) checklist, milestone/social drafts that cite a version (see **§ Distribution** in VERSIONING).
