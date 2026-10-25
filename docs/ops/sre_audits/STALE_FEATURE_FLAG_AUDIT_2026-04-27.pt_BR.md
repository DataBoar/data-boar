# Auditoria de feature flags obsoletas — 2026-04-27

> **Gatilho:** handoff Slack `[CLEANUP PROTOCOL: STALE FEATURE-FLAG REMOVAL]`
> do **SRE Automation Agent** (canal `C0AN7HY3NP9`, mensagem
> `1777310318.237219`).
>
> **Branch (entregável da auditoria):** `cursor/sre-automation-agent-protocol-84a1`.
> O agente **não** fez push em nenhuma branch de PR de terceiro: este é o eco
> de auditoria que vive na própria fatia, mesma regra usada no
> `PR_SECURITY_AUDIT_2026-04-27.md` (PR #234).

## TL;DR (compartilhável no Slack)

- :broom: **FLAGS LIMPAS:** *(nenhuma)* — o repositório **não tem feature
  flags obsoletas elegíveis para remoção cirúrgica** em 2026-04-27 16:08 UTC.
- :checkered_flag: **CAMINHO VENCEDOR:** *(sem rewiring)* — toda
  ramificação condicional que o protocolo poderia tocar continua sendo um
  **botão de configuração** ou uma **fronteira open-core ativa**, não um
  rollout vestigial.
- :shield: **CHECK DE PARIDADE:** comportamento de produção inalterado —
  este PR é **documentação + um teste de regressão**. Zero impacto em locks
  de banco, paths de scan ou scoring (ver [§3](#3-arquitetura-defensiva-impacto-zero-em-banco)).
- :gear: **STATUS:** *Candidato encontrado: revisão manual obrigatória* — a
  regra de segurança do passo 3 do protocolo se aplica
  ([§4](#4-por-que-o-protocolo-abortou-regra-de-segurança-do-passo-3)).
  Como follow-up, adicionamos um **teste de regressão** para impedir que um
  SDK Statsig / LaunchDarkly / Unleash / Flagsmith / Split.io entre
  silenciosamente em um PR futuro.

---

## 1. Método (estilo Julia Evans — o que de fato fizemos grep)

O protocolo identifica candidatos a "flag obsoleta" em três classes de
sinal. Cada uma foi pesquisada contra o índice de `main` na base desta
branch e contra a árvore de trabalho.

### 1.1 SDKs de flag de terceiros (alvo principal)

```text
ripgrep -i  'statsig|launchdarkly|launch_darkly|unleash|flagsmith|ldclient|split\.io'  →  0 arquivos
```

Validação cruzada com `pyproject.toml`, `requirements.txt`, `pylock.toml` e
os manifests cargo em `rust/` — nenhum desses fornecedores está instalado.
Isso já cobre o **escopo principal** do protocolo.

### 1.2 Toggles internos de configuração (parecem flag, mas não são)

```text
ripgrep '_enabled|_disabled' --type py
ripgrep 'enable_pro|enable_pro_prefilter|use_density|use_all|use_ntlm'
```

| Símbolo | Onde | Classe |
| ------- | ---- | ------ |
| `api.maturity_self_assessment_poc_enabled` | `config/loader.py`, `api/routes.py`, `tests/test_api_assessment_poc.py` | **Gate POC ajustável pelo operador.** |
| `detection.aggregated_identification_enabled` | `core/aggregated_identification.py`, `tests/test_aggregated_identification.py` | **Toggle de modo de detecção.** |
| `report.jurisdiction_hints_enabled` | `tests/test_jurisdiction_hints.py` | **Toggle de relatório.** |
| `fuzzy_enabled=` | `core/...`, `tests/test_fuzzy_column_match.py` | **Argumento por chamada** (não é gate de runtime). |
| `RATE_LIMIT_ENABLED` | `config/loader.py` (env), `tests/test_rate_limit_api.py` | **Knob de env / config do operador.** |
| `enable_pro` / `enable_pro_prefilter` | `pro/prefilter.py`, `core/discovery_orchestrator.py` | **Fronteira open-core** (refactor ativo — PR #246, ADR 0044). |
| `use_density` (`use_lgpd_density_risk`) | `scripts/generate_grc_report.py` | **Argumento de CLI** para script de dev. |
| `use_all` (wildcard de extensão) | `connectors/{webdav,smb,sharepoint,filesystem}_connector.py` | **Expansão por chamada.** |

Nenhum casa com a definição de "obsoleto" do protocolo. São todos **botões
documentados** (YAML, env ou parâmetros). Remover qualquer um quebraria
comportamento documentado e quebraria a suíte de regressão.

### 1.3 Ramos condicionais mortos perto de leitura de env

```text
ripgrep 'os\.(getenv|environ\.get)\b'  →  todos os hits revisados
```

Os envs interessantes estão **todos ativos**: `DATA_BOAR_LICENSE_*`
(licensing guard, ADR 0044 em andamento), `DATA_BOAR_DASHBOARD_TRANSPORT` /
`DATA_BOAR_DASHBOARD_INSECURE_OPT_IN` (postura HTTPS,
`core/dashboard_transport.py`), `DATA_BOAR_SQL_SAMPLE_LIMIT` /
`DATA_BOAR_SAMPLE_STATEMENT_TIMEOUT_MS` /
`DATA_BOAR_PG_TABLESAMPLE_SYSTEM_PERCENT` /
`DATA_BOAR_MSSQL_TABLESAMPLE_SYSTEM_PERCENT` (válvulas de alívio —
[`docs/ops/inspirations/DEFENSIVE_SCANNING_MANIFESTO.md`](../inspirations/DEFENSIVE_SCANNING_MANIFESTO.md) §2),
`DATA_BOAR_MATURITY_INTEGRITY_SECRET` (selo HMAC),
`DATA_BOAR_WEBAUTHN_TOKEN_SECRET`, `DATA_BOAR_MACHINE_SEED`,
`DATA_BOAR_ALLOW_DESTRUCTIVE_REPO_OPS` (opt-in destrutivo coberto por
`tests/test_primary_windows_destructive_repo_ops_guard.py`).

Nenhuma leitura de env protege um caminho "100 % rolado" que pudesse ser
deletado com segurança.

---

## 2. Sidequest protection (escudo de PR aberto)

Pelo protocolo: *"se uma flag for tocada por um PR aberto, ABORTE a limpeza
para aquela flag específica para evitar merge hell."*

`gh pr list --state open` no momento da auditoria:

| PR | Título | Toca código com cara de flag? |
| -- | ------ | ----------------------------- |
| **#246** | `feat(licensing): unified feature_gate facade for the open-core boundary (ADR 0044)` | **Sim — todo o módulo tier_features / feature_gate.** |
| **#243** | `docs(plans): RFC Slice 5 — Enterprise Hardening (gap analysis + reprioritization)` | Sobreposição de docs com o roadmap de tiers. |
| **#235 / #236 / #232** | Slices de doutrina Pro vs OpenCore | Toca `pro/` e `core/detector.py`. |
| **#244** | `feat(report): DPO/CISO action-plan layer — LGPD/GDPR mapping + risk heatmap` | Toca `report/` (área de jurisdiction-hints). |
| **#240** | `fix(security): close protocol-relative open-redirect in WebAuthn login safe_next_path` | Toca settings de webauthn (gate por env). |
| **#238** | `fix(security): drop bogus T-SQL OPTION (MAX_EXECUTION_TIME) on MSSQL sampling` | Toca sampling MSSQL (válvula de alívio). |
| **#234** | `docs(ops): SRE security audit of open PRs (2026-04-27)` | Auditoria irmã; mesma família. |
| **#233** | `fix(ci): move SLACK_WEBHOOK_URL guard out of job-level if:` | Apenas superfície de CI. |

**Conclusão:** todo candidato alcançável está "tocado em PR aberto". A
trava de segurança **aborta** para cada um.

---

## 3. Arquitetura defensiva (impacto zero em banco)

Esta auditoria entrega **duas coisas** e zero mudança de comportamento:

1. `docs/ops/sre_audits/STALE_FEATURE_FLAG_AUDIT_2026-04-27.md` (este
   arquivo) e seu par pt-BR.
2. `tests/test_no_third_party_feature_flag_sdks.py` — somente leitura, faz
   parse de `pyproject.toml` / `requirements.txt` / `pylock.toml` e roda
   grep contra a árvore Python rastreada procurando marcadores conhecidos
   de fornecedor.

Pelo [`docs/ops/inspirations/DEFENSIVE_SCANNING_MANIFESTO.md`](../inspirations/DEFENSIVE_SCANNING_MANIFESTO.md):

- **Sem DDL, sem objetos temporários, sem shared lock.** O teste novo não
  abre conexão de cliente — só lê arquivos.
- **Sem `ORDER BY` em sampling automático.** Não se aplica; nenhum código
  de sampling é tocado.
- **Cobertura sobre veracidade:** o teste pode *deixar passar* o nome de
  um fornecedor zero-day (a lista é finita), mas não pode mentir sobre o
  que viu. Listamos os fornecedores explicitamente no módulo do teste para
  que um operador estenda a lista com um PR de uma linha.

Pelo [`docs/ops/inspirations/THE_ART_OF_THE_FALLBACK.md`](../inspirations/THE_ART_OF_THE_FALLBACK.md):

- O teste lê cada manifest com **`encoding="utf-8"`** e tolera arquivo
  ausente (repo vazio, checkout parcial) **degradando para um diagnóstico
  claro** em vez de estourar `FileNotFoundError`. É a regra
  "diagnóstico ao cair".

---

## 4. Por que o protocolo abortou (regra de segurança do passo 3)

O passo 3 do protocolo Slack diz:

> *"Se a remoção exigir mudar mais de 3 arquivos relacionados para
> 'consertar' a arquitetura, é complexo demais para automação. ABORTE e
> reporte como 'High Risk Manual Cleanup'."*

O único candidato *parcial* que o agente encontrou foi a fronteira
open-core — `pro/prefilter.py::get_prefilter(enable_pro=...)` mais o
chamador em `core/discovery_orchestrator.py` mais o mapa de tiers da
licensing. Limpar de forma decente envolve no mínimo:

1. `pro/prefilter.py`
2. `core/discovery_orchestrator.py`
3. `core/licensing/tier_features.py`
4. `core/licensing/runtime_feature_tier.py`
5. `tests/test_prefilter_contract.py`
6. `tests/test_tier_features_open_core_subscription.py`

Isso já é o tema do PR #246 (`feat(licensing): unified feature_gate facade
for the open-core boundary (ADR 0044)`). Mexer aqui criaria exatamente o
merge hell que a regra "Sidequest Protection" foi escrita para evitar.

→ **Abort. Report. Echo.** — exatamente o que o protocolo manda.

---

## 5. Cinto de segurança contra regressão (o que de fato saiu)

`tests/test_no_third_party_feature_flag_sdks.py` garante:

1. Os manifests de dependência (`pyproject.toml`, topo de
   `requirements.txt`, seção relevante de `pylock.toml`) **não** contêm as
   substrings `statsig`, `launchdarkly`, `ldclient`, `unleash`, `flagsmith`
   ou `splitio` (case-insensitive, em linhas de nome de dependência).
2. Nenhum **arquivo Python rastreado** (exceto `tests/`, `docs/` e os
   próprios paths desta auditoria) importa esses fornecedores.

Se um PR futuro quiser introduzir um desses SDKs, o teste falha alto e
força o autor a (a) abrir um ADR, (b) atualizar a allow-list do teste
explicitamente, (c) parear com plano documentado de rollout + sunset.
É o cinto que o protocolo pediu, em código.

---

## 6. Próximos passos sugeridos (operador, GTD)

| # | Dono | Ação |
| - | ---- | ---- |
| 1 | Mantenedor | Mergear o **PR #246** (facade `feature_gate` open-core, ADR 0044) — esse é o "caminho vencedor" real para consolidação dos gates. |
| 2 | Mantenedor | Reexecutar esta auditoria como cron de 30 dias após #246 mergear; espere mais candidatos com a fronteira uniformizada. |
| 3 | Colaboradores | Se for adicionar um SDK de flag de terceiro, atualize **ao mesmo tempo** `tests/test_no_third_party_feature_flag_sdks.py` **e** `docs/adr/` (ADR novo) no mesmo PR. |

---

## 7. Forma (inspiração LMDE de issue de bug fix)

Em forma, esta auditoria segue o mesmo molde de
[`linuxmint/live-installer#177`](https://github.com/linuxmint/live-installer/issues/177)
e
[`linuxmint/live-installer#178`](https://github.com/linuxmint/live-installer/issues/178):
reprodução exata (os greps acima), a menor afirmação que casa com a
evidência ("nenhuma flag obsoleta elegível"), a regra de segurança que fez
o agente parar (passo 3) e o teste de regressão que evita reincidência.

---

*Gerado pelo Data Boar SRE Automation Agent em 2026-04-27, fatia
`cursor/sre-automation-agent-protocol-84a1`. Equivalente em inglês:
[`STALE_FEATURE_FLAG_AUDIT_2026-04-27.md`](STALE_FEATURE_FLAG_AUDIT_2026-04-27.md).*
