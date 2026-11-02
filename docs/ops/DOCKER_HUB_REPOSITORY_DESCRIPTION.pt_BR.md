# Docker Hub — descrição do repositório (fonte para copiar/colar)

**English (canônico para colar no Hub UI):** [DOCKER_HUB_REPOSITORY_DESCRIPTION.md](DOCKER_HUB_REPOSITORY_DESCRIPTION.md)

**Objetivo:** O texto curto e a descrição longa no [Docker Hub](https://hub.docker.com/r/fabioleitao/data_boar) **não** ficam versionados no Git. O documento em inglês é a **fonte** para colar após cada release (passo 9 do ritual). Este arquivo é o **gêmeo pt-BR** da seção de **escolha**.

**Quando atualizar:** Logo após **`docker push`** / ritual podman de **`fabioleitao/data_boar:<semver>`** e **`latest`**. No Hub: cole **Short** + **Full** do **EN**. Mantenha este pt-BR alinhado (LCM). Ritual: [DOCKER_IMAGE_RELEASE_ORDER.pt_BR.md](DOCKER_IMAGE_RELEASE_ORDER.pt_BR.md) **passo 9**.

---

## O que faz

- **Chega nas suas fontes:** arquivos, **SQL**, **NoSQL**, **APIs**, **Power BI**, **Dataverse**, **SharePoint**, **SMB/NFS** e mais. Varre dentro de arquivos compactados (zip, tar, gz, 7z com extra opcional) e lida com encodings multilíngues e legados.
- **Encontra mais do que identificadores óbvios:** CPF, CNPJ (incluindo o formato alfanumérico novo), e-mail, telefone e dados de pagamento — mais **categorias sensíveis** (saúde, religião, opinião política, biométrico, genético: LGPD art. 5º II, GDPR art. 9) e **combinações de campos que podem reidentificar pessoas**. **Dados de menores** têm lógica de detector dedicada.
- **Metadados, não o dado:** registra onde algo foi encontrado e qual padrão casou. Não armazena nem exfiltra o dado pessoal em si.
- **Um motor dirigido por config:** um único arquivo YAML/JSON define alvos, regex, termos ML/DL, tags de norma e overrides de recomendação, sem mudar código para alinhar a outro framework.
- **Rode do seu jeito:** **CLI** one-shot, ou **REST API** (porta **8088**) com dashboard web; os scans podem ser agendados pela API.
- **Saídas que você entrega a um auditor:** relatórios **Excel**, **heatmaps**, **tendências** entre sessões e JSON de auditoria, com recomendações etiquetadas por norma.

## Aceleração Rust

**`boar_fast_filter`** é um acelerador Rust (PyO3) **embutido nesta imagem**. É um pré-filtro para três padrões de alto volume: **CPF, e-mail e números de cartão**. Num microbenchmark pinado e reproduzível em **200 mil linhas** (mesmo payload, contagens de hit idênticas: 100.000 dos dois lados) ficou **4,69×** mais rápido que o pré-filtro Python ([`tests/benchmarks/rust_prefilter_hotspot.json`](https://github.com/DataBoar/data-boar/blob/main/tests/benchmarks/rust_prefilter_hotspot.json), 2026-06-30). Esse número mede **o estágio do filtro isolado**; **não** é ganho ponta a ponta do scan. Os demais detectores, inclusive CNPJ, continuam em Python.

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
