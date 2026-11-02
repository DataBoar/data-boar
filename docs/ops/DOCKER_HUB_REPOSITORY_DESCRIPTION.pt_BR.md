# Docker Hub — descrição do repositório (fonte para copiar/colar)

**English (canônico para colar no Hub UI):** [DOCKER_HUB_REPOSITORY_DESCRIPTION.md](DOCKER_HUB_REPOSITORY_DESCRIPTION.md)

**Objetivo:** O texto curto e a descrição longa no [Docker Hub](https://hub.docker.com/r/fabioleitao/data_boar) **não** ficam versionados no Git. O documento em inglês é a **fonte** para colar após cada release (passo 9 do ritual). Este arquivo é o **gêmeo pt-BR** da seção de **escolha**.

**Quando atualizar:** Logo após **`docker push`** / ritual podman de **`fabioleitao/data_boar:<semver>`** e **`latest`**. No Hub: cole **Short** + **Full** do **EN**. Mantenha este pt-BR alinhado (LCM). Ritual: [DOCKER_IMAGE_RELEASE_ORDER.pt_BR.md](DOCKER_IMAGE_RELEASE_ORDER.pt_BR.md) **passo 9**.

---

## Qual imagem puxar? (escolha)

A imagem **1.8.0** **já está no Hub** (`latest` e `1.8.0`, mesmo digest, **2026-11-01**).

**Uma imagem publicada, CPython free-threaded (`cp314t`).** No-GIL em runtime é **só Enterprise**: o entrypoint do container define `PYTHON_GIL=1` nos demais tiers. Não force `PYTHON_GIL=0`.

**Imagem atual no Hub (release `1.8.0`):** **`latest`** e **`1.8.0`** apontam para o **mesmo digest** (Linux/amd64, enviada **2026-11-01**):

`sha256:1f7a8a32b2fced12969382579721d6311a6b4f3fd98d2e6ffca921da47ec6ebc` (~**281 MB** comprimido no Hub).

**Requisito de CPU mudou:** esta imagem exige **x86-64-v2 ou mais recente** (SSE4.2 / POPCNT). **Não** roda em CPU antiga sem POPCNT (por exemplo máquinas classe Celeron 900). Nesses hosts, fixe a tag **`1.7.4.post12`** (imagem GIL, roda em qualquer x86-64).

**Forma do runtime:** build multi-stage → **`python:3.14-slim`** + CPython 3.14 free-threaded (instalado com `uv`) → **`gcr.io/distroless/cc-debian13:nonroot`** (uid **65532**, sem shell / sem apt). **`boar_fast_filter`** (acelerador Rust) vem **embutido**. SQLAlchemy é puro-Python nesta imagem (sem extensão C), então o import não religa o GIL.

**Release:** [GitHub Release v1.8.0](https://github.com/DataBoar/data-boar/releases/tag/v1.8.0) · PyPI [`data-boar 1.8.0`](https://pypi.org/project/data-boar/1.8.0/). Confirme o **`pyproject.toml`** e as [GitHub Releases](https://github.com/DataBoar/data-boar/releases) para o pareamento exato.

Não existe tag **`-nogil`** no Hub. A **`1.7.4.post12`** histórica é GIL e roda em qualquer x86-64.

---

## Tags (referência rápida)

| Tag | Papel |
| --- | ----- |
| **`fabioleitao/data_boar:latest`** | Build publicado mais recente (mesmo digest que **`1.8.0`**) |
| **`fabioleitao/data_boar:1.8.0`** | Imagem imutável atual (free-threaded **`cp314t`** / distroless / **x86-64-v2+**) |
| **`fabioleitao/data_boar:1.7.4.post12`** | Imagem anterior: GIL, roda em qualquer x86-64 (**popcnt=0**); fixe-a em CPU antiga |
| **`fabioleitao/data_boar:1.7.4`** | Imagem GA de junho/2026 (histórica) |

**Checklist / versão nos artefatos:** [VERSIONING.md](../VERSIONING.md) · [PUBLISHED_SYNC.md](today-mode/PUBLISHED_SYNC.md).
