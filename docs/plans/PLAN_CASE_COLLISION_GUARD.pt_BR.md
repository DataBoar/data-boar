# Plano: guarda de colisão de caixa em caminhos rastreados

<!-- plans-hub-summary: O check-all e o job lint do CI falham quando dois caminhos rastreados diferem só pela caixa (#2044). -->

**Status:** Done
**Data:** 2026-10-11
**Autores:** Fabio Leitao
**Prioridade:** P3
**GitHub:** [#2044](https://github.com/DataBoar/data-boar/issues/2044)

**Sincronizado com:** [PLANS_TODO.md](PLANS_TODO.md)

## Objetivo

Dois caminhos rastreados que diferem só pela caixa das letras convivem no Linux e quebram o checkout no Windows e no macOS padrão. `scripts/check_case_collisions.py` agrupa a saída de `git ls-files` pelo caminho em minúsculas e falha quando um grupo tem mais de um caminho distinto.

## Feito

| Passo | Status |
| ----- | ------ |
| Guarda + teste (o par `A.md`/`a.md` falha e cita os dois; caminhos únicos passam; espaço e acento passam) | ✅ Done |
| `scripts/check-all.sh` e `scripts/check-all.ps1` | ✅ Done |
| Passo no job `lint` existente de `.github/workflows/ci.yml` (sem workflow novo) | ✅ Done |

## Fora do escopo

Não entrou hook de pre-commit. `.pre-commit-config.yaml` é arquivo de gate do tripwire, e o job lint mais os dois check-all já executam a guarda.
