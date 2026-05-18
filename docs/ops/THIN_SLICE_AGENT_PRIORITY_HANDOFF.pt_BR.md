# Fatias finas, faixas de prioridade e quando chamar o operador

**English:** [THIN_SLICE_AGENT_PRIORITY_HANDOFF.md](THIN_SLICE_AGENT_PRIORITY_HANDOFF.md)

**Objetivo:** Manter assistente e mantenedor alinhados ao reduzir issues do GitHub e linhas de plano em **PRs finos**, sem perder **disciplina de prioridade** nem repetir erros de **fechamento de duplicatas**.

**Relacionado:** [COMMIT_AND_PR.pt_BR.md](COMMIT_AND_PR.pt_BR.md) (subsecção *Fatias finas*), [PLANS_TODO.md](../plans/PLANS_TODO.md), **`.cursor/rules/execution-priority-and-pr-batching.mdc`**, **`.cursor/rules/git-pr-sync-before-advice.mdc`**. **Duplicatas (eco):** depois do merge do PR na issue **canônica** e CI verde, fechar o eco com **`gh issue close <eco> --duplicate-of <canonica>`** (ver `gh issue close --help`).

## Faixas de prioridade (títulos das issues)

1. Ler **`[P0]`**, **`[P1]`**, **`[P2]`**, **`[P3]`** (ou **`[decision][Pn]`**) no **título** quando existirem.
2. **Ordem:** **`P0` → `P1` → `P2` → `P3`**, depois **número da issue crescente** dentro da faixa quando dois itens conflitarem.
3. **Atualizar:** Novas issues de audit surgem — de quando em quando rodar **`gh issue list --state open --limit 200 --json number,title,createdAt`** e ajustar o **próximo slice** em **`PLANS_TODO.md`** se o início da fila mudou.

## Autonomia do assistente (mesma faixa)

- **Fazer:** Implementar **um recorte coerente** por grupo de commits; **`check-all`** / **`lint-only`** antes de integrar; **`Closes #NNN`** na issue **canônica**; merge + CI verde antes de **`gh issue close <eco> --duplicate-of <canonica>`** nos ecos.
- **Fazer:** Se o slice **A** estiver **bloqueado** (decisão de produto ambígua, evidência em falta, ambiente indisponível), deixar **ponteiro de retomada** claro — por exemplo **comentário na issue**, ou **uma linha** em **Integration / active threads** no **`PLANS_TODO.md`** — e seguir **B**, **C** na **mesma faixa** de prioridade apenas.
- **Não:** Cair para faixa **inferior** enquanto itens **acionáveis** persistirem numa faixa **mais alta** (sem bloqueio documentado). Quando isso acontecer — **parar e chamar o operador** (chat ou menção na issue): o que ficou na faixa mais alta é **mais importante** do que abrir **`P3`** antes da hora.
- **Não:** Usar “backlog” como desculpa silenciosa — ou **entrega**, ou **documenta o bloqueio**, ou **adiamento explícito** com ponteiro datado/numerado para retomar.

## Enquadramento PRD / readiness

**“Mais perto de PRD readiness”** aqui significa: superfícies de **operador** corretas (man pages, **`USAGE`**, docs de deploy), **CI verde**, sequenciamento **honesto** no **`PLANS_TODO.md`**, e **sem duplicatas órfãs** após merge. **Não** significa fechar todo **`P3`** antes de qualquer **`P2`** — respeitar as faixas acima.

## Checklist rápido (assistente)

1. Confirmar a **faixa** da issue na mão.
2. Se bloqueado — escrever **onde** retomar; escolher **próxima mesma faixa**.
3. Antes de começar trabalho **`P3`**, verificar **`P0–P2`** abertas — se alguma continua **acionável** sem handoff, **parar** e **chamar o operador**.
