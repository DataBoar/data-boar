# Carryover do "today mode" (fila viva)

**English:** [CARRYOVER.md](CARRYOVER.md)

**Objetivo:** Uma **lista viva** de itens do operador que atravessam vários `OPERATOR_TODAY_MODE_*` datados. **Fecha, adia com data ou passa para `PLANS_TODO` / issue** — nada imortal sem dono.

**Relacionado:** **`carryover-sweep`** (manhã), **`eod-sync`** (fim do dia), **`docs/private/TODAY_MODE_CARRYOVER_AND_FOUNDER_RHYTHM.md`** (privado).

---

## Fila (edite a tabela abaixo no próprio documento)

| Item | Origem | Estado | Próximo passo / defer |
| ---- | ------ | ------ | ----- |
| **Desacelerar — refil de token ~2026-09-09** | Operador **2026-08-30** EOD | 🔄 Ativo | Manhãs só Tier A; sem maratona de agente; **`feature`/`deps`** adiados salvo **U0** em `main`. Hoje: [OPERATOR_TODAY_MODE_2026-08-31.pt_BR.md](OPERATOR_TODAY_MODE_2026-08-31.pt_BR.md). |
| **#1840 mapa da fila — PR #1841** | [#1840](https://github.com/DataBoar/data-boar/issues/1840) · [PR #1841](https://github.com/DataBoar/data-boar/pull/1841) | 🔄 PR aberto | Mergear com CI verde (`Closes #1840`); regen: `scripts/issue_queue_sequencing_map.py`. |
| **#1709 guard PR operator-gated — PR #1832** | [#1709](https://github.com/DataBoar/data-boar/issues/1709) · [PR #1832](https://github.com/DataBoar/data-boar/pull/1832) | ✅ Mergeado **2026-08-30** | Operador: **SSHSIG attestation when gated** no ruleset **`main-gate-pii`**. |
| **Give-back Heptapod / Codeberg (AIIDCOBPP #63)** | [data-boar-shared#63](https://github.com/DataBoar/data-boar-shared/issues/63) | ⬜ Decantar | **Sem contato upstream** até após **09/09**. Heptapod `projects_limit: 0`. |
| **Hygiene milestone — 3 abertas sem milestone** | [ISSUE_QUEUE_SEQUENCING_MAP.md](../ISSUE_QUEUE_SEQUENCING_MAP.md) **2026-08-30** | ⬜ Opcional | `#696`, `#697`, `#1538` — [#1522](https://github.com/DataBoar/data-boar/issues/1522). |
| **#552 sink de achados — PR #1816** | [#552](https://github.com/DataBoar/data-boar/issues/552) · [PR #1816](https://github.com/DataBoar/data-boar/pull/1816) | ✅ Mergeado | **#552** **CLOSED** — não fechar manualmente. |
| **#553 relatórios multi-formato — Part A ODS + allowlist de caminho** | Sessão **2026-08-28** · [#553](https://github.com/DataBoar/data-boar/issues/553) · branch `feat/report-multiformat-553` | 🔄 WIP sem commit | HIGH do Bugbot: `_REPORT_FILENAME_PATTERN` agora `.xlsx`\|`.ods`. Commit da Part A depois do `check-all`; Part B (pandoc GRC) em seguida. **Não** empilhar na #1816. |
| **#1061 tombstone DSAR — não é escopo do Boar** | [#1061](https://github.com/DataBoar/data-boar/issues/1061) · [tidy-tortoise#14](https://github.com/DataBoar/tidy-tortoise/issues/14) | ✅ Fechada (not planned) | Milestone **v1.8.0** removido **2026-08-28**. Residual **`docs`:** tirar o texto de survey restante em `PLANS_TODO.md`. |
| **Drift de Status do plano de observability lab-op (#1542)** | Sessão lab **2026-08-11→12** · [PLAN_LAB_OP_OBSERVABILITY_STACK.md](../../plans/PLAN_LAB_OP_OBSERVABILITY_STACK.md) | ✅ Feito | Fechado via PR **#1545** (**2026-08-12**). Phase D (Graylog) ainda **não** adotada. |
| **Gaps OTel de produto — LoggerProvider + oneshot + plano preflight** | [#1529](https://github.com/DataBoar/data-boar/issues/1529) · [#1535](https://github.com/DataBoar/data-boar/issues/1535) · [#1540](https://github.com/DataBoar/data-boar/issues/1540) | ✅ Feito (produto/plano) | **#1544 / #1547 / #1548** em `main` **2026-08-12**. Residual **código:** [maestro#32](https://github.com/DataBoar/maestro/issues/32) (linha abaixo). |
| **Preflight OTel Maestro (maestro#32)** | [maestro#32](https://github.com/DataBoar/maestro/issues/32) · desbloqueada pelo fechamento da [#8](https://github.com/DataBoar/maestro/issues/8) | ⬜ Pendente | Implementar em **DataBoar/maestro** `core/`/`engine/` — não no data-boar. |
| **Links do plano de packaging nativo (#1541) + CI Windows (#1427)** | [#1541](https://github.com/DataBoar/data-boar/issues/1541) · [#1427](https://github.com/DataBoar/data-boar/issues/1427) · [#1467](https://github.com/DataBoar/data-boar/issues/1467) | 🔄 #1541 fechada; #1427 ainda aberta | Job `windows-latest` (#1427) ainda bloqueia MSI/winget (#1467). |
| **Sidequest doutrina bestiário (#994) — 10 repos, SOUL vault → DOUTRINA + ADRs** | Sessões **2026-07-01**–**03** · `docs/private/commercial/bestiais/` · vault `bestiais/` | 🔄 Em progresso | **Feito:** inventário honesto; Homing Robin birth-triplet **pushado**; rascunhos locais Ferret / Sage / Stoat (02/jul). **Próximo:** 7 repos + **um PR por repo**. **Maestro** fase 1 **PR #9** mergeado **2026-07-20** (linha abaixo fechada). |
| **Maestro — migração fase 1 + companion purge (#8)** | `DataBoar/maestro` · `docs/ops/CURSOR_ECOSYSTEM_ONBOARDING.md` · data-boar **#1551** | ✅ Feito | Fase 1 **PR #9** (**2026-07-20**). Spinout **#8** fechada **2026-08-12** — data-boar **#1551** removeu `scripts/maestro/`; consumidores usam **`MAESTRO_ROOT`** / sibling via `scripts/Resolve-MaestroRoot.ps1`. Gate do operador: **ADR-0001 Proposed → Accepted**. |
| **#828 scan_failures — open-core em `main`** | PR **#1146** mergeado **2026-07-03** | 🔄 Parcial | Zip/7z/PDF + Bugbot. Issue **#828** aberta para Pro/fixtures/plano. |
| **Housekeeping planos (#91) + survey #1062** | [OPERATOR_TODAY_MODE_2026-06-29.pt_BR.md](OPERATOR_TODAY_MODE_2026-06-29.pt_BR.md) | ✅ Feito | **#91** mergeado · **#1062** mergeado **2026-06-30**. Residual: branches **`houseclean/plans-drift-archive-91`** / **`plans-wave-2`**. |
| **Fila Dependabot (`deps`) — landar ou superseder local** | `gh pr list` **2026-08-28** · skill **dependabot-recommendations** · ADR-0069 **`rpds-py<2026`** | 🔄 Reaberta | **Novos 2026-08-28:** **#1802** setup-uv **10** · **#1803** claude-code-action · **#1805** CodeQL analyze · **#1804** distroless · **#1807** grupo uv-minor-patch · **#1808** sentence-transformers **6** (major) · **#1810** types-pyyaml. Fila **2026-08-17** tinha sido limpa. Triar **um** PR; não mergear majors às cegas. |
| **#1586 TCP peer pin (Mongo/Redis/SQL)** | Survey + design · slices A–F | ✅ Feito | **Fechada 2026-08-17** (UTC) no merge de **#1603**. Matriz em `main`: Postgres **#1589** · Mongo **#1591** · testes **#1593** · harden **#1594** · Redis **#1596** · MySQL **#1597** · SSOT mssql **#1598** / **#1588** · pin MSSQL **#1600** · Oracle **#1603**. |
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
