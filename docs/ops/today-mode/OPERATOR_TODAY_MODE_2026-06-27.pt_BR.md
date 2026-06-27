# Today-mode do operador — 2026-06-27 (pós-1.7.4 GA · housekeeping pré-épico)

**English:** [OPERATOR_TODAY_MODE_2026-06-27.md](OPERATOR_TODAY_MODE_2026-06-27.md)

**Destaque:** **1.7.4 GA publicado** (2026-06-26). Hoje = **housekeeping / chore** no `main` antes do épico **A.I.I.D.C.O.B.P.P. v2** (governança + vault + ADR — **fatia séria**, sem misturar com deps/cosmética). **Só Composer** no Cursor até o refil Ultra (**2026-07-09**).

**Âncora `main`:** `1a8d954d` — **`ci.yml` verde** no merge do **#1033** (2026-06-26). **Publicado:** [PUBLISHED_SYNC.pt_BR.md](PUBLISHED_SYNC.pt_BR.md) (**v1.7.4**, Hub **:1.7.4** + **:latest**).

**Fila pré-épico (privada):** ver **`docs/private/ops/`** (handoff do auditor — detalhe fica no privado; peça ao Cursor os trechos mecânicos quando escolher uma linha).

---

## Bloco 0 — Realidade da manhã (10–15 min)

Rode **`carryover-sweep`** / **`./scripts/operator-day-ritual.sh -Mode Morning`** (ou `.ps1`). Depois:

1. **`origin/main`:** `git fetch` · `git status -sb` · confirme **`ci.yml`** verde no `main` atual.
2. **PRs abertos:** `gh pr list --state open` — fila Dependabot (**#1025**, **#1029**, **#1011**, **#1010**, **#975**, **#974**, **#915**, **#912**, …) — só **`deps`** / **`houseclean`**; **sem merge cego** (`.cursor/skills/dependabot-recommendations/SKILL.md`).
3. **Git privado empilhado:** se `docs/private/` mudou de madrugada, `./scripts/private-git-sync.sh -Push` (EOD **2026-06-26** já rodou — commit privado **`689261e`**).

**Fila contínua:** [CARRYOVER.pt_BR.md](CARRYOVER.pt_BR.md) · **Verdade publicada:** [PUBLISHED_SYNC.pt_BR.md](PUBLISHED_SYNC.pt_BR.md)

### Social / editorial (~2 min)

- [ ] Passar o olho em **`docs/private/social_drafts/editorial/SOCIAL_HUB.md`** para **Alvo editorial** de **hoje** / **amanhã** — [SOCIAL_PUBLISH_AND_TODAY_MODE.pt_BR.md](SOCIAL_PUBLISH_AND_TODAY_MODE.pt_BR.md).

---

## Prioridade — housekeeping pré-épico (antes do A.I.I.D.C.O.B.P.P.)

**Regra:** **A.I.I.D.C.O.B.P.P. v2** (vault `project_aiidcobpp_pattern`, amend ADR-0062, issue-bus) = **Gate do operador** + **Tier 2+** — **não** é o default de hoje salvo promoção explícita.

| Trilha | Intenção | Notas |
| ------ | -------- | ----- |
| **Chores pré-épico** | Fechar ponteiros **públicos** obsoletos + housekeeping de **código** que o auditor listou | Composer + `lint-only` / `check-all`; um PR por lote coerente |
| **Docs opcionais** | `PLANS_TODO.md` **~L621** (M-PILOT / “next patch” ainda fala 1.7.3→1.7.4) · **CARRYOVER** “v1.7.4-rc no main” → marcar shipado | Só doc; espírito do **#1032** |
| **Dependabot** | Triar **um** PR se couber (ex. **#974** `py7zr` alinha com narrativa G1 do lab) | Segurar se o bench Maestro voltar |
| **Épico (adiar)** | Captura **A.I.I.D.C.O.B.P.P. v2 FINAL** + ADR | Após Gate: `private-stack-sync` + amend **ADR-0062** |

**Ontem fechado (não reabrir):** **#1024** release · **#1026** Docker daemonless · **#1031** man `data-boar` · **#1033** `PUBLISHED_SYNC` · **#406** gate no `main`.

---

## Carryover — secundário

- [ ] **Lista pré-épico (privada):** escolher **uma** linha do handoff do auditor; Cursor executa diff/testes/corpo de PR.
- [ ] **Maestro / #968 / R12.2** — backlog pós-gate; não bloqueia publish 1.7.4 (ver **#1021** / **PLANS_TODO**).
- [ ] **Roster premium (2026-07-09):** Codex 5.3 como slot **O** default no Ultra — só planejamento hoje.
- [ ] Rolagem: [CARRYOVER.pt_BR.md](CARRYOVER.pt_BR.md) — atualizar linha obsoleta **1.7.4-rc** quando der.

---

## Fim do dia (2026-06-27)

- **`eod-sync`** + **`private-stack-sync`** se o privado ou evidência de homelab mudou.
- Próximo checklist: **`OPERATOR_TODAY_MODE_2026-06-28.md`** (criar no próximo `eod-sync` se faltar).

---

## Referências rápidas

- Tokens de sessão: `.cursor/rules/session-mode-keywords.mdc` (`today-mode`, `carryover-sweep`, `eod-sync`, `houseclean`, `deps`, `private-stack-sync`)
- Governança (épico adiado): ADR-0062 · A.I.I.D.C.O.B.P.P. v2 FINAL (Gate do operador pendente)
- Token-aware: `docs/plans/TOKEN_AWARE_USAGE.md`
