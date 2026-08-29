# Docker Hub — descrição do repositório (fonte para copiar/colar)

**English (canônico para colar no Hub UI):** [DOCKER_HUB_REPOSITORY_DESCRIPTION.md](DOCKER_HUB_REPOSITORY_DESCRIPTION.md)

**Objetivo:** O texto curto e a descrição longa no [Docker Hub](https://hub.docker.com/r/fabioleitao/data_boar) **não** ficam versionados no Git. O documento em inglês é a **fonte** para colar após cada release (passo 9 do ritual). Este arquivo é o **gêmeo pt-BR** da seção de **escolha**.

**Quando atualizar:** Logo após **`docker push`** / ritual podman de **`fabioleitao/data_boar:<semver>`** e **`latest`**. No Hub: cole **Short** + **Full** do **EN**. Mantenha este pt-BR alinhado (LCM). Ritual: [DOCKER_IMAGE_RELEASE_ORDER.pt_BR.md](DOCKER_IMAGE_RELEASE_ORDER.pt_BR.md) **passo 9**.

---

## Qual imagem puxar? (escolha)

**Uma imagem publicada (cp314t).** No-GIL em runtime é **só Enterprise** (`PYTHON_GIL=1` nos demais tiers). Cole o Full **quando essa imagem estiver no Hub** — até o próximo publish, `:latest` no Hub ainda é a imagem GIL de **2026-07-30**.

### `latest` / `1.7.4.post12` — universal, é o default

Use esta a menos que tenha motivo concreto para free-threading.

- Python **3.14 com GIL**, distroless nonroot (uid **65532**).
- **`popcnt = 0`** em **540** `.so` (medido) → roda em **qualquer x86-64**, inclusive **Celeron 900 de 2009** sem AVX.
- ML completo: **numpy 2.5.1 · scipy 1.18.0 · scikit-learn 1.9.0 · pandas 3.0.5**.
- **`boar_fast_filter`** (Rust) via **`abi3`**.
- ~**309 MB** no Hub (`sha256:ab8f5dad3e336…`, medido **2026-07-30**).

**Use esta se:** não sabe qual escolher · hardware antigo ou heterogêneo · frota mista · on-prem com máquina de idade desconhecida · quer o piso garantido.

### `1.7.4.post12-nogil` — paralelismo real (opt-in)

- Python **3.14t free-threaded** (PEP 703); `sys._is_gil_enabled()` → **False** — **inclusive depois de `import sqlalchemy`**.
- Mesmo ML, wheels **`cp314t`** — **`cp314` e `cp314t` não são intercambiáveis**.
- **`boar_fast_filter`** compilado **nativo para `cp314t`** (não abi3).
- **SQLAlchemy é puro-Python nesta imagem** (`DISABLE_SQLALCHEMY_CEXT=1`, zero `.so` em `sqlalchemy/**`). O cyextension de estoque **religa o GIL** no import e anularia o propósito da `-nogil`. Na imagem GIL (`latest` / `post12`) o cext **permanece** — correto lá.
- **Exige x86-64-v2+** — o **numpy cp314t** de upstream usa **`popcnt`** (**1477** ocorrências, medido). **Não roda** em CPU sem SSE4.2/POPCNT.
- **`:latest` nunca aponta para esta tag.**

**Use esta se:** CPU moderna **e** vários workers **e** detecção **regex-bound**.

**Não use se:** hardware antigo/desconhecido, ou **1 worker** (não há ganho).

### O que “mais rápido” significa (microbenchmark medido + mecanismo)

Mecanismo ([#551](https://github.com/DataBoar/data-boar/issues/551)): workers em **regex Python puro** (`core/detector.py`) são **serializados pelo GIL**; free-threaded remove isso. **`boar_fast_filter`** já libera o GIL (ganho menor). I/O-bound: marginal.

**Medido no builder nogil** (microbenchmark — **não** substitui `--demo` real): com cext, GIL volta a **True** e regex 8 threads fica **0,90×** (pior que 1 thread); sem cext, GIL fica **False** e regex 8 threads fica **5,30×**, com SELECT ~**+21%** e INSERT igual. A imagem paga esse SELECT para não anular o paralelismo da detecção. Sem outros multiplicadores inventados. **Não** use `PYTHON_GIL=0` / `-Xgil=0` para manter o cext.

### Tier de licença limita workers — e o GIL

Os bits são free-threaded, mas **no-GIL na subida do processo é só Enterprise**. Os demais tiers recebem `PYTHON_GIL=1`. O teto de workers continua `min(scan.max_workers, tier cap)` em `core/engine.py` (`#551`); sem JWT vale `OPEN_MODE_WORKER_CAP`.

---

## Tags (referência rápida)

| Tag | Papel |
| --- | ----- |
| **`latest`** | Próximo publish: cp314t + gate de GIL por licença. **Até lá** = **`1.7.4.post12`** (GIL). |
| **`1.7.4.post12`** | Última `:latest` com GIL (qualquer x86-64, `popcnt=0`). |
| **`1.7.4`** | GA de junho/2026 (histórica). |

**Checklist / versão nos artefatos:** [VERSIONING.md](../VERSIONING.md) · [PUBLISHED_SYNC.md](today-mode/PUBLISHED_SYNC.md).
