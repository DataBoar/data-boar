# Modo hoje do operador — 2026-04-22 (pós PR #213: pitch README, hub de planos, espelhos de compliance)

**English:** [OPERATOR_TODAY_MODE_2026-04-22.md](OPERATOR_TODAY_MODE_2026-04-22.md)

**Tema:** o **`main`** deve incluir o **PR #213** (pitch README + vocabulário do deck, **ADR 0035**, ajustes de hub/todo nos planos, toques em **COMPLIANCE** / **GLOSSARY** / **TECH_GUIDE** / **TESTING**, teste **`test_readme_stakeholder_pitch_contract`**). **Primeiro:** **`git fetch origin`** · **`git checkout main`** · **`git pull origin main`** — confirmar merge recente e **`git status`** limpo. **Depois:** próxima linha do **`PLANS_TODO.md`** ou fatia **`feature`** pequena; rodar **`.\scripts\check-all.ps1`** antes de novo PR. **Privado empilhado:** se **`docs/private/`** mudou, **`.\scripts\private-git-sync.ps1`**.

---

## Bloco 0 — Manhã (10–15 min)

Roda **`carryover-sweep`** ou **`.\scripts\operator-day-ritual.ps1 -Mode Morning`**. Depois:

1. Confirmar que não ficou PR aberto redundante em cima do README pitch (**`gh pr list --state open`**).
2. Opcional: **`uv run pytest tests/test_readme_stakeholder_pitch_contract.py tests/test_docs_pt_br_locale.py -q`**

**Fila:** [CARRYOVER.pt_BR.md](CARRYOVER.pt_BR.md) · **Publicado:** [PUBLISHED_SYNC.pt_BR.md](PUBLISHED_SYNC.pt_BR.md)

### Social / editorial (hub privado) — ~2 min

- [ ] Olhar **`docs/private/social_drafts/editorial/SOCIAL_HUB.md`** por **Alvo** em **2026-04-22** — [SOCIAL_PUBLISH_AND_TODAY_MODE.pt_BR.md](SOCIAL_PUBLISH_AND_TODAY_MODE.pt_BR.md).

---

## Carryover — do EOD anterior

- [ ] **`main`** atualizado após merge do **#213** — sem trabalho pendente na branch antiga, salvo follow-up explícito.
- [ ] **Git privado:** se o ritual sinalizou pendências, commit/push no repo empilhado (nada de segredo em PR público).

---

## Fim do dia

- **`eod-sync`** ou **`.\scripts\operator-day-ritual.ps1 -Mode Eod`**
- Reler ou criar **`OPERATOR_TODAY_MODE_2026-04-23.md`** a partir deste arquivo se precisar

---

## Referências rápidas

- **`docs/adr/ADR-0035-readme-stakeholder-pitch-vs-deck-vocabulary.md`** — pitch vs deck
- **`docs/plans/PLANS_TODO.md`** · **`docs/plans/PLANS_HUB.md`**
- Atalhos: **`eod-sync`**, **`carryover-sweep`**, **`pmo-view`**
