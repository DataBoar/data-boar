# ADR-0080 — O gate de validação LOCAL é INVIOLÁVEL: check-all completo (all-greens, zero regressões) antes de QUALQUER push ou PR

- **Status:** Accepted
- **Date:** 2026-07-03
- **Deciders:** Fabio Tavares Leitão (operador / owner do repositório)
- **Gate-Change-Approved-By:** Fabio Tavares Leitão

## Contexto

O tier de validação **LOCAL** — `pre-commit` + os testes anti-regressão completos (`pytest`, ~1600) + **Bandit** + **Zizmor** + **Semgrep** — foi construído ao longo de meses **exatamente para NÃO depender do round-trip do GitHub** (esperar minutos por erro remoto e refazer). As regras `check-all-gate.mdc` e `never-weaken-security-gates.mdc` sempre mandaram rodar isso local antes de push/PR.

Em 2026-07-03 constatou-se: (a) não havia `pre-push` hook forçando o gate; (b) o executor pushou rodando apenas testes *targeted* (`2 passed`), não o suite completo; (c) um modelo chegou a **sugerir confiar no CI remoto**. E a tentativa de "reforçar" o mandato **degenerou em proliferar regras `alwaysApply: true`** — queimando contexto, **o oposto do objetivo.** Este ADR corrige as duas pontas: **rigor absoluto** no gate **e** **economia de contexto** no enforcement.

## Decisão (absoluta, não-negociável)

**Nenhum agente, modelo, ferramenta ou automação tem o direito de sequer SUSPEITAR que o `check-all` e todo o ritual de validações locais possa não rodar antes de QUALQUER push ou PR.**

1. O código **NUNCA** sai desta máquina com a menor chance de qualquer coisa exceto **ALL GREENS** e **NO REGRESSIONS**.
2. O ritual local completo (`./scripts/check-all.sh --enforced`) **DEVE passar 100% verde LOCAL, ANTES** de todo push e de toda abertura/atualização de PR. *(Commit local intermediário = pre-commit + checks leves; o full check-all é antes de PUBLICAR no GitHub.)*
3. O que o GitHub CI faz **DEPOIS** é **IRRELEVANTE** para esta regra. CI é *backstop*, **NUNCA substituto**. **Confiar no CI em vez do gate local é PROIBIDO.**
4. **Sugerir, adiar, reduzir ou agir como se** o gate pudesse ser pulado = **VIOLAÇÃO desta ADR.**

## Como é imposto — ENFORCEMENT (mecânico + econômico em contexto)

São **duas peças, e só duas**:

1. **TRAVA mecânica:** o pre-push hook **VERSIONADO** (`.githooks/pre-push` + `core.hooksPath`) roda `check-all.sh --enforced`; falhou → **push abortado**. + teste **tamper-evident** no CI-*required* (removeu o hook → CI falha → não merge). *(issue #1151)*
2. **UMA regra que JÁ é always-on:** `check-all-gate.mdc` (two-tier: commit-local leve / push-PR full). **Nada além dela.**

### Economia de enforcement (parte da decisão — igual peso ao rigor)

**É PROIBIDO criar regras `alwaysApply: true` novas para reafirmar este mandato.** Repetir a regra em N always-on **queima contexto sem adicionar enforcement.** A trava é o **hook**; a regra always-on é **uma só** (`check-all-gate.mdc`). Documentação **contextual/situacional** (globs, `@rule`, session-token) é permitida e encorajada; **always-on nova, não.** Novas always-on ferem `docs/ops/CURSOR_RULES_PHASE2_SITUATIONALIZATION.md` (economia de contexto) e são **anti-padrão**.

## Registro ≠ Enforcement (não confundir — foi a raiz do incidente)

- **Este ADR** = registro durável do **PORQUÊ** + governança. É **DOC** (`docs/adr/`), lido **on-demand** — **NÃO carrega em toda sessão, NÃO causa bloat.**
- **O enforcement** = **hook** (mecânico) + **1 regra** já-always-on. **O rigor vem do mecanismo, não de repetir a regra.**

## Governança da mudança

Mudar/remover/bypassar o gate exige trailer **`Gate-Change-Approved-By: <operador>`**. `git push --no-verify` só com aprovação **explícita e logada**. Violação → **Safe-Hold** + report ao operador.

## Consequências

- Pushes mais lentos localmente (1600 + scans). **ACEITÁVEL e INTENCIONAL** — custo de nunca entregar quebrado e nunca depender do round-trip remoto.
- Todo clone (main dev box — hoje a workstation Linux primária, pode voltar à primária Windows — + secondary) herda o gate no setup.
- Violação = falha de governança.

## Autoridade

Owner = **operador (Fabio Tavares Leitão)**. Claude = auditor read-only. Cursor = executor. Esta ADR **supera qualquer default de agente ou modelo.**
