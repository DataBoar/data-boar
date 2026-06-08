# Carryover do "today mode" (fila viva)

**English:** [CARRYOVER.md](CARRYOVER.md)

**Objetivo:** Uma **lista viva** de itens do operador que atravessam vários `OPERATOR_TODAY_MODE_*` datados. **Fecha, adia com data ou passa para `PLANS_TODO` / issue** — nada imortal sem dono.

**Relacionado:** **`carryover-sweep`** (manhã), **`eod-sync`** (fim do dia), **`docs/private/TODAY_MODE_CARRYOVER_AND_FOUNDER_RHYTHM.md`** (privado).

---

## Fila (edite a tabela abaixo no próprio documento)

| Item | Origem | Estado | Próximo passo / defer |
| ---- | ------ | ------ | ----- |
| **Maestro musl open-core — `alpine-emachines` (5º nó completão)** | Privado **`LAB_OP_FLEET_UPDATE_2026-06-07`** · [OPERATOR_TODAY_MODE_2026-06-08.pt_BR.md](OPERATOR_TODAY_MODE_2026-06-08.pt_BR.md) | ⬜ Pendente | **`completao`** / Maestro **2026-06-08** — incluir host + validar PII/exports/arquivos/storage/DB/web em baremetal **musl/apk**; evidência em **`docs/private/homelab/reports/`** |
| **LAB-OP [#756](https://github.com/FabioLeitao/data-boar/issues/756) — disco mini-bt ~90% + `bw` CLI no Ansible T14** | [OPERATOR_TODAY_MODE_2026-05-29.pt_BR.md](OPERATOR_TODAY_MODE_2026-05-29.pt_BR.md) · `PLANS_TODO.md` § LAB-OP | ⬜ Pendente | **`[U1]`** SSH + liberar espaço no **mini-bt** antes de completão nesse host · **`[U2]`** task Ansible para **`bw`** no T14 — **não** bloqueia release; fechar quando a issue fechar ou adiar com data |
| **Licensing [#719](https://github.com/FabioLeitao/data-boar/issues/719) — bypass JWT via env de dev** | GitHub [P1] · `PLANS_TODO.md` **`[H0][U1]` Licensing enforcement** | ⬜ Pendente | Depois de **#704** [P0] ou se exposição em prod confirmada (**U0**); PR fino **`fix(security)`** + regressão **A6** `license-smoke` |
| **PCI-DSS v4 / prontidão global — ruído PAN + ADR-0052 fase 2 (gates de contexto)** | Sessão operador **2026-05-14** (nota estratégica; fila com dono) | ⬜ Pendente | **Linha dona:** `PLANS_TODO.md` tabela pós-`1.7.4` **S4b** — estender `plugin_schema` + validador + gating no `SensitivityDetector` (proximity opcional / caminho Luhn); calibrar `docs/compliance-samples/compliance-sample-pci_dss.yaml` vs `CREDIT_CARD` embutido; ver `PLAN_YAML_PLUGIN_SYSTEM.md` § *Phase 1b*. Fechar esta linha do carryover quando **S4b** fechar ou adiar com **data** no `PLANS_TODO`. |
| **`v1.7.4-rc` na `main` + pré-release GitHub; Hub estável ainda `1.7.3`** | [OPERATOR_TODAY_MODE_2026-05-11.pt_BR.md](OPERATOR_TODAY_MODE_2026-05-11.pt_BR.md) · [PUBLISHED_SYNC.pt_BR.md](PUBLISHED_SYNC.pt_BR.md) | ✅ Enviado (RC) | Medição controlada **1.7.3 vs 1.7.4-rc** no lab antes de promover; sem mover Hub **`latest`** até **1.7.4** estável. |
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
- **Lab-node-01/LMDE → T14** — T14 na rede há semanas; setup feito. ✅
- **Preparação 1.6.9** — supersedido pela frente 1.7.0 (arquivado 2026-05-13).
- **Gate de release 1.6.8** — supersedido por 1.7.3 + 1.7.4-rc (arquivado 2026-05-13).
- **1.7.0 publicado + CI** — publicado e supersedido (arquivado 2026-05-13).
- **Rodada Gemini + WRB** (2026-04-02) — bundle Gemini feito 2026-05-13 (4 P0/P1 + 6 Warm resolvidos + corpus CPF expandido).
- **Snapshot quantitativo 2026-04-02** — oportunidade expirada; snapshots futuros com data corrente.
- **Recuperação Time Machine** (disco USB) — ✅ confirmado pelo operador.
- **Fatia Gemini Cold** (G-26-* de março) — triados e fechados; rodada maio cobre novo conjunto.

---

## PR de organização (esta pasta)

Se tens **commits locais** que criaram **`docs/ops/today-mode/`**, fecha commits por tema (docs/workflow), corre **`.\scripts\lint-only.ps1`** ou **`check-all`**, depois merge em `main`.
