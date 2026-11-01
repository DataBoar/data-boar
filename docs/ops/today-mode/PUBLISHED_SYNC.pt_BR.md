# Publicado (release) vs versão no repositório (anti-stale)

**English:** [PUBLISHED_SYNC.md](PUBLISHED_SYNC.md)

**Objetivo:** Depois de um **tag Git**, **GitHub Release** ou push no **Docker Hub**, arquivos “today mode” datados ou tabelas nos **PLANS** podem ainda dizer “pendente no operador”. Este arquivo é o **registro curto de reconciliação**: atualize quando a realidade mudar.

**Guarda:** **`tests/test_published_sync.py`** falha se este arquivo (ou o EN) divergir de **`pyproject.toml`** (`version` + `maturity_build`), não citar a tag **`v*`** correspondente, ou ainda linkar o caminho pessoal pré-org no GitHub. Checagens de rede (PyPI / Hub) são opcionais/`skipif`.

---

## Última verificação (operador ou agente)

| Campo | Valor |
| ----- | ----- |
| **Verificado** | **2026-11-01** |
| **`pyproject.toml` em `main`** | **`1.8.0`** (`maturity_build=200`) — linha de versão `1.8.0` no `main` (ADR-0073). |
| **PyPI** (publicado) | [**data-boar `1.8.0`**](https://pypi.org/project/data-boar/1.8.0/) — `pip install data-boar` (wheel `data_boar-1.8.0-py3-none-any.whl` **2026-11-01T23:15:29Z** sha256 `019e0d4227586f2113c791b513679fea0d01b40bd89bcf2521921446116c1799`; sdist `data_boar-1.8.0.tar.gz` **2026-11-01T23:15:32Z** sha256 `6fed428b8c73ff40bd6f240f1c17bf68d06d26d1693a8189c67501f9f545a49a`; `requires_python >=3.12`). TestPyPI **1.8.0**: wheel **2026-11-01T23:11:50Z**, sdist **2026-11-01T23:11:53Z**. Histórico: [**`1.7.4.post12`**](https://pypi.org/project/data-boar/1.7.4.post12/). |
| **GitHub Release Latest** (publicado) | [**v1.8.0**](https://github.com/DataBoar/data-boar/releases/tag/v1.8.0) — título **Data Boar 1.8.0** (não pré-release), publicado **2026-11-01T23:11:10Z**, tag anotada assinada no commit `3b0170641f2ab7a1358058902e12ff3f1fc3f545` (notas: **`docs/releases/1.8.0.md`**, **`CHANGELOG.md`**). Latest histórico: [**v1.7.4.post12**](https://github.com/DataBoar/data-boar/releases/tag/v1.7.4.post12). |
| **Docker Hub** (publicado) | **`fabioleitao/data_boar:1.8.0`** + **`latest`** = `sha256:1f7a8a32b2fced12969382579721d6311a6b4f3fd98d2e6ffca921da47ec6ebc` (linux/amd64, ~281 MB comprimido, enviado **2026-11-01T23:28Z**; free-threaded **cp314t**, **x86-64-v2+**; **sem** tag `-nogil`). Histórico: **`1.7.4.post12`** (`sha256:ab8f5dad3e336…`, GIL, qualquer x86-64), **`1.7.4`**, **`1.7.3`** intactas. |
| **Wheelhouse** | [**`wheelhouse-x86-64-v1-2026-07-29`**](https://github.com/DataBoar/data-boar-site/releases/tag/wheelhouse-x86-64-v1-2026-07-29) — **58** `.whl` (incl. **14× `cp314t`**: 10 ML + 4 extras SQL `linux_x86_64`) |
| **Próximo publicável** | **`1.8.0`** está no PyPI + Hub + GitHub Release (**2026-11-01**). Linha publicada histórica: **`1.7.4.post12`**. |

---

## Como reconfirmar (copiar/colar)

Na raiz do repo (precisa **`gh`** autenticado + rede):

```bash
git fetch origin --tags
git tag -l "v1.8.*" --sort=-version:refname | head -5
grep -nE '^(version|maturity_build)' pyproject.toml
gh release list --repo DataBoar/data-boar --limit 5
uv run pytest tests/test_published_sync.py -q
```

Docker Hub: confirma **`1.8.0`** e **`latest`** em [hub.docker.com/r/fabioleitao/data_boar/tags](https://hub.docker.com/r/fabioleitao/data_boar/tags) ou na API do registry; **descrição longa** alinhada a **[`docs/ops/DOCKER_HUB_REPOSITORY_DESCRIPTION.md`](../DOCKER_HUB_REPOSITORY_DESCRIPTION.md)**. **GitHub:** existe Release **`v1.8.0`**. **PyPI:** [página do projeto](https://pypi.org/project/data-boar/) mostra **`1.8.0`** como latest.

---

## Quando atualizar este arquivo

- **Logo após** tag + GitHub Release + push Docker de uma versão nova.
- **Opcional** numa semana calma: confirmar que a tabela ainda é verdade para os carryovers não reabrirem trabalho **já feito**.
- **Sempre** alinhar bullets de release em **`docs/plans/PLANS_TODO.md`** se ainda disserem “só no repo / pendente” para o mesmo número.

Automação: **`tests/test_published_sync.py`** (núcleo offline) + **`tests/test_about_version_matches_pyproject.py`** (`pyproject.toml` ↔ runtime / man `.TH`). Sondas de rede PyPI/Hub no teste de sync são opcionais.
