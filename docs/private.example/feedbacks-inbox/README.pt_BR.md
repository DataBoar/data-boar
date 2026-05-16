# Caixa de entrada de feedbacks de parceiro / cliente — modelo (rastreado)

**English:** [README.md](README.md)

**Esta pasta é versionada** só como **esboço de política**. **Não** coloque PDFs Corporate-Entity-C, exportações Gemini ou outros pacotes completos de revisão no Git.

## Onde ficam os arquivos (máquina do operador)

Crie **`docs/feedbacks, reviews, comments and criticism/`** na **raiz do repositório** (no mesmo nível que **`docs/`**). Esse caminho está no **`.gitignore`** — **não** fica embaixo de **`docs/private/`**.

- **Hábito:** coloque aí feedbacks de parceiros ou clientes (drops estilo WRB, análises Corporate-Entity-C, exportações **Gemini**, revisão **externa Claude** (ex.: Sonnet, várias personas) — o que **não** deve ir para o `origin`).
- **Conclusões destiladas** e IDs ficam em **planos** ou notas em **`docs/ops/`** depois de redigir — **nunca** cole tabelas confidenciais completas em **issues**, **corpos de PR** nem em Markdown público.

### Issues no GitHub (rastreador opcional)

Você pode **abrir issues** a partir de um lote de revisão para o trabalho aparecer no **`origin`**. Mantenha o corpo da issue **enxuto** (título + uma linha de ponteiro + checklist opcional). **Postura:** a revisão é **recomendação**, **não** manda no merge — igual às rondas **Gemini**: triar cada item como **feito**, **adiado** (com link no plano ou data), **não faremos** (motivo curto) ou **já atendido**, e fechar ou comentar. **Agente + mantenedor** decidem; não tratar saída de LLM de terceiro como gate obrigatório por defeito.

## Espelho opcional (Git privado empilhado)

Se você usa um repositório **aninhado** em **`docs/private/`**, pode também manter comprovantes em **`docs/private/feedbacks_and_reviews/`** e commitar conforme **`docs/ops/PRIVATE_LOCAL_VERSIONING.pt_BR.md`** — ainda assim **nunca** envie esses arquivos para o remoto **do produto** no GitHub.

## Agentes (Cursor)

Quando o operador usar o token de sessão **`feedback-inbox`**, os assistentes fazem **`read_file`** / listam primeiro a pasta gitignored de drops. Se estiver **vazia**, diga isso. Se a **origem** (Corporate-Entity-C vs Gemini vs **Claude externo** vs outra) não estiver clara, **pergunte** antes de atribuir linhas em **`docs/plans/`** ou **`PLANS_TODO.md`**. Se o operador **já disse** a fonte na conversa, use esse rótulo.

## Ver também

- **[PRIVATE_OPERATOR_NOTES.pt_BR.md](../../PRIVATE_OPERATOR_NOTES.pt_BR.md)** — caminho de feedback vs `docs/private/`.
- **`.cursor/rules/session-mode-keywords.mdc`** — linha **`feedback-inbox`**.
