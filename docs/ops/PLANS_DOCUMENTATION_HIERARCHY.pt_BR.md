# Hierarquia da documentação de planos (`docs/plans/`)

**English:** [PLANS_DOCUMENTATION_HIERARCHY.md](PLANS_DOCUMENTATION_HIERARCHY.md)

## Para que serve esta página

Colaboradores e operador às vezes misturam **issues do GitHub**, **to-dos no chat** e **`PLAN_*.md` commitados**. Este runbook define o **modelo em três camadas** que o repositório realmente indexa: sem um `PLAN_*.md` no disco, o trabalho **não** entra no hub de planos e **não** cumpre o contrato PMO do projeto para quem só lê o Git.

## Três camadas (da base ao espelho ops)

| Camada | Caminho / artefato | Função |
| ------ | ------------------- | ------ |
| **1 — Documentos de plano** | `docs/plans/PLAN_*.md` (ativos) e `docs/plans/completed/PLAN_*.md` (arquivados) | **Intenção durável:** propósito, escopo, fatias, critérios de aceite, links a ADRs e a outros planos. Corpo **só em inglês** para histórico (ver introdução de `PLANS_TODO.md`). |
| **2 — Hub de planos (índice)** | `docs/plans/PLANS_HUB.md` (+ intro curta `PLANS_HUB.pt_BR.md`) | **Tabela automática de todo `PLAN_*.md`** (aberto + concluído): título, resumo de uma linha (comentário HTML `plans-hub-summary`), cross-links opcionais `plans-hub-related`. **Não** substitui ler `PLANS_TODO` nem o arquivo do plano. Atualizar: `python scripts/plans_hub_sync.py --write` após adicionar/renomear/arquivar; CI valida com `--check`. |
| **3 — Espelho operacional consolidado** | `docs/plans/PLANS_TODO.md` | **Visão única do backlog de execução:** tabela de dependências, snapshot de integração, tabelas de **to-dos** por plano, ponteiros de triagem do GitHub, **dashboard de status** automático (`plans-stats.py`). **Este arquivo manda na ordem de execução e no feito vs pendente;** cada `PLAN_*.md` guarda a narrativa e o spec. |

**Modelo mental:**

- **`PLAN_*.md`** = *o que combinamos construir* (spec + fatias).
- **`PLANS_HUB.md`** = *catálogo de todos os arquivos de plano* (navegação).
- **`PLANS_TODO.md`** = *como isso se mistura com o resto e o que está feito ou não* (espelho ops).

## Issues do GitHub e chat

- **Issues** servem para **coordenação e triagem** (links, prioridades, discussão). **Não** substituem a camada 1.
- Quando uma issue descreve trabalho **multi-etapa** ou **transversal**, **promova**: acrescente ou estenda um **`PLAN_*.md`**, inclua linhas em **`PLANS_TODO.md`**, rode **`plans_hub_sync.py --write`** e **`plans-stats.py --write`** se as tabelas do dashboard mudarem.
- **Handoff entre ferramentas** (outro modelo ou humano na mesma issue): use a thread da issue para **decisões**, mas **grave** o resultado em **`docs/plans/`** para o hub não mentir.

## Ordem de edição (ritual mínimo)

1. Edite **`PLAN_*.md`** (status, fatias, critérios).
2. Atualize **`PLANS_TODO.md`** (no mesmo passo quando der: linha de dependência, tabela de fases, snapshot de triagem).
3. Rode **`python scripts/plans_hub_sync.py --write`** quando qualquer caminho de `PLAN_*.md` ou **`plans-hub-summary`** / **`plans-hub-related`** mudar.
4. Rode **`python scripts/plans-stats.py --write`** quando linhas de status em **`PLANS_TODO`** que alimentam o dashboard mudarem (bloco `<!-- PLANS_STATUS_DASHBOARD:START -->`).
5. Ao **concluir** plano: **`.cursor/rules/docs-plans.mdc`** — `git mv` para `docs/plans/completed/`, corrija links, hub de novo, atualize pitch conforme **`pitch-roadmap-sync.mdc`** quando o objetivo era visível para compradores.

## Relacionados

- **`.cursor/rules/docs-plans.mdc`** — localização, comentários do hub, fluxo de conclusão.
- **`docs/plans/PLANS_TODO.md`** — backlog vivo.
- **`docs/README.md`** — *Internal and reference* (entrada para links de planos a partir do hub de docs).
- **Audiência:** **`docs/ops/`** pode linkar para `docs/plans/`; docs de produto de tier externo **não** (ver **`audience-segmentation-docs.mdc`** / `tests/test_docs_external_no_plan_links.py`).
