# Workboard do operador (backlog + carryover + lembretes)

**English:** [WORKBOARD.md](WORKBOARD.md)

**Objetivo:** oferecer um cockpit único para o trabalho ativo sem criar segunda fonte de verdade. Este arquivo é uma **camada de roteamento**: aponta para docs canônicos e registra só resumos curtos de "agora/próximo".

---

## 1) Fontes canônicas (sem duplicação)

| Tema | Fonte de verdade | Uso principal |
| ---- | ---------------- | ------------- |
| Backlog de produto e sequência | [../../plans/PLANS_TODO.md](../../plans/PLANS_TODO.md) | Ordem de prioridade, dependências e linhas ativas |
| Índice/mapa de planos | [../../plans/PLANS_HUB.md](../../plans/PLANS_HUB.md) | Busca rápida de arquivos `PLAN_*.md` |
| Visão de sprint e marcos | [../../plans/SPRINTS_AND_MILESTONES.pt_BR.md](../../plans/SPRINTS_AND_MILESTONES.pt_BR.md) | Sequência por tema e semântica dos marcos |
| Fila viva de carryover | [CARRYOVER.pt_BR.md](CARRYOVER.pt_BR.md) | Itens abertos que atravessam dias/blocos |
| Follow-up WRB (janela de token) | [GitHub issue #189](https://github.com/FabioLeitao/data-boar/issues/189) | Retomar agora o ciclo de revisão externa com token disponível |
| Checklist diário datado | [README.pt_BR.md](README.pt_BR.md) + `OPERATOR_TODAY_MODE_YYYY-MM-DD.md` | Foco do dia e fechamento |
| Alinhamento de publish | [PUBLISHED_SYNC.pt_BR.md](PUBLISHED_SYNC.pt_BR.md) | Versão no repo vs GitHub Release vs Docker Hub |
| Ritmo/lembretes privados | `docs/private/TODAY_MODE_CARRYOVER_AND_FOUNDER_RHYTHM.md` | Lembretes e cadência do operador |
| Carryover editorial social | `docs/private/social_drafts/editorial/SOCIAL_HUB.md` | Linhas de posts planejados/adiados/publicados |

---

## 2) Snapshot atual do workboard (curto, manual)

Atualize esta seção com bullets curtos. Detalhes ficam nas fontes canônicas acima.

- **Agora (top 1):** `S2a` transporte + confiança (Fase 7 + fatia de trust-state alinhada com `#86`) está selecionado no `PLANS_TODO`.
- **Próximos (top 3):**
  - Fechar a trilha de carryover do `1.7.0` (`gh run list` no `main` + follow-up opcional de smoke `lab-op` no `CARRYOVER.md`).
  - Rodar a prova `-1L` de homelab / `benchmark-ab` quando houver janela de laboratório.
  - Enviar o follow-up WRB e triar os deltas da revisão externa para o `PLANS_TODO`.
- **Bloqueios:**
  - Janela de calendário/hardware do lab para executar `-1L` e `benchmark-ab` (`PLANS_TODO` + `CARRYOVER.md`).
  - Cadência externa de revisão para o follow-up WRB (ciclo no GitHub + espera de resposta).
- **Adiado com data:** manter data + dono em `CARRYOVER.pt_BR.md`.

---

## 3) Ritmo de uso

### Manhã (rápido)

1. Rodar `.\scripts\operator-day-ritual.ps1 -Mode Morning`.
2. Abrir o `OPERATOR_TODAY_MODE_YYYY-MM-DD.md` do dia.
3. Checar `CARRYOVER.pt_BR.md` e puxar só o que for realista.

### Durante o bloco

1. Manter este arquivo curto ("Agora", "Próximos", "Bloqueios").
2. Atualizar docs canônicos quando algum estado mudar.
3. Evitar narrativa longa aqui; este é um quadro operacional.

### Fim de bloco / fim de dia

1. Usar `block-close` (ou `eod-sync` quando for fechamento de calendário).
2. Levar pendências para `CARRYOVER.pt_BR.md` com próxima data.
3. Se houve publish, atualizar `PUBLISHED_SYNC.pt_BR.md`.

---

## 4) Política de edição

- Este arquivo pode resumir, mas não substitui:
  - `PLANS_TODO.md` para verdade de backlog,
  - `CARRYOVER.pt_BR.md` para fila entre dias,
  - `OPERATOR_TODAY_MODE_*.md` para execução diária.
- Preferir links em vez de copiar tabelas inteiras.
