# Hub de planos — navegação para colaboradores

**English:** [PLANS_HUB.md](PLANS_HUB.md)

**Finalidade:** Página-índice para **candidatos, colaboradores e revisores** entenderem rapidamente **todos os arquivos `PLAN_*.md`** (abertos e arquivados), com **resumo** e **referências cruzadas** opcionais. O **conteúdo canônico da tabela** (nomes de arquivo e textos extraídos dos planos em inglês) fica no arquivo em **inglês**; este arquivo em **pt-BR** resume o fluxo em português.

## Leia também:

- **[PLANS_TODO.md](PLANS_TODO.md)** — fila e estado (fonte única de verdade para to-dos).
- **[SPRINTS_AND_MILESTONES.pt_BR.md](SPRINTS_AND_MILESTONES.pt_BR.md)** — temas de sprint e marcos (par EN + pt-BR); subseção **Compor marcos** (mapa de ciclo de vida) alinha combinações de **M-*** a narrativa vs postura comercial/automação.

**Atualizar a tabela** depois de criar, renomear ou arquivar um `PLAN_*.md`:

```bash
python scripts/plans_hub_sync.py --write
```

**Dicas opcionais dentro do plano** (comentários HTML no corpo do `.md`, em inglês):

```html
<!-- plans-hub-summary: Uma linha curta para humanos. -->
<!-- plans-hub-related: PLAN_OUTRO.md, completed/PLAN_VELHO.md -->
```

**Tabela completa:** abra **[PLANS_HUB.md](PLANS_HUB.md)** (Markdown Preview recomendado para linhas largas).

**Snapshot PMO (2026-07-12):** trust-floor do post4 fechado com merge das issues **#1194 #1195 #1201 #1202 #1137 #1198 #1130** via PRs **#1203–#1209** e **#1214**; follow-ups **#1210** (merge-secrets), **#1211** (integrity fail-open) e **#1212** (GRACE) estão na fila de open issues em **PLANS_TODO**.

**Documentos meta** (papéis): ver a seção *Meta documents* no **PLANS_HUB.md** em inglês.

**Narrativa de posicionamento (sem valor jurídico):** metáfora **data soup** + ingredientes “esquecidos” e descoberta **opt-in** empilhada — ver parágrafo **Positioning narrative** no [PLANS_HUB.md](PLANS_HUB.md) e bullet correspondente em [PLANS_TODO.md](PLANS_TODO.md) (**Integration / active threads**).

**Ver também:** [README.md](../README.md) (índice, **Interno e referência**), [CONTRIBUTING.md](../../CONTRIBUTING.pt_BR.md), [AGENTS.md](../../AGENTS.md).
