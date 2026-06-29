# Today-mode do operador — 2026-06-29 (housekeeping onda 2 · TestPyPI · pausa nas auditorias)

**English:** [OPERATOR_TODAY_MODE_2026-06-29.md](OPERATOR_TODAY_MODE_2026-06-29.md)

**Destaque:** Dia de **descanso + refil de tokens** — fechar **housekeeping de planos** antes de **features** novas. **TestPyPI** tem **`1.7.4`** + **`1.7.4.post1`** (2026-06-27); **`pyproject.toml` local** = **`1.7.4.post1`**. Investigação **Claude Code** (hardware legado / **pipx** / Alpine **musl**, Celeron sem AVX ~2009, stack ML sem DL) **ainda não entrou no repo público** — capturar quando o allowance voltar (~**17h** horário local).

**Âncora `main`:** `07b5dc50` — merge **#1052** PyPI OIDC; **`ci.yml` verde** (última execução **2026-06-27**). **Estável publicado:** [PUBLISHED_SYNC.pt_BR.md](PUBLISHED_SYNC.pt_BR.md) (**v1.7.4** GitHub + Hub); TestPyPI é **canal à parte** — [test.pypi.org/project/data-boar](https://test.pypi.org/project/data-boar/).

**Em voo (git público, fora do `main`):** branch **`houseclean/plans-drift-archive-91`** — commit **`61df9df0`** (5 planos → `completed/` + status detection/secrets); **4 fixes de link** fora do commit (gate PII no stage). **PR [#1062](https://github.com/FabioLeitao/data-boar/pull/1062)** — survey docs **#1056** (merge **depois** ou **rebase** com plans-drift).

---

## Bloco 0 — Realidade da manhã (10–15 min)

Rode **`carryover-sweep`** / **`morning-readiness`**. Depois:

1. **`origin/main`:** `git fetch` · `git status -sb` · `gh run list --workflow ci.yml --branch main --limit 1`.
2. **PRs abertos:** `gh pr list --state open` — **produto:** **#1062** · **houseclean:** push/abrir PR da branch **`houseclean/plans-drift-archive-91`** · **Dependabot:** segurar salvo sessão **`deps`** (**#974** `py7zr` continua bom primeiro candidato).
3. **Git privado empilhado:** EOD **2026-06-29** rodou **`./scripts/private-git-sync.sh --push`** — privado **`1fddf98`**; bare **origin** + espelhos **lab-*** configurados OK — repetir **`private-stack-sync`** se algum mirror não terminou.
4. **Orçamento de tokens:** Composer primeiro até refil premium (~**17h**); **sem** maratonas de auditoria/investigação antes do refil, salvo promoção explícita de uma linha.

**Fila contínua:** [CARRYOVER.pt_BR.md](CARRYOVER.pt_BR.md) · **Verdade publicada:** [PUBLISHED_SYNC.pt_BR.md](PUBLISHED_SYNC.pt_BR.md)

### Social / editorial (~2 min)

- [ ] Passar o olho em **`docs/private/social_drafts/editorial/SOCIAL_HUB.md`** — [SOCIAL_PUBLISH_AND_TODAY_MODE.pt_BR.md](SOCIAL_PUBLISH_AND_TODAY_MODE.pt_BR.md).

---

## Prioridade — housekeeping antes de features

**Regra:** Nenhum épico **feature** novo até a **onda 2 de housekeeping** cair no `main` (salvo override explícito).

| Ordem | Trilha | Intenção | Notas |
| ----- | ------ | -------- | ----- |
| **1** | **Plans drift #91** | Merge **`houseclean/plans-drift-archive-91`** | 5 planos → `completed/`; **detection** **Active** (#1056); **secrets** só Phase A; **4 links** — allowlist ou hostnames genéricos em micro-PR |
| **2** | **Plans drift onda 2** | Arquivar low-hanging + honestidade no `PLANS_TODO` | **`PLAN_OPERATING_DOMAIN_*`** · **`PLAN_SCOPE_IMPORT_*`** · **`PLAN_CLI_VALIDATE_*`** se issues fechadas · tabela **HTTPS** no `PLANS_TODO` ainda ⬜ com plano em **completed/** |
| **3** | **#1056 / #1062** | Merge survey docs após rebase no `main` | Depois **#1057→#1058→#1059→#1061→#1060** (ordem docs-first acordada) |
| **4** | **pipx legado / Alpine** | Promover investigação Claude → plano ou ADR rastreado | Evidência em **`docs/private/`**; sem PII/LAN em PR público |
| **5** | **Adiar** | **A.I.I.D.C.O.B.P.P. v2**, Maestro e2e, **deps** em massa (**#1025**) | Depois do housekeeping verde |

**Sessão recente (não perder):** TestPyPI **`1.7.4.post1`** em **2026-06-27**; auditorias em pausa — **descanso merecido**.

---

## Carryover — secundário

- [ ] Alinhar narrativa **TestPyPI** vs **`pyproject.toml`** / **`PUBLISHED_SYNC`** (Test ≠ PyPI produção).
- [ ] **`gh pr checks`** no **#1062** antes do merge.
- [ ] Atualizar linha obsoleta **“v1.7.4-rc no main”** no **CARRYOVER**.
- [ ] **Roster premium (2026-07-09):** só planejamento.

---

## Fim do dia (2026-06-29)

- **`eod-sync`** + **`private-stack-sync`** se privado ou evidência de homelab mudou.
- Próximo checklist: **`OPERATOR_TODAY_MODE_2026-06-30.md`** no próximo **`eod-sync`**.

---

## Referências rápidas

- Tokens de sessão: `today-mode`, `carryover-sweep`, `eod-sync`, `houseclean`, `private-stack-sync`, `block-close`
- PMO planos: `docs/plans/PLANS_TODO.md`, `PLAN_TAXONOMY_AXES.md`, housekeeping interno **#91** (Claude Code — não é issue GitHub)
- Token-aware: `docs/plans/TOKEN_AWARE_USAGE.md`
