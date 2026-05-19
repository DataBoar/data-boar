# Plano: G0-G3 gravity tier (gravidade intrinseca do achado)

<!-- plans-hub-summary: Eixo G0-G3 de gravidade de achados; ortogonal a U/H/P de execucao -->

**Status:** Ativo
**Date:** 2026-05-19
**Authors:** Fabio Leitao
**Priority:** H0

**Espelho (EN):** [PLAN_G_TIER.md](PLAN_G_TIER.md)

**Sincronizado com:** [PLANS_TODO.md](PLANS_TODO.md)

---

## Problema

O repo ja usa **H0-H5** (horizonte), **U0-U3** (urgencia), **A1-A7** (faixa A), **P0-P3** (labels GitHub), **S0-S6** (sprints) e **M-*** (milestones). Nenhum desses eixos responde: **quao grave e este achado se ficar em aberto?**

Sem um eixo de **gravidade**, um typo cosmético e um vazamento de PII / candidato a **Safe-Hold** parecem igualmente "pendentes" na fila.

---

## Definicao G0-G3 (canonica)

| Nivel | Nome | Criterio |
| ----- | ---- | -------- |
| **G0** | Negligivel | Cosmetico, typo, sem risco funcional ou de compliance |
| **G1** | Baixo | Melhoria, lacuna documental, sem exposicao direta |
| **G2** | Significativo | Lacuna funcional ou de compliance; exposicao potencial |
| **G3** | Critico | Breach de compliance, vazamento de PII, risco de IP, candidato a **Safe-Hold** |

---

## Ortogonalidade

| Eixo | Mede | Exemplo |
| ---- | ---- | ------- |
| **P0-P3** (label GitHub) | **Quando executar** o issue | Fazer antes do feature H3 X |
| **G0-G3** | **Dano intrinseco** se o achado permanecer | G3 com label P3 = critico mas nao urgente esta semana |
| **U0-U3** | **Pressao de prazo** | U0 seguranca agora vs U3 catalogo |
| **H0-H5** | **Horizonte de planejamento** | H0 agora vs H4 longo prazo |

**CodeQL P0/P1/P2** e mundo SAST separado — nao confundir com issue **P0** ou **G3** sem declarar o eixo.

---

## To-do

| # | Item | Status |
| - | ---- | ------ |
| 1 | Publicar este plano + linha em PLANS_TODO | ✅ Feito |
| 2 | Link cruzado em PLAN_TAXONOMY_AXES quando existir | ⬜ Pendente |
| 3 | ADR-0055 contrato anti-colisao (#573) | ⬜ Pendente |
