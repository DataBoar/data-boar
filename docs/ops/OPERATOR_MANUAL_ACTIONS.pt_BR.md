# Ações manuais do operador (evidências, homelab, estudo)

**Finalidade:** Um único documento rastreado para o **seu** trabalho que o agente não faz sozinho: capturar evidências, passos de homelab, fotos/saídas para contexto e **como** janelas de estudo/certificação convivem com readiness de produção. Sem segredos aqui—conteúdo sensível em **`docs/private/`** (gitignored).

**English:** [OPERATOR_MANUAL_ACTIONS.md](OPERATOR_MANUAL_ACTIONS.md)

---

## 1. Janela de estudo e certificação (2026)

- **Foco principal:** **Cyber pago (CWL)** — concluir **BTF** → **C3SA** e a lista §3.2 em [PORTFOLIO_AND_EVIDENCE_SOURCES.md](../plans/PORTFOLIO_AND_EVIDENCE_SOURCES.md); **prova para stakeholders** = esses certificados + **Data Boar entregue** + narrativa de compliance. O dia a dia no IDE pode **não** ser Claude; estudo Anthropic **não** é a prioridade máxima **deste** trilho de produto.
- **Alternando no ano:** **Anthropic Academy** (grátis; [Anthropic courses](https://docs.claude.com/en/docs/resources/courses)) — sequência no PORTFOLIO §3.0 quando couberem blocos de IA. **CCA** depois, quando elegível; página CCA no Skilljar + [guia](https://aitoolsclub.com/how-to-become-a-claude-certified-architect-complete-guide/) não oficial.
- **Em paralelo (fio fino):** **Faixa prioritária A** (Dependabot, Docker Scout, `check-all`)—[PLANS_TODO.md](../plans/PLANS_TODO.md) **–1** / **–1b**.
- **Opcional:** certificados de conclusão **terceiros** para CV — não são exames oficiais do fornecedor.
- **Se CCA não passar:** anotações em `docs/private/`; **nova tentativa** depois.

O racional de sequência também está em [SPRINTS_AND_MILESTONES.pt_BR.md](../plans/SPRINTS_AND_MILESTONES.pt_BR.md) §3.1 e [PORTFOLIO_AND_EVIDENCE_SOURCES.md](../plans/PORTFOLIO_AND_EVIDENCE_SOURCES.md) §3.0.

**Ritmo semanal (sugestão):** **2** blocos **CWL** + **1** **IA**; na semana seguinte **2** CWL + **1** **outro** (tese, LGPD, nota de homelab); repetir o ciclo. Aliviar quando **faixa A** (–1/–1b) ou release apertar—ver §4.

**Cursor / agente:** O assistente pode lembrar **em poucas linhas** o combinado de estudo em **pontos naturais** (fatia pronta, fim de sessão)—ver **`.cursor/rules/study-cadence-reminders.mdc`**. Para **recap na hora** no chat, digite o token em inglês **`study-check`** (ver **`.cursor/rules/session-mode-keywords.mdc`**).

### O que ajuda o agente em **faixa A** e **homelab**

| Tema          | O que passar (sem segredo no chat—só status ou caminho em `docs/private/`)                                                                                            |
| ----          | ---------------------------------------------------------------------------                                                                                           |
| **A1**        | Dependabot / Security: **quantos alertas abertos** ou “triagem esta semana sim/não”.                                                                                  |
| **A2**        | Docker Scout / imagem: **CVE que te preocupa** ou “rebuild feito / pendente”.                                                                                         |
| **A3**        | Hub / tags: **uma linha** (só operador).                                                                                                                              |
| **–1L**       | **Qual linha** da matriz §9 do [HOMELAB_VALIDATION](HOMELAB_VALIDATION.pt_BR.md); §1–§2 **feito / bloqueado**; saídas em `docs/private/` se quiser que o agente leia. |
| **Bloqueios** | Ex.: “segundo host só depois de data X”—evita plano errado.                                                                                                           |

---

## 2. Evidências que você pode juntar para o agente (manual)

**Não** colar senhas ou chaves privadas no chat. Prefira:

| Ação                                                            | Onde guardar                                                                                             | Por quê                            |
| ----                                                            | ------------                                                                                             | -------                            |
| Inventário de homelab (hosts, papéis, IPs redigidos se preciso) | `docs/private/homelab/` conforme [PRIVATE_OPERATOR_NOTES.md](../PRIVATE_OPERATOR_NOTES.md)               | O agente pode `read_file` sem `@`. |
| Fotos de equipamento, rack, etiquetas (opcional)                | Mesma árvore privada; descrever num `.md` o que cada imagem mostra                                       | Contexto visual para topologia.    |
| Saídas de CLI (`ssh`, `curl`, resumos de scan)                  | Colar numa nota datada em `docs/private/` ou log de sessão                                               | Depuração reproduzível.            |
| Conclusão de curso / certificado                                | PDF ou screenshot em `docs/private/`; acrescentar linha no PORTFOLIO §3 quando quiser no narrative de CV | Alinha tese/pitch.                 |

---

## 3. Homelab e validação

- **Critérios:** [HOMELAB_VALIDATION.pt_BR.md](HOMELAB_VALIDATION.pt_BR.md) §1–§12 ([EN](HOMELAB_VALIDATION.md)).
- **O que o agente pode fazer:** Sugerir comandos, ler docs **rastreados**, ler **`docs/private/`** quando você mantém—**não** SSH sozinho sem o seu terminal.
- **Snapshot para o chat:** Manter **`docs/private/WHAT_TO_SHARE_WITH_AGENT.md`** atualizado (não versionado). Layout e dicas: [PRIVATE_OPERATOR_NOTES.pt_BR.md](../PRIVATE_OPERATOR_NOTES.pt_BR.md), [docs/private.example/author_info/README.md](../private.example/author_info/README.md).

---

## Ver também

- [OPERATOR_NEXT_DAY_CHECKLIST.pt_BR.md](OPERATOR_NEXT_DAY_CHECKLIST.pt_BR.md) ([EN](OPERATOR_NEXT_DAY_CHECKLIST.md)) — sugestão de **dia inteiro** (homelab + banda A + –1L + Corporate-Entity-C opcional)
- [SPRINTS_AND_MILESTONES.pt_BR.md](../plans/SPRINTS_AND_MILESTONES.pt_BR.md) §3.1 — faixa de estudo no quadro de sprints
- [TOKEN_AWARE_USAGE.md](../plans/TOKEN_AWARE_USAGE.md) — disciplina estudo vs código no mesmo dia (doc EN; parcial pt-BR onde existir)
- [OPERATOR_LAB_DOCUMENT_MAP.pt_BR.md](OPERATOR_LAB_DOCUMENT_MAP.pt_BR.md) — onde cada doc de lab mora
