# Modo de hoje do operador — 2026-06-16 (drenar fila do Dependabot com segurança, sem regressões)

**English:** [OPERATOR_TODAY_MODE_2026-06-16.md](OPERATOR_TODAY_MODE_2026-06-16.md)

**Nota:** Rascunhado para **drenar a fila de PRs do Dependabot com segurança**. O trabalho do gate de produto (#891/#890/#888/#889, deps #896/#899, claims #894, dev-dep rust #892) está mergeado. Sobram sete PRs do Dependabot na fila; três deles (Python) foram abertos **antes** dos merges recentes de dependências, então a base está desatualizada — fazer merge cego causaria conflito ou downgrade. O ritual seguro é **aplicar localmente + validar + fechar o PR do bot como "applied locally"**, conforme `.cursor/skills/dependabot-recommendations/SKILL.md`.

**Âncora da `main`:** `f870f156` — **#903** (handle-web exit reconcile) mergeado. PRs abertos do Dependabot: **#867 #868 #869** (actions), **#870 #871 #348** (Python minor/patch + build), **#872** (redis major). Alerta restante: um `torch` de baixa severidade (sem correção upstream).

---

## Bloco 0 — Realidade da manhã (10–15 min)

1. **`origin/main`:** `git fetch` · `git status -sb` · confirme `ci.yml` verde na `main` antes de trabalho profundo.
2. **PRs abertos:** `gh pr list --state open` — os 7 são do Dependabot.
3. **Stack privado:** se `docs/private/` mudou durante a noite, `./scripts/private-git-sync.ps1 -Push` (ou o caminho `.sh` no Linux).

**Fila contínua:** [CARRYOVER.pt_BR.md](CARRYOVER.pt_BR.md)

---

## Ritual de drenagem segura (contrato sem regressão)

Para cada lote:

1. **Aplicar localmente** (não mergear a branch do bot) — editar YAML / `pyproject.toml`, depois `uv lock` (ou `uv lock --upgrade-package <nome>`), depois atualizar `requirements.txt` com `uv export --frozen --no-emit-project -o requirements.txt` (forma `--no-emit-project` fixada no #891).
2. **Validar:** `./scripts/check-all.sh` (Ruff + format + markdown + pytest completo). Para deps, reproduza também o audit do CI: `uv sync --extra shares && uv pip install pip-audit && uv run pip-audit` (espelha o gate `Dependency audit`).
3. **Guard de regressão** só quando protege um contrato (piso de segurança, comportamento). Pular para patch trivial.
4. **Um PR por lote**, commit assinado, sem rebase/force. Depois do merge, **feche o PR do bot** com comentário "applied locally in #<PR>"; deixe a branch ser apagada.

---

## Classificação de risco (os 7 PRs)

| PR | Mudança | Tipo | Risco | Lote |
| -- | ------- | ---- | ----- | ---- |
| **#867** | `actions/checkout` 6.0.2→6.0.3 (10 workflows) | patch de action | Baixo | **A** |
| **#869** | `astral-sh/setup-uv` 8.1.0→8.2.0 (3 workflows) | minor de action | Baixo | **A** |
| **#868** | `gitleaks/gitleaks-action` 2.3.9→**3.0.0** | major de action (Node 20→24, *sem mudança de input/output/comportamento*) | Baixo, **com prazo** | **A** |
| **#348** | `hatchling` >=1.24.0→>=1.29.0 | build backend | Baixo | **B** |
| **#870** | grupo `uv-minor-patch` (20 pacotes) | minor/patch Python | Médio (**base velha**) | **B** |
| **#871** | `rpds-py` 0.30.0→2026.5.1 (CalVer) | transitivo (via referencing/jsonschema) | **Alto — breaking** | **B (pinar `<2026`)** |
| **#872** | `redis` 7.4.0→**8.0.0** | major direto-opcional (extra `nosql`; breaking só em type hints, RESP3 default) | Médio | **C** |

**Nota da base velha:** a `main` já tem `pypdf 6.13.2`, `starlette 1.3.1`, `python-multipart 0.0.32` (dos #896/#899). O grupo #870 ainda mira versões mais antigas desses — aplique via `uv lock --upgrade` para o resolver manter os pisos mais altos; **não** faça downgrade.

**Urgência do #868:** o GitHub vira os runners para Node 24 em **2026-06-02** (já passou) e remove o Node 20 em **2026-09-16**. O v3 é puro bump de runtime — seguro e necessário.

**#871 rpds-py é breaking (verificado):** o `2026.5.1` é um release **legítimo** (pivô CalVer real no PyPI, não typosquat), **mas quebra o `check-all`** — o próprio CI do PR do bot está vermelho em Lint + Test 3.12/3.13/3.14 (4 reds). `rpds-py` é puramente transitivo (via `referencing`/`jsonschema`); nada aqui precisa do pivô. **Fix:** adicionar a restrição `rpds-py<2026` no Lote B para o resolver manter o `0.x` que funciona. Não deixe o `uv lock --upgrade` puxar o `2026.5.1`.

**redis (#872):** usado por `connectors/redis_connector.py` (import lazy, `redis>=5.0` já permite 8.0). Os breaking do 8.0 são só de type hints; runtime inalterado. Mesmo assim, isole e rode os testes de tier/timeout do connector.

---

## Ordem sugerida

| Passo | Lote | PRs | Validação |
| ----- | ---- | --- | --------- |
| 1 | **A — Actions** | #867, #869, #868 | `quick-test.sh --path tests/test_github_workflows.py` + `workflow-security-lint` (zizmor). #868 tem prazo Set/2026 — não sentar nele. |
| 2 | **C — redis major** | #872 | `check-all.sh` + testes de tier/timeout do connector; isolado |
| 3 | **B — Python minor/patch + build** | #870, #348 | `check-all.sh` + reproduzir o gate `pip-audit`. **Pinar `rpds-py<2026`** (fechar #871 como "não aceita o pivô — breaking") |

A ordem A → C → B é deliberada: A é baixo risco e tem prazo; C é isolado e testável; B por último porque precisa da restrição `rpds-py<2026` para ficar verde. Cada passo = um PR assinado; feche o(s) PR(s) do bot após o merge.

---

## Fim do dia (2026-06-16)

- `eod-sync` + `private-stack-sync` se o stack privado ou o hub social mudarem.
- Caminho do checklist de amanhã: `OPERATOR_TODAY_MODE_2026-06-17.md` (criar no próximo `eod-sync` se faltar).

---

## Referências rápidas

- Ritual Dependabot: `.cursor/skills/dependabot-recommendations/SKILL.md`
- Palavras-chave de sessão: `.cursor/rules/session-mode-keywords.mdc` (`today-mode`, `eod-sync`, `deps`)
- Guard de SHA-pin de workflow: `tests/test_github_workflows.py`; zizmor: `scripts/workflow-security-lint.sh`
