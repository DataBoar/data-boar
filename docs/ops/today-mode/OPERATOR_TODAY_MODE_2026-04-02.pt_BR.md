# Modo hoje do operador — 2026-04-02 (ritmo normal, token-aware, gate de release)

**English:** [OPERATOR_TODAY_MODE_2026-04-02.md](OPERATOR_TODAY_MODE_2026-04-02.md)

**Objetivo:** manter o ganho do ciclo MAX e voltar ao ritmo padrão: slices pequenas e coerentes, gates explícitos e sem ambiguidade de release.

---

## Bloco 0 — Checagem de realidade (10-20 min)

1. Confirmar verdade atual:
   - Versão de trabalho no repo: `1.6.8` (`pyproject.toml`, `core/about.py`).
   - Última release/tag publicada: confirmar em GitHub Releases e Docker Hub.
1. Confirmar estado de branch/worktree:
   - `git status -sb`
   - `git fetch origin`
   - `gh pr list --state open`

---

## Bloco A — Gate de qualidade de documentação (15-25 min)

Rodar e guardar referência da saída:

```powershell
uv run pytest tests/test_docs_pt_br_locale.py -q
uv run pytest tests/test_markdown_lint.py::test_markdown_lint_no_violations -q
```

Se der vermelho, corrigir drift de locale (traços de pt-PT, tradução truncada) antes de qualquer publish.

---

## Bloco B — Ciclo de revisão externa (WRB + Gemini) (30-60 min)

### WRB (Corporate-Entity-C)

1. Usar: `docs/ops/Corporate-Entity-C_WRB_REVIEW_AND_SEND.pt_BR.md`.
1. Manter explícitas as três lentes temporais:
   - histórico acumulado;
   - desde o último relatório Corporate-Entity-C;
   - desde a última release/tag pública.
1. Pedir split explícito por severidade e por tipo de esforço (segurança, integridade/evidência, feature, docs/governança, ops/observabilidade, refatoração).

### Gemini

1. Gerar bundle seguro:

```bash
uv run python scripts/export_public_gemini_bundle.py --output docs/private/gemini_bundles/public_bundle_2026-04-02.txt --compliance-yaml --verify
```

2. Usar prompt/runbook em `docs/ops/GEMINI_PUBLIC_BUNDLE_REVIEW.md`.
3. Triar saída em `docs/plans/PLAN_GEMINI_FEEDBACK_TRIAGE.md` antes de promover para `PLANS_TODO.md`.

---

## Bloco C — Gate de decisão de release (20-40 min)

Só publicar `v1.6.8` quando tudo for verdadeiro:

- existe nota de release em `docs/releases/1.6.8.md`;
- gate de qualidade está verde (`check-all` ou subconjunto acordado para docs-only);
- estado de PR aberto está claro (sem conflito pendente com a fatia de release);
- texto de versão de trabalho vs publicada está sincronizado na documentação.

Se qualquer gate falhar, não taguear/publicar; mover pendências para carryover com data.

---

## Bloco D — Snapshot quantitativo de progresso (15-25 min)

Gerar janelas de progresso:

```powershell
git log --since="2026-04-02 00:00" --pretty=format:"%h|%ad|%s" --date=short
git log --since="3 days ago" --pretty=format:"%h|%ad|%s" --date=short
git log --since="7 days ago" --pretty=format:"%h|%ad|%s" --date=short
```

Resumir por frentes:

- Produto/detector/API/relatórios
- Segurança/integridade/hardening
- Docs/compliance/narrativa para decisores
- Ops/lab-op/automação de workflow
- Planos/governança de roadmap

---

## Condição de parada

Dia está completo quando:

- guardrails de locale + markdown estiverem verdes;
- pedidos WRB e Gemini estiverem preparados/enviados com framing de fonte da verdade;
- decisão de release estiver explícita (`publicar agora` ou `adiar com gate`);
- snapshot de progresso existir para hoje, 3 dias e 7 dias.
