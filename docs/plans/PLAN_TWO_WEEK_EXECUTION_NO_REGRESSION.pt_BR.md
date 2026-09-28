# Plano: Sprint de execução de duas semanas (sem regressões, baixo toil, entrega rápida)

<!-- plans-hub-summary: Sprint de duas semanas focado em no-regression, higiene de branches/PRs e uma fatia primária por ciclo -->

**English:** [PLAN_TWO_WEEK_EXECUTION_NO_REGRESSION.md](PLAN_TWO_WEEK_EXECUTION_NO_REGRESSION.md)

**Status:** Ativo
**Data:** 2026-08-16
**Autores:** Fabio Leitao
**Prioridade:** H0

**Sincronizado com:** [PLANS_TODO.md](PLANS_TODO.md) · carryover [CARRYOVER.pt_BR.md](../ops/today-mode/CARRYOVER.pt_BR.md) · âncora [OPERATOR_TODAY_MODE_2026-09-28.pt_BR.md](../ops/today-mode/OPERATOR_TODAY_MODE_2026-09-28.pt_BR.md)

**Ciclos anteriores:** **2026-08-16 → 2026-08-29** e anteriores ficam **superados** por este ciclo e [PLANS_TODO.md](PLANS_TODO.md).

### Ciclo atual — foco (2026-09-28 → 2026-10-11)

