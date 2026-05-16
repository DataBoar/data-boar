# Modo hoje do operador — 2026-05-17 (retomada de manhã)

**English:** [OPERATOR_TODAY_MODE_2026-05-17.md](OPERATOR_TODAY_MODE_2026-05-17.md)

**Nota:** Rascunho a partir do fecho da noite **2026-05-16** — o **Bloco 0** manda amanhã.

---

## Bloco 0 — Realidade de manhã (10–15 min)

Roda **`carryover-sweep`** ou **`.\scripts\operator-day-ritual.ps1 -Mode Morning`**. Depois:

1. **`origin/main`:** `git fetch` · `git status -sb` · `git pull origin main` se estiveres atrás — confirma **`ci.yml`** verde no **`main`** antes de mergulhar.
2. **PRs abertos:** triagem **#365** (rascunho), **#348**, e o que aparecer em `gh pr list` — faz merge quando verde com **`.\scripts\pr-merge-when-green.ps1`** onde fizer sentido.
3. **Marco **M-PILOT-READY**:** checklist de saída no **[PLANS_TODO.md](../../plans/PLANS_TODO.md)** — Maestro **#403** / **#404**+**#408** / release **#406** / PR **#391** / completão smoke nos quatro hosts / **`docs/releases/1.7.4.md`**.
4. **`plans-stats` / `PLANS_TODO`:** se adicionares cabeçalhos `H0`–`H5` no meio do arquivo, relembra **Learned Workspace Facts** no **`AGENTS.md`** — o **`plans-stats.py`** agrupa linhas pelo **último** cabeçalho assim; preferir etiquetas inline tipo **`[H1]`** em vez de **`#### H1`** solto.

**Fila viva:** [CARRYOVER.pt_BR.md](CARRYOVER.pt_BR.md) · **Publicado:** [PUBLISHED_SYNC.pt_BR.md](PUBLISHED_SYNC.pt_BR.md)

### Social / editorial (hub privado) — ~2 min

- [ ] Olhar **`docs/private/social_drafts/editorial/SOCIAL_HUB.md`** para **2026-05-17** / **2026-05-18** — [SOCIAL_PUBLISH_AND_TODAY_MODE.pt_BR.md](SOCIAL_PUBLISH_AND_TODAY_MODE.pt_BR.md).

---

## Carryover — coluna

| Trilho | Item | Notas |
| ------ | ---- | ----- |
| Portão piloto | **M-PILOT-READY** | Use-cases law/pharma/EdTech no **PLANS_TODO**; fechar bundle **v1.7.4** quando os critérios fecharem. |
| Maestro | **#403** SSH `ConnectTimeout`, **#404**+**#408** `--bench-config` | Scripts + testes alinhados; não regredir smoke de completão. |
| Release | **#406** tag **1.7.4** + Hub + **`docs/releases/1.7.4.md`** | Depois de **`check-all`** / ritual de release. |
| Toolchain | **PR #391** correção filtro PII | Merge quando revisão + CI passarem. |
| Governação | **ADR-0055** | Continua **`Proposed`** até ratificação explícita — ver today-mode **2026-05-15** se ainda aberto. |

---

## Fim do dia (**2026-05-17**)

- **`eod-sync`** ou **`block-close`** conforme carga — [README.pt_BR.md](README.pt_BR.md).
- Se **`docs/private/`** mudou: **`.\scripts\private-git-sync.ps1 -Push`**.
