# Captura de sessão do operador — transformar chat em nota durável

**English:** [OPERATOR_SESSION_CAPTURE_GUIDE.md](OPERATOR_SESSION_CAPTURE_GUIDE.md)

**Objetivo:** Quando você e o assistente **alinham** estratégia, política, ferramentas ou próximos passos no chat, threads **de valor** merecem um **artefato pequeno e durável** para **reabrir**, **ensinar o você futuro** ou **virar plano** — sem encher docs rastreados nem vazar fato sensível.

**Não substitui:** [PLANS_TODO.md](../plans/PLANS_TODO.md), notas de release nem ADR. É **higiene de memória do operador**.

---

## 1. O que vale capturar

| Vale a pena                                                                       | Costuma pular                                           |
| -----------                                                                       | -------------                                           |
| Decisões (“Slack antes do Signal, depois os dois”)                                | Transcrição inteira do chat                             |
| **Política** nova (onde ficam dumps de CLI, `commercial` vs `operator_economics`) | Senhas, tokens, `last`/`w` cru em arquivo **rastreado** |
| Ponteiros (“GitHub Mobile = canal A; Cursor mobile = ressalvas”)                  | Erro de digitação pontual, duplicata de linha do plano  |
| Enquadramento ético / carreira para reler                                         | O que é só de **jurídico** ou RH                        |
| “Combinamos pasta X para Y”                                                       | Texto longo que só repete `AGENTS.md`                   |

---

## 2. Onde gravar (sensibilidade)

| Sensibilidade                                     | Onde                                                      | Exemplos                                                                                 |
| -------------                                     | ----                                                      | --------                                                                                 |
| **Público / equipe**                              | `docs/` rastreado (EN + pt-BR quando for doc de operador) | Este guia, canais de notificação, tabela do `PRIVATE_OPERATOR_NOTES`                     |
| **Produto + roadmap**                             | `docs/plans/`, `PLANS_TODO`                               | Novo `PLAN_*.md` quando a ideia virar entrega **escopada**                               |
| **Pessoal, estratégia, família, números de OPEX** | Só **`docs/private/`**                                    | Ética acadêmica, tabela de luz, rascunho de proposta por cliente                         |
| **LAN, hábitos, IPs, dumps de sessão**            | **`docs/private/homelab/`** (ex. `reports/`)              | `uptime`, `last`, `lastlog` — ver [PRIVATE_OPERATOR_NOTES.md](PRIVATE_OPERATOR_NOTES.md) |

**Regra prática:** se perder a nota **prejudica carreira ou compliance** e **não** pode ir ao GitHub → **`docs/private/`** com arquivo ou seção **datada**.

---

## 3. Layout privado sugerido (índice opcional)

Manter um **índice leve** para achar depois:

- **`docs/private/author_info/RECENT_OPERATOR_SYNC_INDEX.pt_BR.md`** (ou nome parecido) — **lista com datas** e **links para outros arquivos private** (caminhos relativos).
- **Um tópico = poucos bullets**, não um romance.

Ponteiro rastreado: **`docs/private.example/author_info/README.md`**.

---

## 4. Comportamento do assistente

Quando o operador pedir para **“salvar para depois”**, **“documentar o que combinamos”** ou **“capturar a sessão”**:

1. **Classificar** cada item: política rastreada vs plano vs **só private**.
1. **Atualizar** o menor conjunto de arquivos (preferir **uma** nota private + **opcional** um link rastreado).
1. **Nunca** commitar IPs LAN, hostnames, nomes de familiares ligados a instituição, nem números comerciais — só **private** ou redigido.
1. Se a ideia virar **fatia de produto**, sugerir linha no **`PLANS_TODO`** ou plano dedicado **à parte** (não misturar tudo num dump gigante).

Cursor: **`.cursor/rules/operator-session-capture.mdc`** e **`.cursor/skills/operator-session-capture/SKILL.md`**.

---

## 5. Documentos relacionados

- [PRIVATE_LOCAL_VERSIONING.pt_BR.md](PRIVATE_LOCAL_VERSIONING.pt_BR.md) — Git aninhado opcional em `docs/private/` (histórico local, sem GitHub).
- [PRIVATE_OPERATOR_NOTES.md](PRIVATE_OPERATOR_NOTES.md) — árvore private, artefatos de hábito CLI.
- [OPERATOR_NOTIFICATION_CHANNELS.md](OPERATOR_NOTIFICATION_CHANNELS.md) — Slack + Signal em fases.
- [TOKEN_AWARE_USAGE.md](../plans/TOKEN_AWARE_USAGE.md) — escopo de sessão vs trabalho de plano.
- [AGENTS.md](../../AGENTS.md) — confidencialidade e scripts de automação.
