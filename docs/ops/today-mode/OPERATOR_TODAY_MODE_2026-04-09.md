# Operator Today Mode — 2026-04-09 (carryovers + foco dia 9)

> Preparado no fecho da sessão que prepara **2026-04-09**. Se o relógio local já for **10/04**, trate este arquivo como registro do dia 9 e abre **`OPERATOR_TODAY_MODE_2026-04-10.md`** quando existir.

---

## eod-sync — snapshot (ritual executado)

- **`git fetch origin`:** ok.
- **`origin/main` desde meia-noite local:** nenhum commit novo reportado pelo `git log` neste clone (ou janela vazia).
- **`git status`:** working tree com **muitas** alterações locais e arquivos novos (incl. ADRs, ops, scripts, regras Cursor) — **decidir** antes de amanhã: commit por temas, stash, ou continuar em branch; não assumir `main` limpo.
- **PRs abertos (`gh pr list`):** **#177** — Dependabot `cryptography` 46.0.6 → 46.0.7 (`dependabot/uv/uv-3344959f9f`). Quando verde: `.\scripts\pr-merge-when-green.ps1 -PrNumber 177` ou revisão manual.
- **Git privado empilhado (`docs/private/`):** ritual reportou **pendências** — correr `.\scripts\private-git-sync.ps1` (e `-Push` se aplicável) quando fizer sentido.

---

## Onde estão rascunhos de **outras** redes (não só LinkedIn)

- **Hub com inventário (X, WordPress, estado, URLs):** `docs/private/social_drafts/editorial/SOCIAL_HUB.md` (atalho: `docs/private/social_drafts/SOCIAL_HUB.md`)
- **Arquivos:** mesma pasta `docs/private/social_drafts/` — padrões `2026-*_x_*.md` (X), `*_wordpress_*.md` (WordPress); tabela **Inventário** no hub lista **X1–X4**, **W1–W2**.
- **Filas:** `EDITORIAL_X_ROTACAO_2026-04.md` (X) · `EDITORIAL_LINKEDIN_SERIE_2026-04.md` (LinkedIn)

---

## Carryover — de `OPERATOR_TODAY_MODE_2026-04-08.md` (ainda relevante)

- [ ] **Private repo:** `private-git-sync` até ficar confortável com o estado pendente.
- [ ] **Working tree público:** fechar ou partir em PRs/commits os diffs locais (grande volume).
- [x] **PR #177** Dependabot (`cryptography` 46.0.6 → 46.0.7) — **merged** no GitHub; `git pull` em clones antigos.
- [x] **Ansible / USAGE (docs + `main`):** seção em `USAGE.pt_BR.md` + push — **feito** (2026-04-09).
- [ ] **LAB-NODE-01 / `uv` / ansible `--check`:** ainda em aberto — ver `OPERATOR_TODAY_MODE_2026-04-06.md`.
- [ ] **Homelab / hardware** (NVMe, VeraCrypt): só em notas privadas; não duplicar aqui.

---

## Prioridades sugeridas — **2026-04-09**

1. Abrir **`SOCIAL_HUB.md`** — marcar próximo rascunho **X** ou **WordPress** se for dia de publicar; **L2** LinkedIn se alinhar com calendário.
2. `git status` + decisão sobre commit/stash do trabalho local em curso.
3. **PR #177:** já **merged** no GitHub; antes de novo trabalho, `git pull origin main` nos clones.
4. `private-git-sync` se houver tempo (bloqueio cognitivo: fila grande no private).

---

## Lembretes

- **Estudos:** `study-check` no chat ou `PORTFOLIO_AND_EVIDENCE_SOURCES.md` §3.0–§3.2.
- **Carryover amanhã cedo:** token **`carryover-sweep`** ou `.\scripts\operator-day-ritual.ps1 -Mode Morning`.

---

## Referências rápidas

- Social hub: `docs/private/social_drafts/editorial/SOCIAL_HUB.md` (atalho: `docs/private/social_drafts/SOCIAL_HUB.md`)
- Token-aware scripts: `docs/ops/TOKEN_AWARE_SCRIPTS_HUB.md` (se estiver no teu tree)
- EOD: `.\scripts\operator-day-ritual.ps1 -Mode Eod`
