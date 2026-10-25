---
name: operator-dialogue-pt-br
description: When the operator chats in Portuguese, the assistant uses Brazilian Portuguese (pt-BR) in replies—same bar as docs-locale-pt-br-contract and docs-pt-br-locale—not European Portuguese; English is fine for commands, brands, and technical jargon.
---

# Operator dialogue: pt-BR + English jargon

Use this skill when you want the assistant to **stick to the project’s Portuguese norm** in **chat** without repeating instructions each session.

## What to expect

- **Portuguese:** **Brazilian (pt-BR)** only in prose — aligned with **`.cursor/rules/docs-locale-pt-br-contract.mdc`** (always) and **`.cursor/rules/docs-pt-br-locale.mdc`** / **`*.pt_BR.md`** (no *ficheiro*, *partilhar*, *secção*, *utilizador*, *tem de*, etc.).
- **English:** Keep **commands**, **CLI/API identifiers**, **tool and brand names**, and **jargon** in English when natural (same habit as in tracked docs).
- **Rule (always on):** **`.cursor/rules/operator-chat-language-pt-br.mdc`** (`alwaysApply: true`).

## Related

- **`.cursor/rules/docs-locale-pt-br-contract.mdc`** — non-negotiable default + exceptions (always applied).
- **`.cursor/rules/docs-pt-br-locale.mdc`** — preference table + link to **`tests/test_docs_pt_br_locale.py`** for committed Markdown.
- **`AGENTS.md`** — chat language + when to run the locale test after doc edits.
