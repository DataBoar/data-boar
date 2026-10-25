# WRB — instantâneo de delta para o próximo e-mail (2026-03-26)

**English:** [WRB_DELTA_SNAPSHOT_2026-03-26.md](WRB_DELTA_SNAPSHOT_2026-03-26.md)

Cola o **parágrafo** da seção seguinte no e-mail à Corporate-Entity-C **depois** do prompt mestre em [Corporate-Entity-C_REVIEW_REQUEST_GUIDELINE.md](Corporate-Entity-C_REVIEW_REQUEST_GUIDELINE.md) (ou integra na seção 2 de [Corporate-Entity-C_WRB_REVIEW_AND_SEND.pt_BR.md](Corporate-Entity-C_WRB_REVIEW_AND_SEND.pt_BR.md) antes de enviar). Atualiza o **hash de commit** se enviares após um merge novo.

---

## Verdade das versões (evitar confusão)

- O **`pyproject.toml`** / docs em **`main`** apontam para **1.6.7** (vê `docs/releases/1.6.7.md`).
- A **última tag publicada** é **`v1.6.7`**, com GitHub Release e Docker Hub alinhados (`1.6.7` e `latest`).
- Pede à Corporate-Entity-C para tratar **“desde a última entrega etiquetada”** como **desde a tag `v1.6.7`**, salvo confirmarem tag mais recente no GitHub.

---

## Bloco para colar (PT-BR)

```text
Contexto complementar (2026-03-26):

Desde o nosso último ciclo WRB e desde a tag v1.6.6, o main acumulou (ou vai integrar no próximo merge) trabalho que inclui: job de lint na CI alinhado com `pre-commit run --all-files` (Ruff, plans-stats --check, markdown, locale pt-BR, guarda commercial); novo hook local `plans-stats-check`; workflow Semgrep para SAST Python; série ADR 0000–0003 (baseline de origem, MD029, docs do operador, roadmap SBOM); docs/ops/WORKFLOW_DEFERRED_FOLLOWUPS; guia acadêmico para tese (ACADEMIC_USE_AND_THESIS + pt-BR); atualizações de regra/skill de qualidade; ping Slack ao operador verificado.

Manter as três lentes temporais separadas. Para “desde a última release etiquetada”, usar v1.6.7 como baseline (última release publicada) e separar trabalho não publicado em `main`, se houver.
```

---

## Relacionado

- [Corporate-Entity-C_IN_REPO_BASELINE.md](Corporate-Entity-C_IN_REPO_BASELINE.md)
- [PLANS_TODO.md](../plans/PLANS_TODO.md)
