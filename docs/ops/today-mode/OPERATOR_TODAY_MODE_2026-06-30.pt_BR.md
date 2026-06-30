# Today mode do operador — 2026-06-30 (Dependabot · housekeeping · roadmap)

**English:** [OPERATOR_TODAY_MODE_2026-06-30.md](OPERATOR_TODAY_MODE_2026-06-30.md)

**Manchete:** Landar PRs **Dependabot** parados (validar local — **sem merge às cegas**; trava **`rpds-py`** ADR-0069) → fechar **housekeeping** em voo ([#91](https://github.com/FabioLeitao/data-boar/issues/91) / [#1062](https://github.com/FabioLeitao/data-boar/pull/1062) já em `main`) → trilha **licensing** ([#887](https://github.com/FabioLeitao/data-boar/issues/887) — **#1097** entregou Std/Pro+/Partner) → **quick-wins** ([#1089](https://github.com/FabioLeitao/data-boar/issues/1089)–[#1096](https://github.com/FabioLeitao/data-boar/issues/1096)).

**Âncora `main`:** pós-merge **#1097**; **`pyproject.toml`** = **`1.7.4.post1`**. **Estável publicado:** [PUBLISHED_SYNC.pt_BR.md](PUBLISHED_SYNC.pt_BR.md) (**v1.7.4** GitHub + Hub **`latest`**).

---

## Bloco 0 — Realidade da manhã (10–15 min)

Rodar **`carryover-sweep`** / **`morning-readiness`**. Depois:

1. **`origin/main`:** `git fetch` · `git status -sb` · `gh run list --workflow ci.yml --branch main --limit 1`.
2. **Dependabot:** `gh pr list --author "app/dependabot" --state open` — **RED** **#1029** · **#1025** · **#1011** · **#975** · **#974** obsoleto; **VERDE** **#1010** ✅ mergeado · **#915** hatchling (aplicar local) · **#912** Sonar (escopo `workflow` ou merge web).
3. **Git privado empilhado:** **`private-stack-sync`** se `docs/private/` mudou.

**Fila viva:** [CARRYOVER.pt_BR.md](CARRYOVER.pt_BR.md) · **Verdade publicada:** [PUBLISHED_SYNC.pt_BR.md](PUBLISHED_SYNC.pt_BR.md)

### Social / editorial (~2 min)

- [ ] Passar **`docs/private/social_drafts/editorial/SOCIAL_HUB.md`** — [SOCIAL_PUBLISH_AND_TODAY_MODE.pt_BR.md](SOCIAL_PUBLISH_AND_TODAY_MODE.pt_BR.md).

---

## Prioridades

| Ordem | Trilha | Intenção | Notas |
| ----- | ------ | -------- | ----- |
| **1** | **Dependabot** | Fechar ou superseder PRs com bump local + CI verde | Skill: `.cursor/skills/dependabot-recommendations/SKILL.md` |
| **2** | **Housekeeping** | **#1062** ✅ · **#91** ✅; branches **`houseclean/*`** se ainda fora de `main` | Sem **feature** nova até wave 2 landar |
| **3** | **Roadmap licensing** | **#887** — enum em **#1097**; fechar issue | Nudge cortesia Std+ (ADR-DRAFT-0076) |
| **4** | **Quick-wins** | **#1089–#1092** via **#1097**; **#1096** restante; **#1093–#1095** governança | **#1080** fechado (**#1087**) |
| **5** | **Adiar** | SDK **#865** · research **#1081–#1085** · enrich 1.8 **#1057–#1061** | Cauda de token |

---

## Carryover — hoje

- [ ] **`gh pr checks`** fresco antes de merge Dependabot.
- [ ] **`#912`:** `gh auth refresh -s workflow` ou UI GitHub.
- [ ] Branches **`houseclean/*`:** abrir PR ou apagar se superseded.

---

## Fim do dia

- **`eod-sync`** + **`private-stack-sync`** se couber.
- Próximo: **`OPERATOR_TODAY_MODE_2026-07-01.md`**.
