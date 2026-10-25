# Docs privados LAB-OP — pares inglês + português do Brasil

**English:** [I18N_LAB_OP.md](I18N_LAB_OP.md)

Ao manter **`docs/private/homelab/`** (gitignored), prefira **dois arquivos por tema** quando houver texto narrativo:

| Padrão              | Papel                                                                                                |
| ------              | -----                                                                                                |
| **`Nome.md`**       | **Inglês** — útil para colaboradores internacionais, páginas com **Mermaid**, ou **resumos** índice. |
| **`Nome.pt_BR.md`** | **Português brasileiro (pt-BR)** — não pt-PT; ver **`.cursor/rules/docs-pt-br-locale.mdc`**.         |

## Exceções / pragmatismo

- **`LAB_SECURITY_POSTURE`:** **`LAB_SECURITY_POSTURE.pt_BR.md`** guarda a **evidência completa** (longo). **`LAB_SECURITY_POSTURE.md`** é um **índice EN** curto apontando para o pt-BR — evita duplicar 900+ linhas até valer traduzir tudo para EN.
- **`iso-inventory`:** **`iso-inventory.md`** mantém a lista **`find`**; **`iso-inventory.pt_BR.md`** espelha layout + política em pt-BR e pede para **sincronizar** a lista com o EN.
- **Matrizes grandes:** **`LAB_SOFTWARE_INVENTORY.pt_BR.md`** pode ser **resumo estruturado** com a **tabela completa** no EN — menos drift.

## Automação

O teste **`tests/test_docs_pt_br_locale.py`** percorre **todos** os **`*.pt_BR.md`** do repositório (só ignora **`.venv`** e **`node_modules`**), **incluindo** **`docs/private/**`** quando existir no clone — mesmo critério do lint de Markdown para notas do operador. Evite colar **pt-PT** no texto; use **`.cursor/rules/docs-pt-br-locale.mdc`**.

## Modelos

**`OPERATOR_RETEACH.md`** + **`OPERATOR_RETEACH.pt_BR.md`** em **`private.example/homelab/`** (só placeholders).
