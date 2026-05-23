---
# ADR-0062 — Agent containment: triple-audit offband pattern (A.I.I.D.C.O.B.P.P.)
**Status:** Accepted
**Date:** 2026-05-22
**Relates to:** ADR-0046 (guardrails não-negociáveis), AGENTS.md

## Contexto
Durante a execução da wave-656-u0-u1 (PR #658), o agente do Cursor (Composer-2.5) apresentou desvio de sequenciamento de regras (.mdc), ignorando limites imperativos de escopo e gerando risco latente de regressão de código e consumo fantasma de tokens Anthropic off-band. Devido ao não-determinismo crônico das barreiras nativas da IDE, foi necessária a criação de um mecanismo externo de controle de estado.

Este padrão emergiu empiricamente durante a madrugada de 21-22/05/2026 e foi validado por três auditores independentes: Anthropic Sonnet 4.6 (Windows), Anthropic Sonnet 4.6 (Linux), e Google Gemini Pro (validação estrutural).

## Topologia real (A.I.I.D.C.O.B.P.P.)

```mermaid
flowchart TD
    OP["🧑 Operador\n(Banda Base — data bus)"]
    CW["Claude Windows\nSonnet 4.6 — Auditor A\n(LAB-NODE-01)"]
    CL["Claude Linux\nSonnet 4.6 — Auditor B\n(LAB-NODE-02)"]
    CT["Consenso Tático\nLinting de Prompt\n(convergência entre auditores)"]
    GG["Google Gemini\nValidador de Arquitetura\n(revisão estrutural independente)"]
    TG["Target — Cursor / Git\nTier Composer-2.5\n(executor — labora apenas)"]

    OP -->|"distribui payload"| CW
    OP -->|"distribui payload"| CL
    CW -->|"ping: recomendação A"| CT
    CL -->|"pong: revisão B"| CT
    CT -->|"payload convergido"| GG
    GG -->|"sign-off estrutural"| TG
```

> **Nota crítica de topologia:** Os dois Claude não se comunicam diretamente. O Operador é o barramento físico (data bus) que roteia os payloads entre os auditores. Uma seta direta entre eles seria uma alucinação de infraestrutura.

## Decisão
Implementar o padrão de Triangulação de Três Pilares Independentes fora do barramento do agente controlado:

1. **Isolamento de Estado (Camada Tática):** Dois modelos independentes (Claude Sonnet 4.6) operando em OSes distintos. O operador atua como barramento físico realizando ping-pong de prompts até convergência e eliminação de typos/gaps.
2. **Validação de Fronteira (Camada Estratégica):** Submissão do payload convergido ao terceiro auditor independente (Google Gemini) para validação estrutural.
3. **Execução Idempotente:** Injeção do prompt final com gatilhos de interrupção síncronos (`git log`, `gh issue list`) antes de qualquer push.

## Caso documentado — exemplo negativo
Durante a elaboração deste ADR, três modelos de IA independentes (Anthropic ×2, Google) convergiram em uma convenção de filename incorreta sem consultar o repositório. O operador humano forçou a verificação dos 59 ADRs existentes. O repositório corrigiu o consenso dos três algoritmos.

> **Consenso de LLMs ≠ fonte da verdade. A fonte da verdade é o repositório.**

## Consequências
- **Positivo:** Risco de regressão reduzido; divergência entre auditores = sinal de ambiguidade no prompt; convergência = verde para executar.
- **Negativo:** Aumento do toil do operador humano como barramento de sincronização entre instâncias isoladas.

## Referências
- Issue #656 — wave que originou este padrão
- PR #658 — wave mergeada com o padrão ativo
- ADR-0061 — sequenciamento U-axis (Issue #655)
- PR #648 — arquitetura SoD que motivou auditoria externa
- Issue #659 — origem desta ADR
- `AGENTS.md` — política de auditores vs executor
---
