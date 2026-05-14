# Carryover do "today mode" (fila viva)

**English:** [CARRYOVER.md](CARRYOVER.md)

**Objetivo:** Uma **lista viva** de itens do operador que atravessam vários `OPERATOR_TODAY_MODE_*` datados. **Fecha, adia com data ou passa para `PLANS_TODO` / issue** — nada imortal sem dono.

**Relacionado:** **`carryover-sweep`** (manhã), **`eod-sync`** (fim do dia), **`docs/private/TODAY_MODE_CARRYOVER_AND_FOUNDER_RHYTHM.md`** (privado).

---

## Fila (edite a tabela abaixo no próprio documento)

| Item | Origem | Estado | Próximo passo / defer |
| ---- | ------ | ------ | ----- |
| **`v1.7.4-rc` na `main` + pré-release GitHub; Hub estável ainda `1.7.3`** | [OPERATOR_TODAY_MODE_2026-05-11.pt_BR.md](OPERATOR_TODAY_MODE_2026-05-11.pt_BR.md) · [PUBLISHED_SYNC.pt_BR.md](PUBLISHED_SYNC.pt_BR.md) | ✅ Enviado (RC) | Medição controlada **1.7.3 vs 1.7.4-rc** no lab antes de promover; sem mover Hub **`latest`** até **1.7.4** estável. |
| **Workflow `zizmor` (warn-first)** — `.github/workflows/zizmor.yml` + scripts | PR **#354** mergeado **2026-05-11** | ✅ Feito | Advisory local por padrão; enforce com **`-Enforce`** quando a linha de base estiver limpa. |
| **Evidência matriz DB Maestro (all-to-all)** | [LAB_LESSONS_LEARNED_2026_05_10.md](../lab_lessons_learned/LAB_LESSONS_LEARNED_2026_05_10.md) | ⬜ Pendente | Uma rodada consolidada + configs por host em **`docs/private/homelab/reports/`**. |
| **Fechamento sprint curto pós-`1.7.4` (escolher uma)** — S3 CNPJ fase 5, S1 Bandit fase 3, S2 Scope import fase E | `PLANS_TODO.md` H1/U1 | ⬜ Pendente | Após métricas de lab ou no mesmo dia sem slot LAB — **`feature`** + **`check-all`**. |
| **Harness `benchmark-ab` na `main` (PR #229)** — correr `.\scripts\benchmark-ab.ps1` e substituir linhas TBD em `BENCHMARK_EVOLUTION.md` | EOD **2026-04-27** | ✅ Mergeado (CI verde) | Correr benchmark real quando houver janela LAB e registrar deltas de manifest. |
| **LinkedIn/ATS do fundador** (perfil completo) | 2026-04-02 | ⬜ Pendente | Aplicar seção nova em `LINKEDIN_ATS_AND_POSITIONING_PLAYBOOK.pt_BR.md` com headline + about + evidências |
| **Recuperação Time Machine** (disco USB → backup externo P0) | 2026-04-02 | ⬜ Pendente | Seguir `docs/ops/TIME_MACHINE_USB_RECOVERY_AND_REPURPOSE.pt_BR.md` |
| **Branch protection** (checks obrigatórios em `main`) | 2026-03-26 | ⬜ Opcional | Ativar quando quiser CI/Semgrep obrigatórios; baixa urgência |
| **E-mail Corporate-Entity-C WRB** | 2026-03-26 | ⬜ Decidir | Ou foi feito (→ arquivar) ou está deferido indefinidamente — **operator: fechar ou dar data-alvo** |
| **`/help` vs `main.py`** (drift check) | 2026-03-29 | ⬜ Quando houver flags | Após próxima flag CLI/dashboard — `tests/test_operator_help_sync.py` |

**Feito / arquivado (não reabrir sem trabalho novo):**

- **Tag `v1.6.7` + GitHub Release + Docker Hub** — enviado **2026-03-26**.
- **Help-sync / OpenAPI / README `--host`** — passe 2026-03-27.
- **PRs Dependabot** (#134 pypdf, #144 starlette, #147 grupo pip) — mergeados **2026-03-29/31**.
- **Slack** prova de ping (PC + telemóvel) — confirmado **2026-03-27** (**CHAN-OK**).
- **Preparação 1.6.9** — supersedido pela frente 1.7.0 (arquivado **2026-05-13**).
- **Gate de release 1.6.8** (2026-04-02) — supersedido por 1.7.3 estável + 1.7.4-rc (arquivado **2026-05-13**).
- **1.7.0 publicado + CI** (2026-04-17) — publicado e supersedido por 1.7.3 + 1.7.4-rc (arquivado **2026-05-13**).
- **Rodada Gemini + WRB** (2026-04-02) — bundle Gemini feito **2026-05-13** (4 P0/P1 + 6 Warm resolvidos + corpus CPF expandido).
- **Snapshot quantitativo 2026-04-02** — oportunidade expirada; snapshots futuros via `.\scripts\progress-snapshot.ps1` com data corrente.
- **Fatia Gemini Cold** (G-26-* da rodada março) — triados e fechados; rodada maio cobre novo conjunto.

---

## PR de organização (esta pasta)

Se tens **commits locais** que criaram **`docs/ops/today-mode/`**, fecha commits por tema (docs/workflow), corre **`.\scripts\lint-only.ps1`** ou **`check-all`**, depois merge em `main`.

---

## LAB-NODE-01 + LMDE (em paralelo)

Instalação de hardware **fora do Git** — usa **[`docs/ops/LMDE7_LAB-NODE-01_DEVELOPER_SETUP.pt_BR.md`](../LMDE7_LAB-NODE-01_DEVELOPER_SETUP.pt_BR.md)** ([EN](../LMDE7_LAB-NODE-01_DEVELOPER_SETUP.md)) quando o portátil estiver pronto.
