# Today mode do operador — 2026-08-07 (pós-outage Actions + merges HITL)

**English:** [OPERATOR_TODAY_MODE_2026-08-07.md](OPERATOR_TODAY_MODE_2026-08-07.md)

**Manchete:** Incidente GitHub Actions resolvido (~2026-08-07 02:04 UTC). Org-path + quickstart Windows + product-facts na `main`; FAQ do site com CI verde — falta HITL nos merges abertos e limpar débitos nomeados.

---

## Bloco 0 — Realidade de manhã (10–15 min)

- Relógio (workstation): **2026-08-07** (−03).
- PRs abertos (refresh): **data-boar** `#1476` (CLEAN) · **data-boar-site** `#55` (checks verdes; `BLOCKED` = review/proteção).
- CI recente em `main`: **success** (após re-run pós-outage).

Depois:

1. **`git checkout main && git pull origin main`** no data-boar (e no site se fores trabalhar lá).
2. Working tree: apagar branches já mergeadas só depois de confirmar (`docs/quickstart-windows-1128`, `chore/canonicalize-org-path`, etc.).
3. Privado empilhado: **`private-stack-sync`** se notas privadas mudaram no dia da outage.
4. - [ ] **Block close (lab / VC)** mais tarde com o token **`block-close`**.

**Fila viva:** [CARRYOVER.pt_BR.md](CARRYOVER.pt_BR.md) · **Publicado:** [PUBLISHED_SYNC.pt_BR.md](PUBLISHED_SYNC.pt_BR.md)

### Social / editorial (~2 min)

- [ ] Olhar **`docs/private/social_drafts/editorial/SOCIAL_HUB.md`** para Alvo **2026-08-07** / **2026-08-08**.

---

## Carryover — hoje (sessão + fila)

### HITL / merge (esta janela)

- [ ] **data-boar-site [#55](https://github.com/DataBoar/data-boar-site/pull/55)** — FAQ SEO; CI verde após fix do guardrails (`canonical` ≠ asset carregado). **Merge quando quiseres**.
- [ ] **data-boar [#1476](https://github.com/DataBoar/data-boar/pull/1476)** — ADR-0085 install ladder; checks **CLEAN**. Auditar + merge HITL (ou fechar se supersedido).

### Adiado do org-path / packaging (não esquecer)

- [ ] **PORTFOLIO** — `docs/plans/PORTFOLIO_AND_EVIDENCE_SOURCES.md` ainda com **3×** `FabioLeitao/data-boar` (fora do #1473 por gatekeeper). Micro-PR após allowlist vs redact.
- [ ] **ADR Status-history** — sem sed cego em `docs/adr/ADR-*.md` (ADR-0045); passe section-aware depois se ainda precisar.
- [ ] **[#1467](https://github.com/DataBoar/data-boar/issues/1467)** — MSI + winget com `cp314`/`cp314t` embutidos (ADR-0084); já apontado no guia Windows.
- [ ] **[#1127](https://github.com/DataBoar/data-boar/issues/1127)** — `--install-shortcut` (só menção no doc; feature aberta).

### CARRYOVER rolante (≤1 item fundo)

- [ ] Uma linha ativa de [CARRYOVER.pt_BR.md](CARRYOVER.pt_BR.md) (Maestro private, Dependabot, LAB-OP #756) — sem inflar a fila imortal.

---

## Feito recentemente (não reabrir)

- **#1473** canonicalize org-path — mergeado (incl. regenerar PLANS_HUB).
- **#1474** guia Windows non-techie (sem Docker) — mergeado.
- **#1475** product facts canónicos (#1470) — mergeado.
- Revalidação pós-outage — classificar RED real vs infra.

---

## Fim do dia

- **`block-close`** / **`eod-sync`** conforme precisar.
- Preparar **`OPERATOR_TODAY_MODE_2026-08-08.pt_BR.md`** se continuar amanhã.

---

## Referências rápidas

- `docs/ops/TOKEN_AWARE_SCRIPTS_HUB.pt_BR.md`
- `.cursor/rules/session-mode-keywords.mdc`
- `docs/ops/COMMIT_AND_PR.pt_BR.md`