| Semana | Tema | Resultados |
| ------ | ---- | ---------- |
| **1** | **Fechar laços BFF (Maestro + Crow + lab)** | ✅ Vitórias dia 0: **[#2011](https://github.com/DataBoar/data-boar/pull/2011)**, **[#2012](https://github.com/DataBoar/data-boar/pull/2012)**, **#1992** fechada. **Meta:** fechar **maestro#91**, avançar **maestro#82**, merge **[crow#99](https://github.com/DataBoar/carrion-crow/pull/99)**, um PR **Dependabot**, smoke no **host de lab** opcional ([#756](https://github.com/DataBoar/data-boar/issues/756)). |
| **2** | **Fatia decisão GA 1.8.0** | Uma linha de **[#1980](https://github.com/DataBoar/data-boar/issues/1980)**: checklist de corte GA **ou** defer explícito com data. **Fora do default:** CRM **#2014–#2018**. |

**Definição de pronto:** **maestro#91** fechado; **crow #99** merged; **maestro#82** avançado ou defer datado; **`check-all`** verde em cada merge; carryover atualizado; sem backlog silencioso.

---

## Objetivo

Executar um sprint curto e realista de 2 semanas que mantém **testes verdes**, evita regressões, reduz toil repetitivo e avança demo -> prontidão de beta com fatias pequenas e auditáveis.

## Restrições operacionais

- Crítico primeiro: bloqueios de segurança/regressão/CI antes de polimento.
- Token-aware: uma fatia coerente por vez, com mínimo drift de contexto.
- Segurança e confiabilidade: sem atalhos nos checks.
- Locale-aware: EN canônico com espelho pt-BR quando aplicável.
- Comercialidade: sem dados privados/comerciais sensíveis em arquivos rastreados.
- Narrativa: manter o posicionamento do Data Boar alinhado ao que já está shipped.

## Escopo de duas semanas (somente essencial)

### Semana 1 - Estabilização e baseline anti-sobreposição

1. Baseline de higiene de PR:
   - Garantir que PRs ativos estejam merged, atualizados ou fechados como superseded.
   - Manter um PR canônico por assunto (docs-only vs RBAC/API vs governança).
1. Endurecimento de automação:
   - Usar `check-all --enforced` como prova pré-push/pré-merge.
   - Priorizar execução script-first (`check-all`, `lint-only`, `quick-test`, `commit-or-pr`) sobre comandos ad-hoc.
1. Testes onde importa:
   - Para cada mudança de comportamento, manter um teste de regressão direcionado no mesmo PR.
   - Evitar reescritas amplas; priorizar testes determinísticos nas rotas alteradas.
1. Controle de divergência de branch:
   - Preferir merge-main-in em branches protegidas quando force-push estiver bloqueado.
   - Estacionar PRs operator-gated quando exigirem aprovação não autônoma.

### Semana 2 - Entrega e fechamento de checkpoint

1. Uma fatia de produção relevante:
   - Escolher uma fatia pequena de `PLANS_TODO` com impacto direto em demo/ops e risco limitado.
   - Incluir docs e testes na mesma fatia.
1. Passagem de prontidão de beta:
   - Rodar `check-all --enforced`, validar consistência de docs e confirmar ausência de alertas críticos pendentes.
   - Fazer uma passada de validação homelab se tempo/ambiente permitir.
1. Checkpoint de redução de toil:
   - Listar os 3 principais atritos recorrentes das duas semanas.
   - Converter pelo menos um em automação ou passo curto de runbook.
1. Artefato de entrega:
   - Encerrar a semana 2 com resumo conciso (o que shipou, o que virou carryover, o que começa na sequência).

## Template diário de execução (bem curto)

1. Início do dia (5 min):
   - Se o contexto do plano estiver espalhado, usar **`pmo-view`** no preview Markdown e escolher uma fatia diária antes de codar.
   - Confirmar fatia prioritária e risco.
   - Confirmar estado de branch/PR.
1. Bloco de construção (60-120 min):
   - Implementar uma fatia estreita.
   - Adicionar/atualizar testes direcionados.
1. Gate (10-20 min):
   - Rodar checks scriptados (`check-all` ou subconjunto justificado).
   - Corrigir ou rollback antes de trocar de contexto.
1. Fechamento (5 min):
   - Registrar o que foi feito e o próximo passo atômico.

## Pacote de execução "auto mode" (token-aware default)

Use este pacote fora de MAX/Turbo, mantendo um objetivo coerente por sessão:

1. Início da sessão (trava de escopo):
   - `git status -sb`
   - `git fetch origin`
   - `gh pr list --state open`
1. Execução de uma fatia:
   - escolher uma fatia de `PLANS_TODO.md` e evitar side tracks salvo bloqueio real.
1. Gate por tipo de fatia:
   - docs-only: `.\scripts\lint-only.ps1`
   - código/comportamento: `.\scripts\check-all.ps1`
1. Fechamento seguro:
   - `.\scripts\preview-commit.ps1`
   - `.\scripts\commit-or-pr.ps1 -Action Preview -Title "<titulo>" -Body "<bullets>"`
1. Snapshot opcional de progresso:
   - `.\scripts\progress-snapshot.ps1` (hoje / 3 dias / 7 dias).

## Today mode (baixa atenção / alta velocidade)

Quando o operador tiver pouco tempo/atenção, seguir esta ordem:

1. Triagem rápida:
   - Trava de escopo opcional: usar **`pmo-view`** primeiro, olhar `PLANS_TODO.md` + este plano e assumir um único objetivo.
   - Checar PRs abertos + status.
   - Escolher um único objetivo para hoje.
1. Uma fatia segura:
   - Preferir mudança de workflow/regressão em vez de feature ampla.
1. Prova mínima:
   - Um teste direcionado + um script/check executado.
1. Parada limpa:
   - Deixar próximo passo explícito (uma linha) para retomar sem redescoberta.
1. Se branch for operator-gated ou protegida:
   - Preferir relatório de status + estacionamento ao invés de reescrita arriscada de histórico.

## Alinhamento de atalhos PMO

- **`pmo-view`**: usar para alinhamento visual rápido (tabelas/roadmap) antes de escolher semana ou fatia do dia.
- **`feature`**: token padrão de execução para a fatia escolhida.
- **`sidequest`**: só para desvios limitados; sempre voltar ao objetivo selecionado do plano/today.

## Definição de pronto (plano de duas semanas)

- Nenhuma regressão crítica/segurança sem resolução aberta por este sprint.
- Gates centrais verdes nas fatias mergeadas.
- Pelo menos 2 testes direcionados de regressão adicionados (ou atualizados) em áreas reais de risco.
- Pelo menos 1 toil recorrente convertido em script/automação ou passo curto de runbook.
- Uma fatia com impacto de demo shipada com docs + testes.
- Carryover com status/data explícitos para itens adiados (sem backlog silencioso).

## Fora de escopo (neste sprint de 2 semanas)

- Refactors grandes cruzando muitos subsistemas.
- Novas keywords amplas sem gap real em relação ao conjunto existente.
- Trabalho multi-frente em paralelo que aumente complexidade de revisão/merge.

## Riscos e mitigação

- Risco: sobrecarga por trilhas ativas demais.
  Mitigação: uma fatia ativa por vez; terminar -> gate -> mover.
- Risco: testes verdes com cobertura fraca no comportamento alterado.
  Mitigação: teste direcionado obrigatório para cada fix.
- Risco: perda de produtividade por troca excessiva de contexto.
  Mitigação: usar "Today mode" e nota explícita de fechamento diária.
