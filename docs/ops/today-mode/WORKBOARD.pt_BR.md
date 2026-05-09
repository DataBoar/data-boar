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
| Checklist diário datado | [README.pt_BR.md](README.pt_BR.md) + `OPERATOR_TODAY_MODE_YYYY-MM-DD.md` | Foco do dia e fechamento |
| Alinhamento de publish | [PUBLISHED_SYNC.pt_BR.md](PUBLISHED_SYNC.pt_BR.md) | Versão no repo vs GitHub Release vs Docker Hub |
| Ritmo/lembretes privados | `docs/private/TODAY_MODE_CARRYOVER_AND_FOUNDER_RHYTHM.md` | Lembretes e cadência do operador |
| Carryover editorial social | `docs/private/social_drafts/editorial/SOCIAL_HUB.md` | Linhas de posts planejados/adiados/publicados |

---

## 2) Snapshot atual do workboard (curto, manual)

Atualize esta seção com bullets curtos. Detalhes ficam nas fontes canônicas acima.

- **Agora (top 1):** checkpoint `S2a` de transporte + confiança no `PLANS_TODO`.
- **Próximos (top 3):**
  - `-1L` passada de prova em homelab quando houver janela.
  - Continuar fatias priorizadas de confiança/comercial após `S2a`.
  - Manter a fila de carryover limpa (`CARRYOVER.pt_BR.md`).
- **Bloqueios:** uma linha por bloqueio com link para o doc dono.
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
