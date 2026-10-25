# Modo hoje do operador — 2026-05-20 (cedo)

**English:** [OPERATOR_TODAY_MODE_2026-05-20.md](OPERATOR_TODAY_MODE_2026-05-20.md)

**Nota:** Rascunhado no **eod-sync** após **2026-05-19** — social + W7 privado primeiro; fatias de produto depois do **B1**.

**Âncora `main`:** `05e4a4af` — **#615** INTEGRITY_HUB mergeado; lote docs **#608–#614** no **`main`**. Tier **#559** mergeado (**#567**). PRs abertos: **#365** (draft), **#348** (Dependabot).

---

## Bloco 0 — Realidade de manhã (10–15 min)

Corre **`carryover-sweep`** ou **`.\scripts\operator-day-ritual.ps1 -Mode Morning`**. Depois:

1. **`origin/main`:** `git fetch` · `git status -sb` · `git pull origin main` se estiver atrás — confirma **`ci.yml`** verde no **`main`** antes de trabalho profundo.
2. **PRs abertos:** `gh pr list --state open` — merge quando verde com **`.\scripts\pr-merge-when-green.ps1`** onde for seguro (pula **#365** enquanto **DRAFT**, salvo se for publicar de propósito).
3. **Private stack:** se **`docs/private/`** mudou de madrugada: **`.\scripts\private-git-sync.ps1 -Push`** (rascunho W7 **1d59afaa** já no **lab-***).
4. **PMO de planos:** Olha **`docs/plans/PLANS_TODO.md`** — **M-PILOT-READY** ainda aberto; **#606** (P0 plugin hook) bloqueia narrativa Enterprise de tokenizer.

**Fila contínua:** [CARRYOVER.md](CARRYOVER.md) · **Publicado:** [PUBLISHED_SYNC.md](PUBLISHED_SYNC.md)

### Social / editorial (hub privado) — prioridade hoje

| Alvo | Linha | Ação |
| ---- | ----- | ---- |
| **2026-05-20** | **B1** Bluesky | Publicar `@presuntorj.bsky.social` — rascunho `2026-05-09_bsky_databoar_llm_incident_echo.md`; atualizar **SOCIAL_HUB** → `published` + URL |
| **2026-05-21** | **X5** | Preparar/validar fio: `uv run python scripts/social_x_thread_lengths.py` |
| **2026-05-22** | **W5 / L6 / W6** | Bloco editorial (kit LLM relaunch + gerúndio fabioleitao) — sessão warm Meta + WP |
| **2026-05-29** | **W7** | Rascunho pronto no private — `2026-05-29_wordpress_databoar_1201_testes_pre_commit.md` (audit **1.201** passes, **259.95s**) |

Ver [SOCIAL_PUBLISH_AND_TODAY_MODE.pt_BR.md](SOCIAL_PUBLISH_AND_TODAY_MODE.pt_BR.md) · **`docs/private/social_drafts/editorial/SOCIAL_HUB.md`**.

---

## Foco sugerido (depois do social)

| Prioridade | Item | Notas |
| ---------- | ---- | ----- |
| **Social** | **B1** hoje | Timing antes de marcar demo Rafael/weAi — prova pública de postura de engenharia |
| **P1** | [#582](https://github.com/FabioLeitao/data-boar/issues/582) / [#583](https://github.com/FabioLeitao/data-boar/issues/583) | ADR-0056/0057 para **inv-adr** + padrão hub (par com **INTEGRITY_HUB**) |
| **P1** | [#578](https://github.com/FabioLeitao/data-boar/issues/578) | Hub RULES_AND_SKILLS |
| **P0** | [#606](https://github.com/FabioLeitao/data-boar/issues/606) | Hook mínimo plugin Enterprise — parceria tokenizer depende disto |
| **H1** | **M-PILOT-READY** | **#406** stable **v1.7.4** + completão limpo nos quatro hosts |

---

## Carryover — espinha

| Trilho | Item | Notas |
| ------ | ---- | ----- |
| Comercial | Rafael / weAi | Demo POC OK em **1.7.3** / **1.7.4-rc**; stable **1.7.4** + MOU antes do pitch de tokenização |
| Editorial | Rascunho W7 private | Linha **W7** no **SOCIAL_HUB** — publicar **2026-05-29** no databoar.wordpress.com |
| Piloto | **M-PILOT-READY** | Checklist no **PLANS_TODO** — fila não está vazia |

---

## Fim do dia (**2026-05-20**)

- **`eod-sync`** + **`private-stack-sync`** se private ou hub social mudou.
- Caminho de amanhã: **`OPERATOR_TODAY_MODE_2026-05-21.md`** (criar no próximo **eod-sync** se faltar).
