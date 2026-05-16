# Operator Today Mode — 2026-04-08 (continuação tarde/noite)

> Sessão anterior (madrugada): contexto no chat + atualizações em `docs/private/` (mapa mental, goals — **detalhe de empregador/carreira só em notas privadas**, não repetir aqui).
> Se atravessar meia-noite antes de concluir, usa também **`OPERATOR_TODAY_MODE_2026-04-09.md`**.

---

## MODO FORTE — aproximar de **production-ready** (prioridade absoluta)

Objetivo: fechar **evidência**, não só texto. Mapa de composição de marcos: **`docs/plans/SPRINTS_AND_MILESTONES.md`** §5 (*Composing milestones*) + §4.1 (OIDC na borda vs passwordless na app). Versões continuam a seguir **`docs/releases/`** / **VERSIONING** — sem misturar com “fases” de produto.

### Bloco A — Hoje (ordem sugerida)

1. **Working tree público:** Se houver alterações locais em `docs/plans/` (ex.: mapa de marcos), **`.\scripts\check-all.ps1`** → commit em `main` → `git push` → PR só se estiveres noutra branch.
2. **S0 — Trust burst (mínimo viável):** [SPRINTS_AND_MILESTONES.md §4.0](../../plans/SPRINTS_AND_MILESTONES.md#40-s0-and-s0b--execution-checklist-when-ready) — **–1 / A1** Dependabot + lockfile + `requirements.txt` alinhados; **–1b / A2** `docker scout quickview` na imagem que corresponde a `main`; **A3** higiene de tags no Hub (ou exceção documentada). *Meta:* **M-TRUST** honesto ou exceções escritas.
3. **S0b — Operabilidade (um item):** Escolher **só um** — runbook one-liner (**`/health`**, logs, disco/SQLite), **nota backup/restore** (config + SQLite + `report.output_dir`), ou **`python scripts/kpi-export.py --limit-prs 10`** colado em `docs/releases/` ou nota. *Meta:* avançar **M-OBS**.
4. **–1L — Homelab (fechar ou datar):** [HOMELAB_VALIDATION.md](../../HOMELAB_VALIDATION.md) — completar **§1 baseline + §2 synthetic FS** noutro host **ou** registar em `docs/private/` **porque** está adiado + próxima janela. *Meta:* **M-LAB** credível ou risco explícito.
5. **Identidade / superfície exposta (caminho para M-ACCESS):** **Não** precisa de código no dia 1 — escolhe **uma** frente: (a) **D-WEB** doc-only — rascunhar URL map + ordem de middleware (`api/routes.py`, locale, sessão futura) em 1 página; **ou** (b) documentar deploy **reverse proxy + OIDC** (Traefik/Caddy/OAuth2 Proxy) como padrão de referência com link em `docs/deploy/`. Issue **[#86](https://github.com/FabioLeitao/data-boar/issues/86)** fica para sprint dedicado; hoje só **prepara terreno**.

### Bloco B — Se ainda houver tempo nesta janela

- **`gh pr list` / `git pull`** em `main`; confirmar CI verde no último merge.
- **`.\scripts\private-git-sync.ps1`** se o nested git em `docs/private/` tiver mudanças com valor.
- **Bandit Phase 3** (triagem *low*) — só se A+B estiverem verdes; senão adia.

### Bloco C — Não desviar agora (proteger foco)

- Novos conectores (S3, SAP), **i18n dashboard** implementação, **Tier 1 data soup**, Selenium QA completo, Wazuh/lab observability pesado — **depois** de A + evidência –1L + plano de identidade.

---

## STATUS GERAL (eod-sync 2026-04-08)

- **Branch:** `main` — alinhado com `origin/main` (working tree limpo no repo público).
- **Commits em `origin/main` desde meia-noite local (8 abr):** ver `git log origin/main --since=midnight --oneline` — inclui deps pygments (Dependabot), fixes scripts/guard, housekeeping.
- **PRs abertos (`gh pr list`):** nenhum no momento do ritual EOD.
- **Git privado empilhado (`docs/private/`):** o ritual reportou **alterações pendentes** no private repo — correr `.\scripts\private-git-sync.ps1` (e `-Push` se quiser enviar para o remote de lab) **antes** de dormir se quiser histórico seguro das notas desta sessão.

---

## CARRYOVER — 2026-04-06 (ainda relevante)

Ver tabela completa em **`OPERATOR_TODAY_MODE_2026-04-06.md`**. Resumo:

- [x] Commit/push **Ansible + USAGE** — **feito** em `origin/main` (2026-04-09); outro clone só precisa `git pull`.
- [x] `USAGE.pt_BR.md` — seção Ansible (sync EN) — **feito** (2026-04-09).
- [ ] `ansible-playbook … --check` no LAB-NODE-01/lab quando disponível
- [ ] **LAB-NODE-01 / `uv`:** playbook atual não instala toolchain dev — se quiser testar Data Boar **a partir do código** no LAB-NODE-01, ou instalas `uv` à mão ou abrimos issue/PR para role opcional `uv` (discutido no chat)
- [ ] Homelab: NVMe USB-C; VeraCrypt (private doc)

---

## CARRYOVER — sessão privada desta madrugada (só `docs/private/`)

- [ ] **`private-git-sync`:** muitas linhas em estado pendente no nested git — commit + push conforme política
- [ ] LinkedIn / About / typo de perfil — checklist e nomes de empregador **só** em `docs/private/` (ex.: goals master em `docs/private/author_info/`), não neste arquivo público
- [ ] Opcional: re-fetch de perfil para pasta de pastes privados depois de editar o perfil

---

## Registro — glossário e triagem Gemini (sessão agente)

- [x] **GLOSSARY.md** / **GLOSSARY.pt_BR.md:** nota de **audiência** e **locale** (pt-BR claro para clientes/integradores); entradas **HHS** (não confundir com **HSS**); **minor** (dados de crianças e adolescentes — risco e salvaguardas); **Corporate-Entity-C / WRB** na secção 9.
- [x] **PLAN_GEMINI_FEEDBACK_TRIAGE.md** — item **G-26-13** (Corporate-Entity-C) marcado **Mitigado** com ponteiro ao glossário.

---

## PRIORIDADES RECOMENDADAS — quando voltares **ainda em 8/4**

1. **Private repo:** `.\scripts\private-git-sync.ps1` (revisar diff; commit; `-Push` se aplicável).
2. **Repo público:** Ansible/USAGE já em `main` (2026-04-09); outro clone: `git pull` + `check-all` se estiveres a integrar trabalho local extra.
3. **Leve:** `gh pr list` + `git pull` em `main` após voltar (refresh rápido).
4. **Energia baixa:** só private sync + uma tarefa única (ex. typo LinkedIn offline).

---

## TIMINGS / LEMBRETES

- **Cadência de estudos:** `docs/plans/PORTFOLIO_AND_EVIDENCE_SOURCES.md` §3.0–§3.2; token **`study-check`** no chat para recap.
- **Empregador / política de rede social:** detalhes só em `docs/private/` — não duplicar neste runbook público.
- **Sono:** boas noites; ao acordar, abre este arquivo ou o de **2026-04-09** conforme o relógio.

---

## REFERÊNCIAS RÁPIDAS

- Mapa mental (privado): `docs/private/author_info/PORTFOLIO_MIND_MAP.pt_BR.md`
- Contexto agente: `docs/private/author_info/OPERATOR_CONTEXT_FOR_AGENT.pt_BR.md`
- Ansible: `deploy/ansible/README.md`
- EOD ritual: `.\scripts\operator-day-ritual.ps1 -Mode Eod`
