# Plano: fallback do JWT de licença no path canônico org-wide

<!-- plans-hub-summary: LicenseGuard lê ~/.config/databoar/license.jwt quando env e config estão vazios e o arquivo existe (#1940). -->

**Status:** Concluído
**Data:** 2026-10-12
**Autores:** Fabio Leitao
**Prioridade:** P3
**GitHub:** [#1940](https://github.com/DataBoar/data-boar/issues/1940)

**Sincronizado com:** [PLANS_TODO.md](PLANS_TODO.md)

## Objetivo

Alinhar o `data-boar` ao `license-studio sign -deploy auto` e aos outros
bestiais: quando nem `DATA_BOAR_LICENSE_PATH` nem `licensing.license_path`
estão setados, usar o path canônico da org se o arquivo existir — sem
sobrescrever configuração explícita (#719).

## Concluído

| Etapa | Status |
| ----- | ------ |
| `core/licensing/paths.py` + precedência em `LicenseGuard._evaluate` | ✅ Feito |
| Testes herméticos (`tests/test_license_canonical_path_fallback.py`) | ✅ Feito |
| `docs/ops/QA_LOCAL_LICENSE.md` (+ pt-BR) | ✅ Feito |
| Evidência falha-então-passa na PR (reverter fallback, UNLICENSED, restaurar) | ✅ Feito (epic local) |

## Fora de escopo

- Mudanças em verificação ML-DSA / híbrida ([#2042](https://github.com/DataBoar/data-boar/issues/2042), [#2043](https://github.com/DataBoar/data-boar/issues/2043)).
- Promover `platformdirs` a dependência direta (XDG/Darwin/Windows manual).
