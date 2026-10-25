# Modo hoje do operador — 2026-05-15 (carryover + fecho de governança)

**English:** [OPERATOR_TODAY_MODE_2026-05-15.md](OPERATOR_TODAY_MODE_2026-05-15.md)

**Nota:** Este arquivo ficou para depois da noite de **2026-05-14**; o **Bloco 0** continua a mandar no "o que correr primeiro" em **2026-05-15**.

--

## Bloco 0 — Realidade de manhã (10–15 min)

Corre **`carryover-sweep`** ou **`.\scripts\operator-day-ritual.ps1 -Mode Morning`**. Depois:

1. **`origin/main`:** `git fetch` · `git status -sb` · `git pull origin main` se estiveres atrás — vê CI do **`main`** (**`ci.yml`**) antes do trabalho fundo.
2. **PRs abertos (deps / workflow):** triagem em sessão **`deps`** ou foco dedicado — conjunto aberto atual inclui **#374** (caps ebcdic/chardet), **#365** (kill-switch Slack CI), **#355**, **#348**, **#347**, **#346**. Faz merge ou adia com data; **não** mistures “chores” com mudança de estatuto de ADR no mesmo PR como atalho de ratificação.
3. **VeraCrypt `Z:` / private stack:** se **fsync** ou montagem **continuarem falhando** desde **2026-05-14**, remonta e volta a correr **`.\scripts\private-git-sync.ps1 -Push`** como em **[ADR 0040](../../adr/ADR-0040-assistant-private-stack-evidence-mirrors-default.md)**.
4. **Governança em voo:** **[ADR 0055](../../adr/ADR-0055-adr-bar-nontrivial-architecture-only.md)** fica **`Proposed`** até **tu** ratificares (**chat explícito para esse ADR** **ou** edição **tua** de **`Status` / `Deciders:`**) — **merge não promove**; ver **`.cursor/rules/adr-trigger.mdc`** e bullet de hábito ADR no **`AGENTS.md`**.

**Fila viva:** [CARRYOVER.pt_BR.md](CARRYOVER.pt_BR.md) · **Publicado:** [PUBLISHED_SYNC.pt_BR.md](PUBLISHED_SYNC.pt_BR.md)

### Social / editorial (hub privado) — ~2 min

- [ ] Olhar **`docs/private/social_drafts/editorial/SOCIAL_HUB.md`** para alvos **2026-05-15** / **2026-05-16** — [SOCIAL_PUBLISH_AND_TODAY_MODE.pt_BR.md](SOCIAL_PUBLISH_AND_TODAY_MODE.pt_BR.md).

---

## Carryover — mesma espinha que **2026-05-14**

| Trilho | Item | Notas |
| ------ | ---- | ----- |
| Estratégia / planos | **PCI-DSS v4 / S4b** (gates de contexto; **ADR-0052** fase 2) | Linha viva em [CARRYOVER.pt_BR.md](CARRYOVER.pt_BR.md) — dono em **`PLANS_TODO.md`**. |
| Lab | **Matriz DB Maestro (all-to-all)** | Reports por host em **`docs/private/homelab/reports/`**; pré-requisitos **sudo**/NFS/CIFS. |
| Produto | **Fecho de sprint** — escolhe **uma** | S3 CNPJ fase 5 **ou** S1 Bandit fase 3 **ou** S2 Scope import fase E — depois **`feature`** + **`check-all`**. |
| Maestro | **Bugs 1–3** (timeout SSH, YAML posicional, race no collect) | Ver checklist **2026-05-14**; commits com testes ou notas de runbook. |
| Social | **L3 LinkedIn**, **X5** | Alvos em atraso; permalinks só no hub privado. |

---

## Foco opcional — ADR / contrato do agente (bloco cur)

- [ ] **Decidir ADR-0055:** **`Accepted`** / **`Rejected`** / **`Deferred`** + **`Deciders:`** real só após **ratificação explícita tua** — alinha a linha do **`docs/adr/README.md`** ao arquivo.
- [ ] **Ler regra always-on** **`.cursor/rules/agent-project-contract-binding.mdc`** — merge não é lei; proíbe atalho “bundle com chores”.

---

## Fim do dia (**2026-05-15**)

- **`eod-sync`** (ou **`block-close`** mais leve se só pausares o bloco) — ver [README.pt_BR.md](README.pt_BR.md) *Prontidão de manhã* / política VeraCrypt privada.
- Se **`docs/private/`** mudou: **`.\scripts\private-git-sync.ps1 -Push`** para os espelhos que usas.
