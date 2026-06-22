# Lab lesson — padrão quad-audit A.I.I.D.C.O.B.P.P.

**English:** [LAB_LESSON_AIIDCOBPP_QUAD_AUDIT.md](LAB_LESSON_AIIDCOBPP_QUAD_AUDIT.md)

**Data:** 2026-05-22/23 (fim da sessão)
**Protocolo:** A.I.I.D.C.O.B.P.P. (ver abaixo)
**Status:** Validado empiricamente em produção de lab
**ADR de referência:** [ADR-0062](../../adr/ADR-0062-agent-containment-triple-audit-offband-pingpong.md)
**Diagrama:** [`docs/adr/ADR-0062-diagram.mermaid`](../../adr/ADR-0062-diagram.mermaid)

Recuperado do backup da estação Windows primária para arquivo público (GitHub **#992**). Codinomes de hostname do rascunho original foram removidos conforme política de PII; a topologia usa placeholders **LAB-NODE-01/02** alinhados ao ADR-0062.

---

## O que é o A.I.I.D.C.O.B.P.P.?

**A**gent · **I**solation · **I**ndependent · **D**ual (expandido para N) · **C**ross-validation · **O**ffband · **B**us · **P**ing · **P**ong

Em português: isolamento de agentes independentes com validação cruzada offband via barramento ping-pong.

O nome canônico do padrão permanece **triple-audit**. Com um quarto auditor (Claude mobile) a configuração virou **quad-audit**, mas o nome do protocolo não é um contador rígido. A seção **Extensibility** do ADR-0062 documenta escala para N auditores.

---

## Contexto

Na wave-656 (PR #658), o agente Cursor apresentou desvio de sequenciamento de regras (`.mdc`), ignorando limites imperativos de escopo e gerando risco de regressão e consumo off-band de tokens.

Barreiras nativas da IDE (regras Cursor, `AGENTS.md`) são necessárias mas insuficientes para conter não-determinismo crônico em sessões longas.

**Conclusão:** Nenhum agente único pode ser árbitro da própria conformidade.

---

## Topologia

```
Operador
│   ↓ distribui payload
├── Auditor A: Claude Windows (LAB-NODE-01)
├── Auditor B: Claude Linux  (LAB-NODE-02)
├── Auditor C: Gemini
└── Auditor D: Claude mobile (visão aérea)
         ↓ convergência
    Cursor / Git (executor — labora apenas)
```

**Regra fundamental:** Os auditores **não** se comunicam entre si. O Operador é o barramento físico.

> Consenso de LLMs ≠ fonte da verdade. A fonte da verdade é o repositório.

---

## Aprendizados principais

1. **Blind spots são sistemáticos** — três LLMs convergiram para filename errado de ADR sem consultar o repo.
2. **Profundidades de contexto complementares** — auditor D (mobile) viu gaps de floresta que A/B/C perderam.
3. **CI do produto detectou PII** que LLMs deixaram passar (`test_public_tree_no_l14_codename.py`).
4. **Guard Rust no check-all** alongou o ritual (~6 min) sem documentação de motivo.
5. **ADR-0045 não foi consultado** ao redigir ADR-0061/0062.
6. **Issues #668–#675** criadas sem labels P nem milestone (ADR-0055).

---

## Quando usar

- Waves críticas (G2/G3) com impacto em segurança, IP ou arquitetura
- Após desvio de escopo do agente autônomo na sessão anterior
- **Não** usar para backlog P3 rotineiro

---

## ROI observado (sessão wave-656)

| Métrica | Valor |
| --- | --- |
| PRs mergeados | 4 (#658, #665, #666, #667) |
| Issues criadas | 8 (#668–#675) |
| ADRs produzidos | 2 (ADR-0061, ADR-0062) |
| PII removido antes do merge | codinomes de estação no rascunho de ADR |
| Gaps de floresta (auditor D) | 8 itens documentais |
| check-all final | 1224 passed, 4 skipped, 0 failed |

---

## Referências

- [ADR-0062](../../adr/ADR-0062-agent-containment-triple-audit-offband-pingpong.md) · [ADR-0061](../../adr/ADR-0061-u-axis-issue-suborder-and-cross-milestone-gate.md) · [ADR-0045](../../adr/ADR-0045-adr-metadata-and-format-standardization.md)
- [`docs/SECURITY_GOVERNANCE_POSTURE_HUB.md`](../../SECURITY_GOVERNANCE_POSTURE_HUB.md)
- Reconciliação de roster com harness atual: GitHub **#991**
