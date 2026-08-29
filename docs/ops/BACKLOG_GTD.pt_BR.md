# Backlog como GTD (issue GitHub é o barramento)

**English:** [BACKLOG_GTD.md](BACKLOG_GTD.md)

Página curta de operador. Não é app novo. A issue continua o barramento AIIDCOBPP.

**Também:** [GITHUB_ISSUE_CANONICAL_AND_DUPLICATE_CLOSE.pt_BR.md](GITHUB_ISSUE_CANONICAL_AND_DUPLICATE_CLOSE.pt_BR.md) (como fechar), [ISSUE_QUEUE_SEQUENCING_MAP.md](ISSUE_QUEUE_SEQUENCING_MAP.md) (espelho — milestone no GitHub é a fonte).

## Cinco baldes

| GTD | Aqui | Regra dura |
| --- | --- | --- |
| **Inbox** | Issue aberta **sem milestone e sem label `P*`** | Não é sprint. Processar em ≤7 dias ou é esqueleto. |
| **Next** | Milestone `v1.8.0` + P0/P1 (P2 só com PLAN/AC) | Se não cabe na cabeça de uma pessoa (~30), o marco mente. |
| **Waiting** | Texto de blocker com `#N` **ainda open** | Se `#N` já fechou, `NÃO INICIAR` stale é hygiene — não é aresta viva. |
| **Someday** | Milestone `backlog`, ou labels `proposta-de-plan` / `no-code-yet` | Lab (Growatt, Slack, curso) mora aqui. Nunca conta como v1.8.0. |
| **Done** | `closed` + motivo explícito | `completed` = artefato (PR/path). `not_planned` = recusa honesta. `duplicate` usa `duplicate_of`. |

`[P2]` no **título** não substitui label. Filtro e agente leem label.

Abrir issue é **capture**. Sair da Inbox pede comentário de processamento:

```text
Inbox → ?
- Outcome: …
- Next physical: PR | PLAN | só comentário | close
- Bucket: v1.8.0 | v1.8.1 | backlog | not_planned
- Label P = Pn do título
- Done looks like: …
```

## Anti-esqueleto / anti-done-acidental

1. Fechar só com evidência no comentário (`via #PR`, path na árvore, ou `not_planned: lab, não produto`).
2. Não fechar P0/P1/bug no mesmo sweep de P3 docs.
3. Stale ≠ done. 90 dias + sem marco + P3 → comentário `stale-review`, depois `not_planned` ou `backlog`. Sem bot mudo neste barramento.
4. Agente não fecha porque o body “parece shipped”. HITL ou checklist com path do artefato.
5. Regenerar `ISSUE_QUEUE_SEQUENCING_MAP.md` no **mesmo PR** que fecha um grupo de hygiene. Mapa velho é esqueleto.
6. Eixos na prática: **label `Pn` + milestone**. Eixo U (ADR-0061) só no Next, ou para de fingir.

## Revisão semanal (30–45 min)

Não é houseclean de sábado.

1. Inbox: `is:issue is:open no:milestone` — processar ou recusar.
2. Waiting: blocker já fechou? Limpar texto ou desbloquear.
3. Next `v1.8.0`: ainda cabe? Empurra P3 sobrando para `backlog`.
4. Closed nos últimos 7d sem `via #PR` — reabrir se o close foi acidental.
5. Regenerar o mapa — um comando, um commit.

Houseclean estilo E–H é revisão **trimestral**. O modo do dia é Next + Inbox.

## Não fazer

- Carimbar `backlog` em tudo para “não ficar sem marco” — isso esconde Inbox.
- Quatro fontes (título, label, Projects, mapa). Label P + milestone; o mapa deriva.
- Abrir issue meta “implantar GTD.”
