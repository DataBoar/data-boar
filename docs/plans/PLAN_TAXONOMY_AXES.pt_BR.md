# Plano: Eixos de taxonomia (mapa unico de prioridades ortogonais)

<!-- plans-hub-summary: Mapa canonico dos eixos H/U/A/P/G/S/M e CodeQL; links para fontes operacionais -->

**Status:** Ativo
**Date:** 2026-05-19
**Authors:** Fabio Leitao

**Espelho (EN):** [PLAN_TAXONOMY_AXES.md](PLAN_TAXONOMY_AXES.md)

**Relacionado:** [ADR-0055](../adr/ADR-0055-orthogonal-priority-axes-anti-collision-contract.md), [PLAN_G_TIER.pt_BR.md](PLAN_G_TIER.pt_BR.md)

Este documento **nao substitui** as definicoes operacionais nos arquivos linkados — ele responde **o que cada eixo mede**, **quando usa-lo** e **como nao confundir eixos**.

---

## Como ler uma afirmacao de prioridade

Correto: "Gravidade **G2**; executar como GitHub **P1** neste sprint (**S2a**); horizonte **H1**."

Incorreto: "Isso e P0" (ambiguo: CodeQL? GitHub? gravidade?).

---

### Eixo: Horizonte (H0-H5)

| Campo | Conteudo |
| ----- | -------- |
| **Mede** | A que momento do roadmap o trabalho pertence |
| **Range** | H0 fazer-agora ate H5 horizonte-sonho/PhD |
| **Racional** | Impede que pesquisa H3 bloqueie seguranca H0 |
| **Objetivo** | Sequenciamento estavel em PLANS_TODO e plans-stats |
| **Aplicabilidade** | Linhas de plano, dashboard em PLANS_TODO |
| **Fonte canonica** | [PLANS_TODO.md](PLANS_TODO.md) (taxonomia Status) |
| **Ortogonalidade** | Nao e urgencia (**U**) nem tema de sprint (**S**) |

---

### Eixo: Urgencia (U0-U3)

| Campo | Conteudo |
| ----- | -------- |
| **Mede** | Pressao de tempo sobre o operador ou implantacao |
| **Range** | U0 seguranca-agora ate U3 backlog/catalogo |
| **Racional** | Separa "importante eventualmente" de "agora" |
| **Objetivo** | Batching token-aware sem esconder U0 |
| **Aplicabilidade** | Tags de plano, today-mode do operador |
| **Fonte canonica** | [PLANS_TODO.md](PLANS_TODO.md), [TOKEN_AWARE_USAGE.md](TOKEN_AWARE_USAGE.md) |
| **Ortogonalidade** | Um achado **G3** pode ser **U3** se a execucao aguarda |

---

### Eixo: Banda de prioridade A (A1-A7)

| Campo | Conteudo |
| ----- | -------- |
| **Mede** | Passos em burst para exposicao de seguranca, PI, comercial |
| **Range** | Checklist ordenado A1-A7 (nao equivale a P0 do GitHub) |
| **Racional** | Protege receita e arvore publica sem renomear issues |
| **Objetivo** | Janelas claras de "parar trabalho em feature" |
| **Aplicabilidade** | Quando operador invoca banda A ou incidente de seguranca |
| **Fonte canonica** | [PLANS_TODO.md](PLANS_TODO.md) (secao Priority band A) |
| **Ortogonalidade** | Nao rotular passos banda-A como **[P0]** em titulos de issue |

---

### Eixo: Labels de execucao GitHub (P0-P3)

