# Lições aprendidas de LAB — arquivo público datado

**English:** [README.md](README.md)

## Objetivo

Este diretório guarda **cópias imutáveis e datadas** de evidência de QA/SRE de laboratório (métricas, comportamento de checkpoint, números de benchmark) adequadas ao **Git público**. Segue a ideia de **`docs/plans/completed/`**: o histórico fica **separado** e **endereçável pelo nome do arquivo**, enquanto o **hub atual** continua em **[`../LAB_LESSONS_LEARNED.md`](../LAB_LESSONS_LEARNED.md)**.

## Contrato de nomes

| Artefato | Regra |
| --------- | ----- |
| **Snapshot datado** | `LAB_LESSONS_LEARNED_YYYY_MM_DD.md` (data de **fim de sessão** no fuso usado na escrita; **um arquivo por sessão**, salvo divisão explícita pelo operador). |
| **Hub** | [`docs/ops/LAB_LESSONS_LEARNED.md`](../LAB_LESSONS_LEARNED.md) — narrativa **atual** curta + índice de arquivo + **follow-ups** para **`docs/plans/PLANS_TODO.md`**. |
| **Narrativa privada de completão** | `docs/private/homelab/COMPLETAO_SESSION_*.md` — hostnames, LAN, notas do operador; **não** copiar isso literalmente para este arquivo. |

## Ritual (quando uma sessão gera evidência nova)

1. **Copiar** o corpo atual de [`LAB_LESSONS_LEARNED.md`](../LAB_LESSONS_LEARNED.md) para um **novo** `LAB_LESSONS_LEARNED_YYYY_MM_DD.md` aqui (ou copiar e depois editar se o hub já tiver o rascunho novo).
2. **Reduzir** o hub a um resumo curto + ligações a este arquivo e a documentos de sprint / integridade conforme necessário.
3. **Abrir ou atualizar** linhas em **`docs/plans/PLANS_TODO.md`** quando uma lição implicar trabalho rastreado (depois `python scripts/plans-stats.py --write`).
4. Depois de **completão**, manter **`docs/private/homelab/COMPLETAO_SESSION_*.md`** como contexto completo; acrescentar aqui só **números públicos** ou resumos passa/falha quando fizer sentido na árvore do produto.

## Registro de contrato

Postura de arquitetura e automação: **[ADR 0042](../../adr/ADR-0042-lab-lessons-learned-archive-contract.md)**.

Token de sessão (regra Cursor situacional): **`lab-lessons`** → **`.cursor/rules/lab-lessons-learned-archive.mdc`**.
