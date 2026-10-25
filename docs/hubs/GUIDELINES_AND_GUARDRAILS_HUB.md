# Guidelines and guardrails hub

**Português (Brasil):** [GUIDELINES_AND_GUARDRAILS_HUB.pt_BR.md](GUIDELINES_AND_GUARDRAILS_HUB.pt_BR.md)

> **For agents (read on cold start when behaviour is in doubt):**
> Guardrails in this table are **contracts**, not style tips. If a row and another doc disagree, trust the **named source file**, not this index.
> This hub **only lists files that exist** in the public tree. It does not copy private operator memory, third-party silos, or stale issue drafts.

Canonical prose stays in the linked files.

## Critical guardrails (hard rules)

| Guardrail | Where it lives | If violated |
| --------- | -------------- | ----------- |
| Claude Code / auditor agents are **read-only** on this repo (issues/comments/prompts only) | [AGENTS.md](../../AGENTS.md) · [`.cursor/rules/agent-roles-executor-vs-auditor.mdc`](../../.cursor/rules/agent-roles-executor-vs-auditor.mdc) · [CLAUDE.md](../../CLAUDE.md) | Dual write paths bypass PII/ADR/pre-commit gates |
| Never put PII, LAN facts, or secrets in **tracked** files | [ADR-0018](../adr/ADR-0018-pii-anti-recurrence-guardrails-for-tracked-files-and-branch-history.md) · [ADR-0019](../adr/ADR-0019-pii-verification-cadence-and-manual-review-gate.md) · [ADR-0020](../adr/ADR-0020-ci-full-git-history-pii-gate.md) · [`.cursor/rules/private-pii-never-public.mdc`](../../.cursor/rules/private-pii-never-public.mdc) | Compliance breach; CI PII gates |
| Never weaken a fired security gate to pass CI | [`.cursor/rules/never-weaken-security-gates.mdc`](../../.cursor/rules/never-weaken-security-gates.mdc) · [ADR-0071](../adr/ADR-0071-self-protecting-pii-gate.md) | Same failure class as issue **#944** |
| Portuguese operator/docs prose is **pt-BR**, not pt-PT | [AGENTS.md](../../AGENTS.md) · [`.cursor/rules/docs-locale-pt-br-contract.mdc`](../../.cursor/rules/docs-locale-pt-br-contract.mdc) | Product-doc inconsistency |
| Naming / taxonomy is not renamed on a whim | [ADR-0048](../adr/ADR-0048-operator-facing-taxonomy-and-naming-contract-preservation.md) | Breaks partner and review vocabulary |
| Confidential commercial material stays gitignored | [`.cursor/rules/confidential-commercial-never-tracked.mdc`](../../.cursor/rules/confidential-commercial-never-tracked.mdc) | Competitive leak |
| Publication surfaces: no invented dates, URLs, or “published” claims | [`.cursor/rules/publication-truthfulness-no-invented-facts.mdc`](../../.cursor/rules/publication-truthfulness-no-invented-facts.mdc) | False public record |

## Operational guidelines (tracked)

| Guideline | Where it lives | Scope |
| --------- | -------------- | ----- |
| Lab network segregation | [`LAB_NETWORK_SEGREGATION_GUIDELINE.md`](../ops/LAB_NETWORK_SEGREGATION_GUIDELINE.md) | Lab |
| PII on the public tree | [`PII_PUBLIC_TREE_OPERATOR_GUIDE.md`](../ops/PII_PUBLIC_TREE_OPERATOR_GUIDE.md) | Public Git |
| Review-request guideline (WRB pack) | [`WABBIX_REVIEW_REQUEST_GUIDELINE.md`](../ops/WABBIX_REVIEW_REQUEST_GUIDELINE.md) | External review pack |
| Cursor Markdown preview | [`CURSOR_MARKDOWN_PREVIEW_SETTINGS.md`](../ops/CURSOR_MARKDOWN_PREVIEW_SETTINGS.md) | Agent / editor |
| Cursor / agent policy map | [`CURSOR_AGENT_POLICY_HUB.md`](../ops/CURSOR_AGENT_POLICY_HUB.md) | Agents |
| Cold-start ladder | [`OPERATOR_AGENT_COLD_START_LADDER.md`](../ops/OPERATOR_AGENT_COLD_START_LADDER.md) | Fresh session |

## ADR contracts that behave as guardrails

Link only — do not restate the Decision body here.

| ADR | Contract |
| --- | -------- |
| [ADR-0046](../adr/ADR-0046-operator-intent-and-blameless-collaboration.md) | Operator intent + blameless collaboration |
| [ADR-0048](../adr/ADR-0048-operator-facing-taxonomy-and-naming-contract-preservation.md) | Taxonomy / naming |
| [ADR-0049](../adr/ADR-0049-no-brittle-mitigations-robust-input-handling.md) | No brittle mitigations |
| [ADR-0025](../adr/ADR-0025-compliance-positioning-evidence-inventory-not-legal-conclusion-engine.md) | Compliance = evidence and inventory, not a legal conclusion |
| [ADR-0018](../adr/ADR-0018-pii-anti-recurrence-guardrails-for-tracked-files-and-branch-history.md) / [0019](../adr/ADR-0019-pii-verification-cadence-and-manual-review-gate.md) / [0020](../adr/ADR-0020-ci-full-git-history-pii-gate.md) | PII anti-recurrence + CI history gate |
| [ADR-0066](../adr/ADR-0066-tampered-state-behavior.md) | TAMPERED / tinted runtime behaviour |

## Safe-Hold conditions

Stop and report to the operator when any of these is true (definitions: [GLOSSARY.md](../GLOSSARY.md) **Safe-Hold**, **TAMPERED**, **TINTED**):

- Runtime integrity / trust verification fails → tinted or tampered state (`core/runtime_trust.py`, integrity docs under [`INTEGRITY_HUB.md`](../ops/INTEGRITY_HUB.md)).
- Pro/OpenCore speed ratio drops below the documented NASA-style floor **0.574×** in the Pro engine path (`pro/engine.py` / `pro/worker_logic.py`) — treat as a hold, not a silent pass.
- PII or secret-scanner hit on a **tracked** path before commit.
- A read-only auditor agent (Claude Code and peers) attempting a **write** to this repo (except `gh issue create` / `gh issue comment` as allowed in [AGENTS.md](../../AGENTS.md)).

## Related maps

- Hub of hubs: [INDEX.md](INDEX.md)
- Ops catalogue: [OPS_HUB.md](OPS_HUB.md)
- [AGENTS.md](../../AGENTS.md) remains the long-form contract — this page does not replace it.
