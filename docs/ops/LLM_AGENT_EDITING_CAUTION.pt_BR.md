# Cautela: edição assistida por LLM (agentes no IDE e chat do fornecedor)

**English (canonical):** [LLM_AGENT_EDITING_CAUTION.md](LLM_AGENT_EDITING_CAUTION.md)

## Objetivo

O Data Boar já inclui **regras** Cursor, **skills**, **palavras-chave** de sessão, **pre-commit**, `**check-all`** e runbooks de laboratório. Isso **reduz** risco — **não** elimina os modos de falha de **LLMs generativas** quando mexem em scripts **validados** e **de alto risco** (por exemplo orquestradores **PowerShell** longos para benchmark em lab).

Esta página é um **aviso público curto** para mantenedores e colaboradores. O **registo completo** (capturas, export de chat, âncoras de branch/commit e narrativa justa) fica só em `**docs/private/`** na estação do operador — ver `**docs/private/ops/INCIDENT_VENDOR_CHAT_ORCHESTRATION_MISMATCH_2026-04-28_29.pt_BR.md**` (gitignored do GitHub; **não** colar esse caminho em **issues** ou **PRs** com segredos).

**Contraste com o produto entregue:** Sinais de sensibilidade e inventário no Data Boar seguem caminho **determinístico + supervisionado** (regex, ML/DL com sementes fixas, relatórios estruturados) — veja [TECH_GUIDE.pt_BR.md](../TECH_GUIDE.pt_BR.md#detection-stack-vs-generative-llms), [COMPLIANCE_FRAMEWORKS.pt_BR.md](../COMPLIANCE_FRAMEWORKS.pt_BR.md#detecção-determinística-vs-hype-de-llm-generativo) e [GLOSSARY.pt_BR.md](../GLOSSARY.pt_BR.md) §8–9.

## O que correu de errado (padrão genérico)

- O operador pediu **fidelidade literal (*as-is*)** a um script já revisto, incluindo **comentários de auditoria / cadeia de custódia** e linhas de prova deliberadas.
- Um **LLM de chat web do fornecedor** (exemplo: **Google Gemini**) produziu **várias variantes renomeadas** em vez de um único arquivo fiel, moveu blocos e alterou caminhos (por exemplo diretórios de export a oscilar entre uma **árvore privada de relatórios** e uma pasta genérica `**out/`**).
- A recuperação exigiu **restaurar desde backup** conhecido, `git add` em massa e **commit** com mensagem **forte** para o custo aparecer no `**git log`**.
- Em paralelo, o mesmo produto pode **anunciar “memória”** no marketing enquanto, num fio longo, alterna entre **“não há log literal”**, **autodescrições dramáticas**, **alucinações confiantes sobre o estado do repositório** e uma **recusa** honesta — tudo isso são **sinais úteis de teste de stress**, não um caso jurídico.

## Hype vs realidade de engenharia

| Narrativa pública                                                        | Verdade de engenharia                                                                                                                                                                                                                                                                                                                                                                                                           |
| ------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| “Memória persistente” / “adapta ao histórico” (imprensa e UX do produto) | Melhora **continuidade** em muitas tarefas; **não** garante **replay literal** das respostas do assistente, trilhos auditáveis nem ausência de **recusas de política**. Artigo de terceiros (resumo): [MSN / PCGuia sobre “memória” do Gemini](https://www.msn.com/pt-pt/noticias/other/gemini-passa-a-ter-mem%C3%B3ria-e-vai-conseguir-adaptar-as-respostas-tendo-em-conta-o-hist%C3%B3rico-das-nossas-conversas/ar-AA2219Hk). |
| Modos “Raciocínio” / “Pro”                                               | Podem mudar tom e estrutura; **não** removem risco de alucinação nem substituem **CI + diff humano**.                                                                                                                                                                                                                                                                                                                           |
| **AGENTS.md** forte + regras + skills neste repositório                  | Guardrails **necessários**; **não suficientes** se a sessão saltar `**git diff`**, `**check-all**` ou **âmbito** explícito (“mexer só nestas linhas”).                                                                                                                                                                                                                                                                          |
## Onde LLMs ainda ajudam

- Brainstorm de **interfaces**, **mensagens de erro** e **estrutura de docs** quando o operador trata a saída como **rascunho**.
- **Pesquisa e navegação** numa árvore grande quando o resultado é verificado contra **código** e **testes**.
- **Resumos** de especificações públicas — sempre cruzar com a fonte primária.

## Onde LLMs começam a atrapalhar

- **Editar** arquivos que são **contratos**: orquestradores, parsers de manifesto, tudo o que deva ficar **bit-a-bit** igual salvo diff humano cirúrgico.
- **Inventar** “o que correu ontem” sem `**git`**, **artefatos de CI** ou **relatórios de lab** em `**docs/private/homelab/reports/`**.
- **Fundir** prosa emocionalmente carregada do chat com **verdade de engenharia** sem evidência.

## Mitigações práticas (checklist público)

1. **Separar canais:** chat do fornecedor para exploração; **agente Cursor + PR** para código que entra no `**main`**.
2. **Preâmbulo de sessão** para arquivos sensíveis: listar caminhos permitidos; proibir refactor; preservar comentários de auditoria.
3. **Preferir scripts do repo** (`check-all`, `preview-commit`, `commit-or-pr`) — ver **[TOKEN_AWARE_SCRIPTS_HUB.pt_BR.md](TOKEN_AWARE_SCRIPTS_HUB.pt_BR.md)**.
4. **Exportar** fios longos do fornecedor para `**docs/private/`** quando houver decisões que possas precisar auditar depois.
5. Ler **[GEMINI_PUBLIC_BUNDLE_REVIEW.pt_BR.md](GEMINI_PUBLIC_BUNDLE_REVIEW.pt_BR.md)** quando o trabalho for “Gemini revê **só caminhos já públicos**” — postura diferente de edição ao vivo do repo.

## Ligações

- **Mapa de políticas:** [CURSOR_AGENT_POLICY_HUB.pt_BR.md](CURSOR_AGENT_POLICY_HUB.pt_BR.md)
- **Contrato de orquestração de lab:** [LAB_COMPLETAO_RUNBOOK.pt_BR.md](LAB_COMPLETAO_RUNBOOK.pt_BR.md), [COMPLETAO_OPERATOR_PROMPT_LIBRARY.pt_BR.md](COMPLETAO_OPERATOR_PROMPT_LIBRARY.pt_BR.md)
- **Glossário** (contraste ML/DL do produto vs LLM generativa): [GLOSSARY.pt_BR.md](../GLOSSARY.pt_BR.md) — linha **LLM**

