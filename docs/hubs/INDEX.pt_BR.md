# Hubs de navegação — Data Boar

**English:** [INDEX.md](INDEX.md)

> **Para agentes:** leia esta página quando precisar do **mapa dos mapas**. Indice mestre (one-liners): [`docs/ops/DOCS_AND_HUBS_INDEX.md`](../ops/DOCS_AND_HUBS_INDEX.md). Cada linha abaixo aponta para o hub no diretorio canonico — **nao** movemos arquivos ([ADR-0057](../adr/ADR-0057-lightweight-hub-index-co-located-links.md)).

## Como usar

1. Identifique a área (planos, scripts, compliance, pitch).
1. Abra o hub abaixo.
1. Siga os links dentro do hub até o arquivo real.

## Índice

### Planejamento e priorização

| Hub | Caminho canônico | Cobre |
| --- | ---------------- | ----- |
| Plans hub | `docs/plans/PLANS_HUB.md` | Todo `PLAN_*.md` |
| Hierarquia PMO | `docs/ops/PLANS_DOCUMENTATION_HIERARCHY.md` | `PLAN_*` vs `PLANS_TODO` vs `PLANS_HUB` |
| Eixos de taxonomia | `docs/plans/PLAN_TAXONOMY_AXES.md` | Faixas H / U / G / P |
| Primers hub | `docs/plans/PRIMERS_HUB.md` | Primers de frameworks |
| Plans to-do | `docs/plans/PLANS_TODO.md` | Dashboard de execução |

### Decisões arquiteturais

| Hub | Caminho canônico | Cobre |
| --- | ---------------- | ----- |
| Índice ADR | `docs/adr/README.md` | ADR-0001 até o mais recente |

### Scripts e automação

| Hub | Caminho canônico | Cobre |
| --- | ---------------- | ----- |
| Scripts hub | `docs/ops/TOKEN_AWARE_SCRIPTS_HUB.md` | `scripts/*.ps1` / `.sh` |
| Pares cross-platform | `docs/ops/SCRIPTS_CROSS_PLATFORM_PAIRING.md` | Gêmeos Windows/Linux |

### Agentes e políticas

| Hub | Caminho canônico | Cobre |
| --- | ---------------- | ----- |
| Cursor policy hub | `docs/ops/CURSOR_AGENT_POLICY_HUB.md` | Regras + skills |
| Hub de regras e skills | `docs/hubs/RULES_AND_SKILLS_HUB.md` | Todas as rules `.mdc` + skills (gerado) |
| Cold-start ladder | `docs/ops/OPERATOR_AGENT_COLD_START_LADDER.md` | Roteador de sessão |
| Contrato do agente | `AGENTS.md` | Não negociáveis + índice |

### Documentação de produto

| Hub | Caminho canônico | Cobre |
| --- | ---------------- | ----- |
| README docs | `docs/README.md` | Tabelas EN/pt-BR |
| Guia de audiências | `docs/AUDIENCE_GUIDE.md` | Quem lê o quê |
| MAP | `docs/MAP.md` | Navegação por preocupação |
| Use cases | `docs/use-cases/USE_CASES_HUB.md` | Cenários de produto |
| Pitch | `docs/pitch/INDEX.md` | Decks executivos |

### Integridade e release

| Hub | Caminho canônico | Cobre |
| --- | ---------------- | ----- |
| **Hub de integridade** | `docs/ops/INTEGRITY_HUB.md` | Tamper detection, confiança em runtime, docs de release vs licenciamento, inventário ADR |
| Release integrity (spec ops) | `docs/ops/RELEASE_INTEGRITY.md` | Evidência Rust, checklist SRE, pesos GRC |
| Release integrity (produto) | `docs/RELEASE_INTEGRITY.md` | Digest de licenciamento, manifesto opcional, SBOM |
| Integrity check (alpha) | `docs/ops/INTEGRITY_CHECK_ALPHA_LOGIC.md` | Especificação de design em runtime |

### Inspirações

| Hub | Caminho canônico | Cobre |
| --- | ---------------- | ----- |
| Inspirations hub | `docs/ops/inspirations/INSPIRATIONS_HUB.md` | Manifestos de engenharia |

## Ritual de atualização

1. Atualize esta página (EN + pt-BR).
1. Rode `.\scripts\check-hubs.ps1` (incluído no `check-all`).
1. Faça grep por caminhos antigos antes do commit.
