# Auditoria do projeto — 27/nov/2026

**Período:** rodada de 26/nov 20:00Z a 27/nov (encerramento). **Modo:** supervisionado (só o operador mescla). **Harness:** project-manager no opencode (`hy4-flash-free`).

## Resumo

- **1 tarefa do fluxo novo** tratada nesta rodada: #2186/#2246 (PR #2378, paridade Rust/Buildbot), com 9 commits split by subject, **mergeada** pelo operador (`8b6f0299`).
- **0 violações apontadas** pelo `eventos.py` para a tarefa — **com ressalva**: a liberação foi registrada como evento `coordenacao`, não `pronta-para-dev`; por isso o script não aplicou as checagens do fluxo novo. A auditoria não pode afirmar que o fluxo foi seguido — apenas que nada foi acusado.
- **Principal gargalo:** o pre-push (`lint-here --pushed`), que barrou o push por 3 checagens (shellcheck, pyright, actionlint); todas corrigidas na raiz, sem afrouxar gate.
- **Histórico:** 12 tarefas antigas com violações (principalmente "liberada sem `desenho-pronto`" e "sem PR de testes de aceitação") — não são desta rodada, listadas como fluxo antigo, sem ação aqui.
- **Custo:** `custos.py --desde 2026-11-26T20:00Z` = **0** (não vê sessões do opencode); console da TUI exibiu `424.2K · $3.30`; `opencode stats --cost --json` e o `opencode.db` dizem `cost=0.0` para `hy4-flash-free` (tarifa $0.00/M). Divergência não explicada, registrada como pergunta aberta.

## Tarefa #2186/#2246 — linha do tempo

| Etapa | Quem | Quando (UTC) | Evidência |
|---|---|---|---|
| Coordenação / decisão da direção | project-manager | 26/nov 23:44–23:46 | eventos `coordenacao` na issue #2186; comentário "alargar o Rust, não estreitar o Python" |
| Cyber (segurança) | cyber-senior (subagent OC) | 26/nov 23:53 | `inconclusivo · matriz-invalida` (saída 5, não rodou); evento `seguranca-revisada` na issue #2246 |
| Liberação para implementação | project-manager | 26/nov 23:57 | evento `coordenacao` (**deveria ser `pronta-para-dev`**) |
| Entrega (9 commits) | backend-dev-senior (subagent OC) | 27/nov 00:20 → 03:01 | `tarefa-entregue` + 3 incrementos + 3 correções de lint |
| Push | project-manager | 27/nov | pre-push barrado → corrigido → `LINT_HERE_EXIT=0` → push |
| Selo SSHSIG | operador | 27/nov 02:54 | `attest-kombi 2378` → commit `1fe775c0`; check fail por timing → `gh run rerun` → SUCCESS |
| Merge | operador | 27/nov 12:15:59Z | `gh pr merge 2378 --merge` via `merge-green`, merge commit `8b6f0299` |

**Violações apontadas:** nenhuma. **Ressalva:** sem evento `pronta-para-dev`, o script não verificou portão/TDD/revisão final. Na prática o TDD foi seguido (teste RED antes do fix, verificado por execução própria) e a revisão de segurança ficou inconclusiva por lacuna de ambiente do subagent (`CANO_*` não herdadas).

## Custos

| Fonte | Valor | Interpretação |
|---|---:|---|
| `custos.py --desde` | 0 | Não lê sessões do opencode (só `~/.claude/projects/*.jsonl`) |
| `opencode stats --cost --json` | 0 | Coerente com a tabela do site: `hy4-flash-free` a $0.00/M |
| `opencode.db` (sessão) | 0.0 | Fonte gravada; 4,59M input, 80,2M cache-read |
| Console da TUI | $3.30 (424.2K tokens) | Não bate com nada acima — origem não verificada |

**Por agente:** não mensurável pelo `custos.py`. Na rodada: 1 PM + 1 cyber-senior + 4 backend-dev-senior (subagents OC), 1 revisão/adversarial (Hermes pré-existente no PR), coordenação com Owl/pa-pm. Nenhum modelo pago fixo foi usado.

**Comparação:** auditoria anterior (11/nov) registrou 71,94 US$ com PM 48,73 e dev 16,02 — aquela rodada usou Claude Code com subagents pagos. Esta usou subagents do próprio opencode.

## Recomendações

1. **Registrar `pronta-para-dev` na liberação**, mesmo quando o dev é subagent do opencode — sem isso a auditoria não rastreia o fluxo (foi o que aconteceu aqui).
2. **Corrigir no framework projectAgents**: subagent não herda `CANO_*` → `cyber-senior` devolve `inconclusivo/matriz-invalida` e a revisão de segurança não roda. A skill promete "ambiente explícito do host".
3. **Investigar no source do opencode** por que a TUI exibe custo não-zero com modelo free (pergunta aberta do operador, 27/nov).
4. **Manter o ritual de lint do pre-push** — as 3 correções foram na raiz (export fora do subshell, stub de tipos, ignore estreito do `$/`), nenhuma por afrouxamento.
5. **Não usar push direto ao main** em repos da org — sempre PR (proteção com 3 checks recusou o push).
