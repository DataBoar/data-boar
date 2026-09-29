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
| Follow-up WRB (janela de token) | [GitHub issue #189](https://github.com/DataBoar/data-boar/issues/189) | Retomar agora o ciclo de revisão externa com token disponível |
| Checklist diário datado | [README.pt_BR.md](README.pt_BR.md) + `OPERATOR_TODAY_MODE_YYYY-MM-DD.md` | Foco do dia e fechamento |
| Alinhamento de publish | [PUBLISHED_SYNC.pt_BR.md](PUBLISHED_SYNC.pt_BR.md) | Versão no repo vs GitHub Release vs Docker Hub |
| Ritmo/lembretes privados | `docs/private/TODAY_MODE_CARRYOVER_AND_FOUNDER_RHYTHM.md` | Lembretes e cadência do operador |
| Carryover editorial social | `docs/private/social_drafts/editorial/SOCIAL_HUB.md` | Linhas de posts planejados/adiados/publicados |

---

## 2) Snapshot atual do workboard (curto, manual)

Atualize esta seção com bullets curtos. Detalhes ficam nas fontes canônicas acima.

**Última atualização:** **2026-09-28** · Today: [OPERATOR_TODAY_MODE_2026-09-28.pt_BR.md](OPERATOR_TODAY_MODE_2026-09-28.pt_BR.md)

- **Agora (top 1):** **Validação BFF / GA** — **[#1980](https://github.com/DataBoar/data-boar/issues/1980)** com fechamento **maestro#82/#91** e **carrion-crow #99** na fila do operador.
- **Próximos (top 3):**
  - Fechar **maestro#91** (**data-boar#2011** mergeado); smoke no host de lab opcional ([#756](https://github.com/DataBoar/data-boar/issues/756)).
  - Merge **carrion-crow #99**, depois lote segurança **#94–#101**.
  - Um PR **Dependabot** (**#1999** / **#1998** primeiro).
- **Bloqueios:**
  - Imagens podman do smoke no lab (limpeza **27/set**; [#756](https://github.com/DataBoar/data-boar/issues/756)).
  - **maestro#82** ainda aberto com RC/segurança já no `main`.
- **Adiado:** espelho `engine/` RC no maestro — sem data (operador **28/set**).

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
