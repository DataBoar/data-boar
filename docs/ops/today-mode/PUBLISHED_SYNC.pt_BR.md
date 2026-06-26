# Publicado (release) vs versão no repositório (anti-stale)

**English:** [PUBLISHED_SYNC.md](PUBLISHED_SYNC.md)

**Objetivo:** Depois de um **tag Git**, **GitHub Release** ou push no **Docker Hub**, arquivos “today mode” datados ou tabelas nos **PLANS** podem ainda dizer “pendente no operador”. Este arquivo é o **registro curto de reconciliação**: atualize quando a realidade mudar.

---

## Última verificação (operador ou agente)

| Campo | Valor |
| ----- | ----- |
| **Verificado** | **2026-06-26** |
| **`pyproject.toml` em `main`** | **`1.7.4`** (mergeado via PR **#1024**; **publicado** estável **1.7.4**) |
| **GitHub Release Latest** | [**v1.7.4**](https://github.com/FabioLeitao/data-boar/releases/tag/v1.7.4) (notas: **`docs/releases/1.7.4.md`**, **`CHANGELOG.md`**) |
| **Docker Hub** | **`fabioleitao/data_boar:1.7.4`** + **`latest`** (publicado **2026-06-26**) |
| **Próxima versão pública** | **`1.8.0-beta`** conforme [VERSIONING.md](../VERSIONING.md) + ADR-0073 |

---

## Como reconfirmar (copiar/colar)

Na raiz do repo (precisa **`gh`** autenticado + rede):

```bash
git fetch origin --tags
git tag -l "v1.7.*" --sort=-version:refname | head -5
grep -n '^version' pyproject.toml
gh release list --repo FabioLeitao/data-boar --limit 5
```

Docker Hub: confirma **`1.7.4`** e **`latest`** em [hub.docker.com/r/fabioleitao/data_boar/tags](https://hub.docker.com/r/fabioleitao/data_boar/tags) ou na API do registry; **descrição longa** alinhada a **[`docs/ops/DOCKER_HUB_REPOSITORY_DESCRIPTION.md`](../DOCKER_HUB_REPOSITORY_DESCRIPTION.md)**. **GitHub:** existe Release **`v1.7.4`**.

---

## Quando atualizar este arquivo

- **Logo após** tag + GitHub Release + push Docker de uma versão nova.
- **Opcional** numa semana calma: confirmar que a tabela ainda é verdade para os carryovers não reabrirem trabalho **já feito**.
- **Sempre** alinhar bullets de release em **`docs/plans/PLANS_TODO.md`** se ainda disserem “só no repo / pendente” para o mesmo número.

Nota de automação: **`tests/test_about_version_matches_pyproject.py`** garante **`pyproject.toml`** ↔ runtime / man `.TH`; **não** consulta GitHub nem Hub — a verificação humana ou do agente fica aqui.
