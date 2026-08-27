# Hub de guidelines e guardrails

**English:** [GUIDELINES_AND_GUARDRAILS_HUB.md](GUIDELINES_AND_GUARDRAILS_HUB.md)

> **Para agentes (cold start quando o comportamento estiver em dúvida):**
> Guardrails nesta tabela são **contratos**, não dicas de estilo. Se uma linha discordar de outro doc, confie no **arquivo-fonte nomeado**, não neste índice.
> Este hub **só lista o que existe** na árvore pública. Não copia memória privada do operador, silos de terceiros nem rascunhos de issue velhos.

A prosa canônica permanece nos arquivos ligados.

## Guardrails críticos (regras duras)

| Guardrail | Onde está | Se violar |
| --------- | --------- | --------- |
| Agentes auditores (Claude Code e pares) são **somente leitura** neste repo | [AGENTS.md](../../AGENTS.md) · [`.cursor/rules/agent-roles-executor-vs-auditor.mdc`](../../.cursor/rules/agent-roles-executor-vs-auditor.mdc) · [CLAUDE.md](../../CLAUDE.md) | Dois caminhos de escrita furam gates de PII/ADR/pre-commit |
| Nunca PII, fatos de LAN ou segredos em arquivos **rastreados** | [ADR-0018](../adr/ADR-0018-pii-anti-recurrence-guardrails-for-tracked-files-and-branch-history.md) · [ADR-0019](../adr/ADR-0019-pii-verification-cadence-and-manual-review-gate.md) · [ADR-0020](../adr/ADR-0020-ci-full-git-history-pii-gate.md) · [`.cursor/rules/private-pii-never-public.mdc`](../../.cursor/rules/private-pii-never-public.mdc) | Breach de compliance; gates de CI |
| Nunca enfraquecer um gate de segurança disparado para passar CI | [`.cursor/rules/never-weaken-security-gates.mdc`](../../.cursor/rules/never-weaken-security-gates.mdc) · [ADR-0071](../adr/ADR-0071-self-protecting-pii-gate.md) | Mesma classe da issue **#944** |
| Prosa de operador/docs em português é **pt-BR**, não pt-PT | [AGENTS.md](../../AGENTS.md) · [`.cursor/rules/docs-locale-pt-br-contract.mdc`](../../.cursor/rules/docs-locale-pt-br-contract.mdc) | Inconsistência de docs de produto |
| Taxonomia / nomes não se renomeiam no impulso | [ADR-0048](../adr/ADR-0048-operator-facing-taxonomy-and-naming-contract-preservation.md) | Quebra vocabulário com parceiros e reviews |
| Material comercial confidencial permanece gitignored | [`.cursor/rules/confidential-commercial-never-tracked.mdc`](../../.cursor/rules/confidential-commercial-never-tracked.mdc) | Vazamento competitivo |
| Superfícies públicas: sem datas, URLs ou “publicado” inventados | [`.cursor/rules/publication-truthfulness-no-invented-facts.mdc`](../../.cursor/rules/publication-truthfulness-no-invented-facts.mdc) | Registro público falso |

## Guidelines operacionais (rastreados)

| Guideline | Onde está | Escopo |
| --------- | --------- | ------ |
| Segmentação de rede do lab | [`LAB_NETWORK_SEGREGATION_GUIDELINE.pt_BR.md`](../ops/LAB_NETWORK_SEGREGATION_GUIDELINE.pt_BR.md) | Lab |
| PII na árvore pública | [`PII_PUBLIC_TREE_OPERATOR_GUIDE.pt_BR.md`](../ops/PII_PUBLIC_TREE_OPERATOR_GUIDE.pt_BR.md) | Git público |
| Guideline de pedido de review (pacote WRB) | [`WABBIX_REVIEW_REQUEST_GUIDELINE.md`](../ops/WABBIX_REVIEW_REQUEST_GUIDELINE.md) | Pacote de review externo |
| Preview Markdown no Cursor | [`CURSOR_MARKDOWN_PREVIEW_SETTINGS.pt_BR.md`](../ops/CURSOR_MARKDOWN_PREVIEW_SETTINGS.pt_BR.md) | Agente / editor |
| Mapa de política Cursor / agente | [`CURSOR_AGENT_POLICY_HUB.pt_BR.md`](../ops/CURSOR_AGENT_POLICY_HUB.pt_BR.md) | Agentes |
| Escada de cold start | [`OPERATOR_AGENT_COLD_START_LADDER.pt_BR.md`](../ops/OPERATOR_AGENT_COLD_START_LADDER.pt_BR.md) | Sessão nova |

## Contratos ADR que viram guardrail

Só link — não restabeleça o corpo da Decision aqui.

| ADR | Contrato |
| --- | -------- |
| [ADR-0046](../adr/ADR-0046-operator-intent-and-blameless-collaboration.md) | Intenção do operador + colaboração sem culpa |
| [ADR-0048](../adr/ADR-0048-operator-facing-taxonomy-and-naming-contract-preservation.md) | Taxonomia / nomes |
| [ADR-0049](../adr/ADR-0049-no-brittle-mitigations-robust-input-handling.md) | Sem mitigações frágeis |
| [ADR-0025](../adr/ADR-0025-compliance-positioning-evidence-inventory-not-legal-conclusion-engine.md) | Compliance = evidência e inventário, não conclusão jurídica |
| [ADR-0018](../adr/ADR-0018-pii-anti-recurrence-guardrails-for-tracked-files-and-branch-history.md) / [0019](../adr/ADR-0019-pii-verification-cadence-and-manual-review-gate.md) / [0020](../adr/ADR-0020-ci-full-git-history-pii-gate.md) | Anti-recorrência de PII + gate de histórico no CI |
| [ADR-0066](../adr/ADR-0066-tampered-state-behavior.md) | Comportamento TAMPERED / tinted |

## Condições de Safe-Hold

Pare e reporte ao operador quando qualquer um destes for verdadeiro (definições: [GLOSSARY.pt_BR.md](../GLOSSARY.pt_BR.md) **Safe-Hold**, **TAMPERED**, **TINTED**):

- A verificação de integridade / confiança do runtime falha → estado tinted ou tampered (`core/runtime_trust.py`, docs em [`INTEGRITY_HUB.pt_BR.md`](../ops/INTEGRITY_HUB.pt_BR.md)).
- A razão de velocidade Pro/OpenCore cai abaixo do piso documentado **0.574×** no caminho do engine Pro (`pro/engine.py` / `pro/worker_logic.py`) — trate como hold, não como passe silencioso.
- Hit de PII ou scanner de segredo em caminho **rastreado** antes do commit.
- Um agente auditor somente leitura tentando **escrever** neste repo (exceto `gh issue create` / `gh issue comment` conforme [AGENTS.md](../../AGENTS.md)).

## Mapas relacionados

- Mapa dos mapas: [INDEX.pt_BR.md](INDEX.pt_BR.md)
- Catálogo de ops: [OPS_HUB.pt_BR.md](OPS_HUB.pt_BR.md)
- [AGENTS.md](../../AGENTS.md) continua o contrato longo — esta página não o substitui.
