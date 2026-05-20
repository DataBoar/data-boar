# Indice mestre de docs e hubs

**English:** [DOCS_AND_HUBS_INDEX.md](DOCS_AND_HUBS_INDEX.md)

<!-- plans-hub-summary: Indice mestre de todos os hubs de navegacao do projeto -->

> **Para agentes:** quando precisar saber "onde fica o hub de X?", comece aqui ou em [`docs/hubs/INDEX.md`](../hubs/INDEX.md). Hubs **so linkam** — nao movem arquivos canonicos ([ADR-0057](../adr/ADR-0057-lightweight-hub-index-co-located-links.md)).

As tabelas completas (paths e one-liners) estao no arquivo em **ingles** acima — mesma politica de outros hubs gerados (evita drift duplo). Secoes cobertas:

- **Planejamento e priorizacao** — `PLANS_HUB`, `PLANS_TODO`, hierarquia PMO, eixos, primers.
- **Decisoes arquiteturais** — `docs/adr/README.md`, `INVENTORY.txt`.
- **Agentes, politicas e scripts** — `RULES_AND_SKILLS_HUB`, `CURSOR_AGENT_POLICY_HUB`, cold-start ladder, `TOKEN_AWARE_SCRIPTS_HUB`, `AGENTS.md`.
- **Navegacao transversal** — `docs/hubs/INDEX.md`, `docs/README.md`, `MAP.md`.
- **Integridade e release** — `INTEGRITY_HUB`, `RELEASE_INTEGRITY`.

## Manutencao

- Hub novo: linha aqui e em `docs/hubs/INDEX.md` no **mesmo PR**.
- Hub de rules/skills: `uv run python scripts/build_rules_skills_hub.py --write`.
- Hub de plans: `uv run python scripts/plans_hub_sync.py --write`.
