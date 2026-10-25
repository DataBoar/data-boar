# “Today mode” do operador — 2026-03-30 (sem bloco de carryover)

**English:** [OPERATOR_TODAY_MODE_2026-03-30.md](OPERATOR_TODAY_MODE_2026-03-30.md)

**Objetivo:** Um dia **focado** **sem** **Bloco 0 de carryover** — pediste para omitir carryon. Começa direto em **higiene do repositório + disciplina de merge**. Usa **`today-mode 2026-03-30`** no chat. Limites do dia: **`carryover-sweep`** (manhã, opcional) · **`eod-sync`** (fim do dia) — **`scripts/operator-day-ritual.ps1`**, **`.cursor/rules/session-mode-keywords.mdc`**.

**Nota:** Se mais tarde quiser varredura de carryover, corre **`carryover-sweep`** à parte ou abre **[OPERATOR_TODAY_MODE_2026-03-29.pt_BR.md](OPERATOR_TODAY_MODE_2026-03-29.pt_BR.md)** — **não** faz parte desta checklist.

**Estado de publicação (verificado 2026-03-30):** **`pyproject.toml`** em `main` está em **1.6.7**, alinhado com **GitHub Release Latest [`v1.6.7`](https://github.com/FabioLeitao/data-boar/releases/tag/v1.6.7)** (publicada **2026-03-26**) e **Docker Hub** **`fabioleitao/data_boar:1.6.7`** + **`latest`**. A próxima versão **pública** depois de commits novos relevantes → **`1.6.8`** (bump + notas), não **republicar** **1.6.7**.

---

## Bloco A — Working tree → commits coerentes / PR(s) (≈ 60–120 min)

- Corre **`git status -sb`** e **`.\scripts\preview-commit.ps1`** (ou **`commit-or-pr.ps1 -Action Preview`**) para o âmbito bater com a intenção.
- **Agrupa por tema** (ver **`.cursor/rules/execution-priority-and-pr-batching.mdc`**): ex. **documentação** (hub de inspirações, tabela de craft + análise profunda, amostras compliance, ADRs, índice ops) vs **workflow/regras** (`.cursor`) — evita um PR gigante misturado salvo se for explícito.
- Depois das edições: **`.\scripts\lint-only.ps1`** para fatias só doc, ou **`.\scripts\check-all.ps1`** antes do merge se tocou em código/testes.

---

## Bloco B — Dependabot / deps (≈ 30–45 min)

- PRs abertos (último **`eod-sync`**): **#134** (pypdf / uv), **#143** (grupo pip minor-patch), **#144** (starlette) — confirma **`gh pr checks`** verde, depois **`.\scripts\pr-merge-when-green.ps1 -PrNumber <N>`** quando seguro, ou triage/dismiss conforme **`SECURITY.md`** / higiene Dependabot.
- Após merges: **`git checkout main && git pull`**, atualiza **`uv lock`** / **`requirements.txt`** se o PR não o fez já.

---

## Bloco C — Follow-ups finos opcionais (≈ 30 min, escolhe um)

- **Supply chain:** confirma que **`uv.lock`** continua **sem `litellm`** depois de qualquer refresh de deps; nota de uma linha em **`SECURITY.md`** / diário privado sobre o incidente PyPI **`litellm`** (mar/2026) se quiser lembrete durável (opcional).
- **Inspirações:** espreita **[ENGINEERING_CRAFT_INSPIRATION_ANALYSIS.pt_BR.md](../ENGINEERING_CRAFT_INSPIRATION_ANALYSIS.pt_BR.md)** — acrescenta **um** bullet de cluster só se surgiu padrão novo.

---

## Critério de paragem

O dia está “fechado” quando: a **árvore está limpa em `main`** ou há **WIP intencional** commitado em branch; **PRs Dependabot tratados** (merge, fecho ou data explícita); e **não** há mistura silenciosa de assuntos unrelated num commit só sem intenção.

---

## Atalho no chat

**`today-mode 2026-03-30`** ou abre este arquivo.
