# Hub de regras e skills

**English (canonical tables):** [RULES_AND_SKILLS_HUB.md](RULES_AND_SKILLS_HUB.md)

> **Para agentes:** consulte o hub em inglês para tabelas atualizadas (nomes de arquivo e descrições técnicas permanecem em inglês). Use [session-mode-keywords.mdc](../../.cursor/rules/session-mode-keywords.mdc) para tokens de sessão. Regenerar: `uv run python scripts/build_rules_skills_hub.py --write`.

## Resumo

Runbooks só do operador ficam em **gitignored** `.cursor/private/skills/` (#1191).

- **Regras:** 72 arquivos `.mdc` (18 always-on, 54 situacionais).
- **Skills:** 26 pastas com `SKILL.md`.
- **Keywords de sessão:** 7 tokens em `session-mode-keywords.mdc`.

Abra o arquivo em inglês para a tabela completa (evita drift entre dois corpos grandes).
