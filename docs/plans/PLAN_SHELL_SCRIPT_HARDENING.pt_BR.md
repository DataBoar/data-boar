# Plano: Endurecimento de scripts shell (shellcheck + bats seletivo)

<!-- plans-hub-summary: Inventário de `.sh` versionados, shellcheck severity=error no check-all e bats hermético para helpers de parse (#1926 parte 2). -->

**Status:** Em progresso
**Data:** 2026-10-11
**Autores:** Fabio Leitao
**Prioridade:** P3
**GitHub:** [#1926](https://github.com/DataBoar/data-boar/issues/1926)

**Sincronizado com:** [PLANS_TODO.md](PLANS_TODO.md)

## Objetivo

Endurecer scripts Bash versionados sem transformar cada wrapper de lab em ruído de CI: **shellcheck severity=error** nos dois twins do `check-all` (#1926 parte 1, já em `main`), **inventário por arquivo** com veredito explícito, e fatia **bats hermética** como passo **opcional** local (pula com aviso visível quando `bats` não está instalado). **Sem job de bats no CI.**

## Critério para bats

Um script **qualifica para bats** quando tem **branching real, parse de argumentos ou orquestração de subprocessos** exercitável de forma **hermética** (só tmp, sem rede, sem `sudo`, sem Docker). Wrappers longos de lab/ansible/docker entram no inventário mas ficam **deferidos**. Bibliotecas **sourced** qualificam quando funções puras podem ser testadas sem efeitos colaterais.

| Veredito bats | Significado |
| ------------- | ----------- |
| **yes** | Bats em `tests/bats/` |
| **pester** | Coberto por `tests/pester/` |
| **defer** | Qualifica em lógica, mas precisa de lab/rede/privilégio |
| **no** | Wrapper fino ou meta gate; só shellcheck |
| **n/a** | Exemplo/template em `docs/private.example/` |

## Inventário de `.sh` versionados (73 arquivos)

Avaliado com `git ls-files '*.sh'`. **Logic** = branching/parse/orquestração relevante para revisão de hardening. A tabela de caminhos permanece em inglês (paths do repositório).

Ver a tabela completa em [PLAN_SHELL_SCRIPT_HARDENING.md](PLAN_SHELL_SCRIPT_HARDENING.md) (mesmas 73 linhas, colunas Path / Logic / Bats / Notes).

**Fatia bats (esta fase):** 3 arquivos, 11 testes — `check_cross_platform_gaps.bats`, `demo_help.bats`, `labop_rfc1918_cidr.bats`.

## Fases

| Etapa | Status |
| ----- | ------ |
| shellcheck `--severity=error` em todos os `*.sh` no `check-all.sh` / `.ps1` | ✅ Feito (em `main`) |
| Inventário por arquivo + este plano | ✅ Feito |
| `tests/bats/` hermético + passo opcional no `check-all` | ✅ Feito |
| Expandir bats para `labop-sudoers-load-order-lib` no Linux (duplicar pester) | ⬜ Pendente |
| Cobertura adicional das linhas defer via labs com fixture | ⬜ Pendente |

## Fora de escopo

- Job de CI para bats (política: opcional só local).
- Substituir bash de Maestro/completão por testes bats integrados.