| Campo | Conteudo |
| ----- | -------- |
| **Mede** | Ordem de execucao para issues do GitHub e thin PRs |
| **Range** | P0 (caminho critico) ate P3 (manutencao) |
| **Racional** | Agentes e humanos compartilham um vocabulario de fila |
| **Objetivo** | Burn-down previsivel per [THIN_SLICE_AGENT_PRIORITY_HANDOFF.md](../ops/THIN_SLICE_AGENT_PRIORITY_HANDOFF.md) |
| **Aplicabilidade** | Titulos de issue `[P0]`-`[P3]`, handoff do assistente |
| **Fonte canonica** | [docs/ops/THIN_SLICE_AGENT_PRIORITY_HANDOFF.md](../ops/THIN_SLICE_AGENT_PRIORITY_HANDOFF.md) |
| **Ortogonalidade** | Ver linhas **G** e **CodeQL** abaixo |

---

### Eixo: Gravidade (G0-G3)

| Campo | Conteudo |
| ----- | -------- |
| **Mede** | Severidade intrinseca de um **achado** se nao tratado |
| **Range** | G0 negligivel ate G3 critico (PII, Safe-Hold) |
| **Racional** | Distingue drift cosmtico de issues classe-breach |
| **Objetivo** | Melhor triagem de auditoria sem repontuar cada issue |
| **Aplicabilidade** | Achados, auditorias de compliance, drift de plano |
| **Fonte canonica** | [PLAN_G_TIER.pt_BR.md](PLAN_G_TIER.pt_BR.md) |
| **Ortogonalidade** | **G3** com **P3** e valido (critico, execucao adiada) |

---

### Eixo: Sprints (S0-S6)

| Campo | Conteudo |
| ----- | -------- |
| **Mede** | Bucket tematico de trabalho para uma janela de calendario |
| **Range** | S0 burst-de-confianca ate S6 (ver doc de sprints) |
| **Racional** | Kanban "Selected / In progress" sem substituir tags H |
| **Objetivo** | Alinhar sessoes a uma narrativa |
| **Aplicabilidade** | [SPRINTS_AND_MILESTONES.md](SPRINTS_AND_MILESTONES.md) |
| **Fonte canonica** | Idem |
| **Ortogonalidade** | **S2a** pode conter issues mistos de **P1** e **P2** |

---

### Eixo: Milestones (M-*)

| Campo | Conteudo |
| ----- | -------- |
| **Mede** | Entregavel com criterio de "pronto" explicito |
| **Range** | M-OBS, M-MOBILE-V1, M-MATURITY-POC, etc. |
| **Racional** | Linguagem de stakeholder distinta de linhas de plano |
| **Objetivo** | Checkpoints de release e demo |
| **Aplicabilidade** | Doc de sprints, bullets de integracao do PLANS_TODO |
| **Fonte canonica** | [SPRINTS_AND_MILESTONES.md](SPRINTS_AND_MILESTONES.md) |
| **Ortogonalidade** | Milestones abrangem multiplos horizontes **H** |

---

### Eixo: Severidade CodeQL (P0/P1/P2 em SAST)

| Campo | Conteudo |
| ----- | -------- |
| **Mede** | Severidade de achado de analise estatica no mundo CodeQL |
| **Range** | P0/P1/P2 per regra codeql-priority-matrix |
| **Racional** | Vocabulario do scanner de seguranca != labels de issue GitHub |
| **Objetivo** | Evitar falso "tudo e P0" no chat |
| **Aplicabilidade** | CI CodeQL, SECURITY.md |
| **Fonte canonica** | `.cursor/rules/codeql-priority-matrix.mdc`, [SECURITY.md](../SECURITY.md) |
| **Ortogonalidade** | Sempre dizer "CodeQL P1" vs "issue P1" |

---

## To-do

| # | Item | Status |
| - | ---- | ------ |
| 1 | Publicar hub EN + este espelho | ✅ Feito |
| 2 | Link em [OPERATOR_AGENT_COLD_START_LADDER.md](../ops/OPERATOR_AGENT_COLD_START_LADDER.md) | ✅ Feito |
| 3 | Cross-link DOCS_AND_HUBS_INDEX (#571) quando disponivel | ⬜ Pendente |
