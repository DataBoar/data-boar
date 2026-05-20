# Hubs de navegação — Data Boar

**English:** [INDEX.md](INDEX.md)

> **Para agentes:** leia esta página primeiro quando precisar do **mapa dos mapas**. Cada linha aponta para o hub no diretório canônico — **não** movemos hubs para cá (ver issue **#577**).

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
| Release integrity | `docs/ops/RELEASE_INTEGRITY.md` | Tags, Hub, evidência |
| Integrity check (alpha) | `docs/ops/INTEGRITY_CHECK_ALPHA_LOGIC.md` | Confiança em runtime |

*(planejado)* **INTEGRITY_HUB** — GitHub **#576**.

### Inspirações

| Hub | Caminho canônico | Cobre |
| --- | ---------------- | ----- |
| Inspirations hub | `docs/ops/inspirations/INSPIRATIONS_HUB.md` | Manifestos de engenharia |

## Ritual de atualização

1. Atualize esta página (EN + pt-BR).
1. Rode `.\scripts\check-hubs.ps1` (incluído no `check-all`).
1. Faça grep por caminhos antigos antes do commit.
