# Carryover do "today mode" (fila viva)

**English:** [CARRYOVER.md](CARRYOVER.md)

**Objetivo:** Uma **lista viva** de itens do operador que atravessam vários `OPERATOR_TODAY_MODE_*` datados. **Fecha, adia com data ou passa para `PLANS_TODO` / issue** — nada imortal sem dono.

**Relacionado:** **`carryover-sweep`** (manhã), **`eod-sync`** (fim do dia), **`docs/private/TODAY_MODE_CARRYOVER_AND_FOUNDER_RHYTHM.md`** (privado).

---

## Fila (edite a tabela abaixo no próprio documento)

| Item | Origem | Estado | Próximo passo / defer |
| ---- | ------ | ------ | ----- |
| **Drift de Status do plano de observability lab-op (#1542)** | Sessão lab **2026-08-11→12** · [PLAN_LAB_OP_OBSERVABILITY_STACK.md](../../plans/PLAN_LAB_OP_OBSERVABILITY_STACK.md) | ✅ Feito | Fechado via PR **#1545** (**2026-08-12**). Phase D (Graylog) ainda **não** adotada. |
| **Gaps OTel de produto — LoggerProvider + oneshot + plano preflight** | [#1529](https://github.com/DataBoar/data-boar/issues/1529) · [#1535](https://github.com/DataBoar/data-boar/issues/1535) · [#1540](https://github.com/DataBoar/data-boar/issues/1540) | ✅ Feito (produto/plano) | **#1544 / #1547 / #1548** em `main` **2026-08-12**. Residual **código:** [maestro#32](https://github.com/DataBoar/maestro/issues/32) (linha abaixo). |
| **Preflight OTel Maestro (maestro#32)** | [maestro#32](https://github.com/DataBoar/maestro/issues/32) · desbloqueada pelo fechamento da [#8](https://github.com/DataBoar/maestro/issues/8) | ⬜ Pendente | Implementar em **DataBoar/maestro** `core/`/`engine/` — não no data-boar. |
| **Links do plano de packaging nativo (#1541) + CI Windows (#1427)** | [#1541](https://github.com/DataBoar/data-boar/issues/1541) · [#1427](https://github.com/DataBoar/data-boar/issues/1427) · [#1467](https://github.com/DataBoar/data-boar/issues/1467) | 🔄 #1541 fechada; #1427 ainda aberta | Job `windows-latest` (#1427) ainda bloqueia MSI/winget (#1467). |
| **Sidequest doutrina bestiário (#994) — 10 repos, SOUL vault → DOUTRINA + ADRs** | Sessões **2026-07-01**–**03** · `docs/private/commercial/bestiais/` · vault `bestiais/` | 🔄 Em progresso | **Feito:** inventário honesto; Homing Robin birth-triplet **pushado**; rascunhos locais Ferret / Sage / Stoat (02/jul). **Próximo:** 7 repos + **um PR por repo**. **Maestro** fase 1 **PR #9** mergeado **2026-07-20** (linha abaixo fechada). |
| **Maestro — migração fase 1 + companion purge (#8)** | `DataBoar/maestro` · `docs/ops/CURSOR_ECOSYSTEM_ONBOARDING.md` · data-boar **#1551** | ✅ Feito | Fase 1 **PR #9** (**2026-07-20**). Spinout **#8** fechada **2026-08-12** — data-boar **#1551** removeu `scripts/maestro/`; consumidores usam **`MAESTRO_ROOT`** / sibling via `scripts/Resolve-MaestroRoot.ps1`. Gate do operador: **ADR-0001 Proposed → Accepted**. |
| **#828 scan_failures — open-core em `main`** | PR **#1146** mergeado **2026-07-03** | 🔄 Parcial | Zip/7z/PDF + Bugbot. Issue **#828** aberta para Pro/fixtures/plano. |
| **Housekeeping planos (#91) + survey #1062** | [OPERATOR_TODAY_MODE_2026-06-29.pt_BR.md](OPERATOR_TODAY_MODE_2026-06-29.pt_BR.md) | ✅ Feito | **#91** mergeado · **#1062** mergeado **2026-06-30**. Residual: branches **`houseclean/plans-drift-archive-91`** / **`plans-wave-2`**. |
| **Fila Dependabot (`deps`) — landar ou superseder local** | `gh pr list` **2026-08-12** EOD · skill **dependabot-recommendations** · ADR-0069 **`rpds-py<2026`** | 🔄 Em progresso | **Abertos:** **#1487** reportlab 5 · **#1485** webauthn 3 · **#1484** pyarrow 25. (**#1492** virtualenv mergeado.) Triage com skill — **sem merge às cegas.** |
| **LAB-OP [#756](https://github.com/DataBoar/data-boar/issues/756) — host de lab com disco ~90% + `bw` CLI no Ansible do laptop de dev** | [OPERATOR_TODAY_MODE_2026-05-29.pt_BR.md](OPERATOR_TODAY_MODE_2026-05-29.pt_BR.md) · `PLANS_TODO.md` § LAB-OP | ⬜ Pendente | **`[U1]`** SSH + liberar espaço no host de lab com disco apertado antes de completão nesse host · **`[U2]`** task Ansible para **`bw`** no laptop de dev — **não** bloqueia release; fechar quando a issue fechar ou adiar com data |
| **Licensing [#719](https://github.com/DataBoar/data-boar/issues/719) — bypass JWT via env de dev** | GitHub [P1] · `PLANS_TODO.md` **`[H0][U1]` Licensing enforcement** | ⬜ Pendente | Depois de **#704** [P0] ou se exposição em prod confirmada (**U0**); PR fino **`fix(security)`** + regressão **A6** `license-smoke` |
| **PCI-DSS v4 / prontidão global — ruído PAN + ADR-0052 fase 2 (gates de contexto)** | Sessão operador **2026-05-14** (nota estratégica; fila com dono) | ⬜ Pendente | **Linha dona:** `PLANS_TODO.md` tabela pós-`1.7.4` **S4b** — estender `plugin_schema` + validador + gating no `SensitivityDetector` (proximity opcional / caminho Luhn); calibrar `docs/compliance-samples/compliance-sample-pci_dss.yaml` vs `CREDIT_CARD` embutido; ver `PLAN_YAML_PLUGIN_SYSTEM.md` § *Phase 1b*. Fechar esta linha do carryover quando **S4b** fechar ou adiar com **data** no `PLANS_TODO`. |
| **`v1.7.4` GA + Hub `latest`** | [OPERATOR_TODAY_MODE_2026-05-11.pt_BR.md](OPERATOR_TODAY_MODE_2026-05-11.pt_BR.md) · [PUBLISHED_SYNC.pt_BR.md](PUBLISHED_SYNC.pt_BR.md) | ✅ Enviado | **GA 2026-06-26** — GitHub **v1.7.4**, Docker Hub **`latest`**, PyPI **`1.7.4.post1`**. Dev pós-GA em `main` (ex. **#1097** licensing) sem bump de semver até próximo release ritual. |
| **Workflow `zizmor`** | PR **#354** mergeado **2026-05-11**; enforce padrão **#732** | ✅ Feito | CI em modo enforced por padrão (opt-out: variável **`ZIZMOR_ENFORCE=false`**). Local continua advisory salvo **`-Enforce`** ou **`DATA_BOAR_ENFORCE_ZIZMOR=true`**. |
| **Evidência matriz DB Maestro (all-to-all)** | [LAB_LESSONS_LEARNED_2026_05_10.md](../lab_lessons_learned/LAB_LESSONS_LEARNED_2026_05_10.md) | ⬜ Pendente | Uma rodada consolidada + configs por host em **`docs/private/homelab/reports/`**. |
| **Fechamento sprint curto pós-`1.7.4`** — S3 CNPJ fase 5, S1 Bandit fase 3, S2 Scope import fase E | `PLANS_TODO.md` H1/U1 | ⬜ Pendente | Após métricas de lab ou no mesmo dia sem slot LAB — **`feature`** + **`check-all`**. |
| **Harness `benchmark-ab` na `main` (PR #229)** | EOD 2026-04-27 | ✅ Mergeado | Correr benchmark real com janela LAB e registrar deltas em `BENCHMARK_EVOLUTION.md`. |

**Feito / arquivado (não reabrir sem trabalho novo):**

- **Tag `v1.6.7` + GitHub Release + Docker Hub** — enviado **2026-03-26**.
- **Help-sync / OpenAPI / README `--host`** — passe 2026-03-27.
- **PRs Dependabot** (#134 pypdf, #144 starlette, #147 grupo pip) — mergeados **2026-03-29/31**.
- **Slack** prova de ping — confirmado **2026-03-27** (**CHAN-OK**).
- **Branch protection** (CI + Semgrep) — em execução há semanas; proteção funcional ativa. Checks formais obrigatórios no GitHub ficam opcionais até o operador ativar `enforcement_level` explicitamente.
- **`/help` vs `main.py`** — `test_operator_help_sync.py` verde (3/3); gate de CI garante sincronía contínua.
- **LinkedIn/ATS do fundador** — perfil atualizado (docs/private); ✅ confirmado pelo operador.
- **E-mail / resposta Corporate-Entity-C WRB** — respondido via issue; canal conta. ✅ confirmado pelo operador.
- **Lab-node-01/LMDE → laptop de dev** — laptop de dev na rede há semanas; setup feito. ✅
- **Preparação 1.6.9** — supersedido pela frente 1.7.0 (arquivado 2026-05-13).
- **Release gate #406 / three fronts (Vault → Maestro → GA)** — **1.7.4 GA shipped 2026-06-26**; gate closed per [PUBLISHED_SYNC.md](PUBLISHED_SYNC.md). Maestro spinout / e2e remains separate backlog (private + issues).
- **1.7.0 publicado + CI** — publicado e supersedido (arquivado 2026-05-13).
- **Rodada Gemini + WRB** (2026-04-02) — bundle Gemini feito 2026-05-13 (4 P0/P1 + 6 Warm resolvidos + corpus CPF expandido).
- **Snapshot quantitativo 2026-04-02** — oportunidade expirada; snapshots futuros com data corrente.
- **Recuperação Time Machine** (disco USB) — ✅ confirmado pelo operador.
- **Fatia Gemini Cold** (G-26-* de março) — triados e fechados; rodada maio cobre novo conjunto.

---

## PR de organização (esta pasta)

Se tens **commits locais** que criaram **`docs/ops/today-mode/`**, fecha commits por tema (docs/workflow), corre **`.\scripts\lint-only.ps1`** ou **`check-all`**, depois merge em `main`.
