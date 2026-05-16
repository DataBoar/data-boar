# Modo hoje do operador — YYYY-MM-DD (carryover + foco efetivo)

**English:** [OPERATOR_TODAY_MODE_YYYY-MM-DD.md](OPERATOR_TODAY_MODE_YYYY-MM-DD.md)

> Copie este arquivo para **`OPERATOR_TODAY_MODE_<data>.md`**, ajuste a data no título e nas ligações e substitua os marcadores. Remova esta nota quando o dia for real.

---

## Bloco 0 — Realidade de manhã (10–15 min)

Rode **`carryover-sweep`** ou **`.\scripts\operator-day-ritual.ps1 -Mode Morning`** — o script imprime o **Tier A** (`git fetch`, `git status -sb`, PRs abertos, último CI do **`main`**, arquivo **today-mode** para **hoje**) e lembretes dos **Tiers B–D** (cadência de supply chain / imagem / lab). Ver **[README.pt_BR.md](README.pt_BR.md)** (*Prontidão de manhã*). Depois:

1. **`origin/main`:** **`git pull origin main`** se o ritual mostrar que estás atrás.
2. **Working tree (repo público):** decide: commits, branch, stash ou continuar.
3. **Git privado empilhado (`docs/private/`):** se houver fila, agenda **`.\scripts\private-git-sync.ps1`** (e **`-Push`** conforme política).
4. `- [ ] **Block close (lab / VC):** ao pausar ou sair do lab mais tarde, escreva **`block-close`** no chat e siga a política de sessão VeraCrypt em **privado** **`docs/private/homelab/OPERATOR_VERACRYPT_SESSION_POLICY*.md`** — checklist de **fronteira**, **não** o ritual completo **`eod-sync`** (git/gh).

**Fila viva:** [CARRYOVER.pt_BR.md](CARRYOVER.pt_BR.md) · **Publicado:** [PUBLISHED_SYNC.pt_BR.md](PUBLISHED_SYNC.pt_BR.md)

### Social / editorial (hub privado) — ~2 min

- [ ] Olhar **`docs/private/social_drafts/editorial/SOCIAL_HUB.md`** por **Alvo editorial** em **hoje** / **amanhã** e linhas **`draft`** / **`scheduled`** / **`deferred`** — fluxo: [SOCIAL_PUBLISH_AND_TODAY_MODE.pt_BR.md](SOCIAL_PUBLISH_AND_TODAY_MODE.pt_BR.md).
- [ ] **Adiar post:** atualizar hub + **renomear** prefixo **`YYYY-MM-DD`** do rascunho; linha opcional em **[CARRYOVER.pt_BR.md](CARRYOVER.pt_BR.md)** só se for compromisso **real** entre dias.
- [ ] **Publicação manual ad-hoc** (blog / Data Boar / rede): atualizar **inventário**; opcional evidência em **`docs/private/social_drafts/drafts/evidence/`** — ver **SOCIAL_PUBLISH_AND_TODAY_MODE.pt_BR.md** (seção ad-hoc).

---

## Carryover — (editar)

- [ ] (itens)

---

## Fim do dia

- **`block-close`** + VeraCrypt (política privada acima) ao terminar um **bloco** de trabalho ou sair do lab; **`eod-sync`** para **`operator-day-ritual -Mode Eod`** + git/gh/PR + apontar o today-mode de amanhã.
- **`eod-sync`** no chat **ou** **`.\scripts\operator-day-ritual.ps1 -Mode Eod`**
- Prepara ou relê **`OPERATOR_TODAY_MODE_<proxima-data>.md`** para a seguir

---

## Referências rápidas

- Hub scripts token-aware (se existir no tree): `docs/ops/TOKEN_AWARE_SCRIPTS_HUB.pt_BR.md`
- Atalhos no chat: **`.cursor/rules/session-mode-keywords.mdc`** (**`block-close`**, **`eod-sync`**, **`private-stack-sync`**)
- Ritmo privado: `docs/private/TODAY_MODE_CARRYOVER_AND_FOUNDER_RHYTHM.md`
