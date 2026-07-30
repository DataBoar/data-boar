# Publicado (release) vs versão no repositório (anti-stale)

**English:** [PUBLISHED_SYNC.md](PUBLISHED_SYNC.md)

**Objetivo:** Depois de um **tag Git**, **GitHub Release** ou push no **Docker Hub**, arquivos “today mode” datados ou tabelas nos **PLANS** podem ainda dizer “pendente no operador”. Este arquivo é o **registro curto de reconciliação**: atualize quando a realidade mudar.

**Guarda:** **`tests/test_published_sync.py`** falha se este arquivo (ou o EN) divergir de **`pyproject.toml`** (`version` + `maturity_build`), não citar a tag **`v*`** correspondente, ou ainda linkar o caminho pessoal pré-org no GitHub. Checagens de rede (PyPI / Hub) são opcionais/`skipif`.

---

## Última verificação (operador ou agente)

| Campo | Valor |
| ----- | ----- |
| **Verificado** | **2026-07-30** |
| **`pyproject.toml` em `main`** | **`1.7.4.post12`** (`maturity_build=263`) |
| **PyPI** | [**data-boar `1.7.4.post12`**](https://pypi.org/project/data-boar/1.7.4.post12/) — `pip install data-boar` (publicado **2026-07-30 00:42:09 UTC**, Trusted Publishing via **`publish-pypi.yml`**) |
| **GitHub Release Latest** | [**v1.7.4.post12**](https://github.com/DataBoar/data-boar/releases/tag/v1.7.4.post12) (notas: **`docs/releases/1.7.4.post12.md`**, **`CHANGELOG.md`**; tag anotada assinada por SSH) |
| **Docker Hub** | **`fabioleitao/data_boar:1.7.4.post12`** + **`latest`** = `sha256:ab8f5dad3e336…` (publicado **2026-07-30**; base **`python:3.14-slim`**, distroless nonroot, **`popcnt=0`**). Tag histórica de junho **`1.7.4`** intocada. |
| **Wheelhouse** | [**`wheelhouse-x86-64-v1-2026-07-29`**](https://github.com/DataBoar/data-boar-site/releases/tag/wheelhouse-x86-64-v1-2026-07-29) — **56** assets (incl. **10× `cp314t`** free-threaded / no-GIL) |
| **Próxima versão pública** | **`1.8.0-beta`** conforme [VERSIONING.md](../VERSIONING.md) + ADR-0073 |

---

## Como reconfirmar (copiar/colar)

Na raiz do repo (precisa **`gh`** autenticado + rede):

```bash
git fetch origin --tags
git tag -l "v1.7.*" --sort=-version:refname | head -5
grep -nE '^(version|maturity_build)' pyproject.toml
gh release list --repo DataBoar/data-boar --limit 5
uv run pytest tests/test_published_sync.py -q
```

Docker Hub: confirma **`1.7.4.post12`** e **`latest`** em [hub.docker.com/r/fabioleitao/data_boar/tags](https://hub.docker.com/r/fabioleitao/data_boar/tags) ou na API do registry; **descrição longa** alinhada a **[`docs/ops/DOCKER_HUB_REPOSITORY_DESCRIPTION.md`](../DOCKER_HUB_REPOSITORY_DESCRIPTION.md)**. **GitHub:** existe Release **`v1.7.4.post12`**. **PyPI:** [página do projeto](https://pypi.org/project/data-boar/) mostra **`1.7.4.post12`** como latest.

---

## Quando atualizar este arquivo

- **Logo após** tag + GitHub Release + push Docker de uma versão nova.
- **Opcional** numa semana calma: confirmar que a tabela ainda é verdade para os carryovers não reabrirem trabalho **já feito**.
- **Sempre** alinhar bullets de release em **`docs/plans/PLANS_TODO.md`** se ainda disserem “só no repo / pendente” para o mesmo número.

Automação: **`tests/test_published_sync.py`** (núcleo offline) + **`tests/test_about_version_matches_pyproject.py`** (`pyproject.toml` ↔ runtime / man `.TH`). Sondas de rede PyPI/Hub no teste de sync são opcionais.
