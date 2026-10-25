# Modo hoje do operador — 2026-04-10 (carryover + foco efetivo)

**English:** [OPERATOR_TODAY_MODE_2026-04-10.md](OPERATOR_TODAY_MODE_2026-04-10.md)

> Preparado ao encerrar **2026-04-09** para **2026-04-10** abrir com carryover explícito — não página em branco. Se o relógio já for **11/04**, trata este arquivo como o do dia 10 e abre **`OPERATOR_TODAY_MODE_2026-04-11.md`** quando existir.

---

## Bloco 0 — Realidade de manhã (10–15 min)

Rode **`carryover-sweep`** ou **`.\scripts\operator-day-ritual.ps1 -Mode Morning`**, depois:

1. `git fetch origin` · `git status -sb` · `gh pr list --state open`
2. **`origin/main`:** após o **eod-sync** de **2026-04-09**, o **PR #177** (Dependabot `cryptography`) foi **mergeado** e deu **`git pull`** em `main` (fast-forward em `requirements.txt` / `uv.lock`). Volta a fazer **`git pull`** se outra máquina mergeou à noite.
3. **Working tree (repo público):** provavelmente **ainda** há **muito** diff local (modificados + untracked) — **decide hoje:** commits por tema, branch, stash ou continuar — **não** assume `main` limpo sem olhar.
4. **Git privado empilhado (`docs/private/`):** se ainda houver fila, agenda **`.\scripts\private-git-sync.ps1`** (e **`-Push`** conforme política).
5. `- [ ] **Block close (lab / VC):** ao pausar ou sair do lab mais tarde, escreva **`block-close`** no chat e siga a política de sessão VeraCrypt em **privado** **`docs/private/homelab/OPERATOR_VERACRYPT_SESSION_POLICY*.md`** — checklist de **fronteira**, **não** o ritual completo **`eod-sync`** (git/gh).

**Fila viva:** [CARRYOVER.pt_BR.md](CARRYOVER.pt_BR.md) · **Publicado:** [PUBLISHED_SYNC.pt_BR.md](PUBLISHED_SYNC.pt_BR.md)

---

## Carryover — de `OPERATOR_TODAY_MODE_2026-04-09.md` (ainda aberto)

- [ ] **Private repo:** `private-git-sync` até o estado pendente ficar confortável.
- [ ] **Working tree público:** fechar ou partir em PRs/commits (volume grande).
- [x] **PR #177** Dependabot `cryptography` — **mergeado** após eod 09/04; continue de olho em novos Dependabot por **`SECURITY.md`**.
- [x] **Ansible / USAGE (docs + `main`):** feito em **2026-04-09** (seção Ansible em `USAGE.pt_BR.md`, push em `main`).
- [ ] **LAB-NODE-01 / `uv` / ansible `--check`:** ainda em aberto — ver **`OPERATOR_TODAY_MODE_2026-04-06.md`**.
- [ ] **Homelab / hardware** (NVMe, VeraCrypt): só notas privadas — não repetir aqui.

---

## Carryover — de [CARRYOVER.pt_BR.md](CARRYOVER.pt_BR.md) (destaques)

Escolhe **uma ou duas** linhas para trabalho profundo; o resto **defer** com data ou linha em **PLANS**:

- [ ] Gate release **1.6.8** (notas + testes + publish/defer) — ver **`OPERATOR_TODAY_MODE_2026-04-02.md`** Bloco C.
- [ ] Volta externa **WRB + Gemini** (“code is truth”) — **`PLAN_GEMINI_FEEDBACK_TRIAGE.md`**
- [ ] Snapshot quantificado (`progress-snapshot.ps1`) se ainda não correu
- [ ] Refresh LinkedIn/ATS do founder (playbook privado)
- [ ] Recuperação USB Time Machine — **`TIME_MACHINE_USB_RECOVERY_AND_REPURPOSE.md`**
- [ ] E-mail **Corporate-Entity-C WRB** — bloco: último **`WRB_DELTA_SNAPSHOT_*.md`**
- [ ] Opcional: fatia **Gemini Cold** · paridade **`/help`** quando mudares flags de CLI

---

## Social + editorial (hub privado)

- **Inventário:** `docs/private/social_drafts/editorial/SOCIAL_HUB.md` (atalho: `docs/private/social_drafts/SOCIAL_HUB.md`)
- **Filas:** `EDITORIAL_INSTAGRAM_THREADS_2026-04.md` · `EDITORIAL_X_ROTACAO_2026-04.md` · série LinkedIn se existir
- **Meta do dia:** abre **SOCIAL_HUB** — **uma** publicação ou **um** avanço de rascunho (X / WordPress / linha LinkedIn **L2** se bater com calendário)

---

## Prioridades sugeridas — **2026-04-10**

1. **Estabilizar história Git:** `git status` → commit mínimo honesto ou branch intencional (público); **private-git-sync** se a pilha privada estiver ruidosa.
2. **Uma vitória de carryover:** ex. sync privado **ou** um commit tema docs/workflow **ou** um rascunho social publicado.
3. **`gh pr list`** — esperável **zero** abertos se não entrar nada novo; merge verde com **`pr-merge-when-green.ps1`** quando seguro.
4. **Política Cursor/agente:** se a consolidação (`CURSOR_AGENT_POLICY_HUB`, índice no `AGENTS`) estiver a meio, continua em PRs **pequenos** — não misture com código de produto sem relação.

### Fatia de doc (glossário — **Stark Law**)

- [x] **`docs/GLOSSARY.md` / `GLOSSARY.pt_BR.md`:** entrada **Stark Law** (EUA — autoencaminhamento *Medicare*, distinto de HIPAA/PHI); ligação CMS; remissões **PHI** / **HCP**. *Commit local até `git push`.*

### Fatia de doc (glossário — **CPML** + **PJ vs dado pessoal**)

- [x] **CPML** revisto: contexto **Stark** / **FDA** / compliance (**CGMP**, **CPGM**) vs engenharia; não assumir **CGMP** sem fonte.
- [x] Nova entrada **legal entity and personal data (scanning)** — CNPJ/sócios/contatos: motor **não** ignora LGPD por “só empresa”; regex/ML na amostra.

---

## Fim do dia

- **`block-close`** + VeraCrypt (política privada acima) ao terminar um **bloco** de trabalho ou sair do lab; **`eod-sync`** para **`operator-day-ritual -Mode Eod`** + git/gh/PR + apontar o today-mode de amanhã.
- **`eod-sync`** no chat **ou** **`.\scripts\operator-day-ritual.ps1 -Mode Eod`**
- Prepara ou relê **`OPERATOR_TODAY_MODE_2026-04-11.md`** para a seguir

---

## Referências rápidas

- Ontem: [OPERATOR_TODAY_MODE_2026-04-09.md](OPERATOR_TODAY_MODE_2026-04-09.md)
- Hub scripts token-aware (se existir no tree): `docs/ops/TOKEN_AWARE_SCRIPTS_HUB.pt_BR.md`
- Estudos: `docs/plans/PORTFOLIO_AND_EVIDENCE_SOURCES.md` (calendário do operador)
- Ritmo privado: `docs/private/TODAY_MODE_CARRYOVER_AND_FOUNDER_RHYTHM.md`
