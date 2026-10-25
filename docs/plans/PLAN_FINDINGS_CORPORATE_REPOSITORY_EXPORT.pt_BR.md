# Plano: Repositório corporativo de findings — export / sync além do SQLite local (médio prazo)

<!-- plans-hub-summary: Export opcional de findings para stores do cliente e tags de catálogo; v1.8.0 #1058 OpenMetadata/DataHub/Atlas + PII-as-quality-check opt-in; discovery somente-leitura (sem write-back na origem) -->
<!-- plans-hub-related: PLAN_DATABRICKS_UNITY_LAKEHOUSE_SCOPE_AND_SCAN.md, PLAN_OBJECT_STORAGE_CLOUD_CONNECTORS.md, PLAN_NOTIFICATIONS_OFFBAND_AND_SCAN_COMPLETE.md, PLAN_FIDESLANG_EXPORT_ADAPTER.md, SECURITY.md, REPORTS_AND_COMPLIANCE_OUTPUTS.md -->

**English:** [PLAN_FINDINGS_CORPORATE_REPOSITORY_EXPORT.md](PLAN_FINDINGS_CORPORATE_REPOSITORY_EXPORT.md)

**Status:** Em andamento (Fases A–C eco SQL/Mongo em `main` via #552; Fase D object storage e clientes de catálogo continuam no backlog; o survey v1.8.0 [#1058](https://github.com/DataBoar/data-boar/issues/1058) permanece aberto — não arquivar)
**Data:** 2026-05-02 (onda v1.8.0: 2026-08-27)
**Autores:** Fabio Leitao
**Prioridade:** H2
**Depende de:** ADR-0048
**Milestone:** v1.8.0
**GitHub:** [#1058](https://github.com/DataBoar/data-boar/issues/1058) (v1.8.x formato de catálogo + PII-as-quality-check)

**Horizonte:** **[H2]** médio prazo; **antecipar** só quando um **prospecto ou contrato nomeado** exigir um sink concreto (MongoDB, um SQL específico, object storage + ingestão no lake, API de catálogo, etc.).

**Sincronizado com:** [PLANS_TODO.md](PLANS_TODO.md)

---

## Problema

Alguns prospectos **corporativos** **não se sentem confortáveis** em tratar **somente** o SQLite **local** do produto (`LocalDBManager` / padrão `audit_results.db` em `core/database.py`) como o **único** store de longa duração de **evidência de scan** e **metadados de sessão**. Podem exigir:

- Warehouses **centrais de segurança / GRC** (SQL ou stores documentais que o cliente já opera),
- Zonas de **data lake** (lotes **Parquet/JSON** consumidos por loaders **Databricks**, **Snowflake**, **BigQuery**),
- Stores **operacionais** (**MongoDB**, **PostgreSQL**, etc.) para dashboards do cliente,
- **Retenção e controle de acesso** na **infraestrutura deles** (RBAC, criptografia em repouso, política de backup).

Hoje o caminho **primário** de persistência é **SQLite** mais saídas **Excel/relatório**. Isso continua válido para muitos deploys; este plano adiciona uma **segunda perna opcional**.

---

## Viabilidade (resposta curta)

**Sim, é tecnicamente viável** **exportar** ou **sincronizar de forma incremental** as **mesmas formas de finding** que o produto já persiste (linhas por sessão, campos **orientados a metadados** — sem payload bruto amostrado em massa no contrato padrão) para backends **escolhidos pelo cliente**. O trabalho é sobretudo:

1. **Esquema de export estável** (JSON versionado ou DDL relacional) mapeando `scan_sessions`, `database_findings`, `filesystem_findings`, falhas e linhas de inventário selecionadas — alinhado ao que [REPORTS_AND_COMPLIANCE_OUTPUTS.md](../REPORTS_AND_COMPLIANCE_OUTPUTS.md) já implica para disciplina de evidência.
1. **Transporte + idempotência** (lote após o scan vs sync agendado; `session_id` + chaves de linha para upserts).
1. **Isolamento de credenciais** (env, cofre ou secret manager — **nunca** config commitada); ver [SECURITY.md](../SECURITY.md).
1. **Módulos por sink** ou uma **interface fina de “sink”** para Mongo vs SQL vs file-drop não bifurcarem o scanner.

**Não-objetivos (padrão):** Replicar o **histórico completo** do esquema SQLite em todo sink no primeiro dia; **transmitir cada amostra de linha** para um DB remoto (fere a história de minimização de metadados, salvo opt-in explícito com aval jurídico).

---

## Postura comercial (formato Pro / Enterprise)

- Posicionar como capacidade **add-on / gated por tier**: **“conectores de repositório corporativo de evidência”** ou **“perfis de export pós-scan”** quando o produto estiver pronto — alinhar a [LICENSING_SPEC.md](../LICENSING_SPEC.md) e flags de tier em runtime quando implementado.
- Até o código existir: **só documentação e ADR**; **nenhuma** promessa de que o tier **Community** inclui sync multi-sink.

---

## Relação com outros planos

| Artefato | Relação |
| -------- | ------- |
| [PLAN_DATABRICKS_UNITY_LAKEHOUSE_SCOPE_AND_SCAN.md](PLAN_DATABRICKS_UNITY_LAKEHOUSE_SCOPE_AND_SCAN.md) | Um **lakehouse** pode ser **sink** (arquivos em lote ou loads SQL) e também **fonte de scan**; manter config de **fonte** vs **sink** separada para não misturar. |
| [PLAN_OBJECT_STORAGE_CLOUD_CONNECTORS.md](PLAN_OBJECT_STORAGE_CLOUD_CONNECTORS.md) | **S3 / Azure Blob / GCS** são destinos naturais de **staging** para lotes JSONL/Parquet antes do ETL do cliente. |
| [PLAN_NOTIFICATIONS_OFFBAND_AND_SCAN_COMPLETE.md](PLAN_NOTIFICATIONS_OFFBAND_AND_SCAN_COMPLETE.md) | **Complementar:** webhooks avisam; **este** plano **pousa** findings estruturados onde o time de **analytics** trabalha. |
| [PLAN_FIDESLANG_EXPORT_ADAPTER.md](PLAN_FIDESLANG_EXPORT_ADAPTER.md) | Visão irmã de taxonomia **só no export** (`data_category`); **não** inventar um segundo dialeto de mapeamento — tags de catálogo reutilizam as mesmas folhas internas de `norm_tag` / pattern. |
| [OBSERVABILITY_SRE.md](../OBSERVABILITY_SRE.md) | Export de **métricas** do produto é trilha **diferente**; não misturar sink de **findings** com Prometheus/OpenTelemetry. |

---

## Esboço em fases (para quebrar depois)

| Fase | Foco | Resultado |
| ---- | ---- | --------- |
| **A — Contrato** | Documentar **JSON canônico de export** (ou pacotes CSV) para um `session_id`: findings + falhas + cabeçalho de sessão; campo de versão; lembrete de política de PII (sem amostras cruas). | O cliente pode **ingerir hoje** com ETL externo **sem** código novo (manual ou o pipeline deles). DDL SQL/Mongo em `docs/deploy/findings_sink_schema.sql` (+ JS Mongo) — ✅ #552 |
| **B — CLI / hook pós-scan** | `scripts/` ou hook do motor: **depois** de `generate_final_reports`, enviar arquivo(s) para um **path** ou **URL pré-assinada**; códigos de saída e logs. | **`--export-findings-sink`** + `scripts/export_findings_to_sink.py` — ✅ #552 |
| **C — Sinks nativos (ordem pela demanda)** | **1)** PostgreSQL / SQL Server **DDL + upsert**; **2)** **collections** MongoDB com índices em `session_id`; **3)** **S3 PutObject** opcional na direção já prevista de object storage. | Eco SQL + Mongo ✅ #552; **S3/Blob/GCS adiado** |
| **D — Governança** | Flags de retenção, **delete-after-export** (opcional, perigoso — documentação pesada), checklist de **RBAC** no sink, linha de audit log “exported to X”. | Conteúdo do pacote de **revisão** Enterprise. |

---

## Critérios de promoção (quando antecipar)

1. Item **contratual** ou de **questionário de segurança**: “findings precisam pousar no **nosso** Mongo/SQL/lake.”
1. **Arquitetura de referência** de um design partner (VPC, private link, janela de lote).
1. **Folga de engenharia** depois de o contrato de export da **Fase A** estar estável (evitar três sinks antes de um esquema acordado).

---

## Reordenar a pilha de to-dos

**Explícito:** Se um cliente exigir a **Fase C** antes de outros itens **[H2]**, [PLANS_TODO.md](PLANS_TODO.md) e as notas de sprint podem **reordenar** — este plano **não** reivindica prioridade fixa vs [PLAN_DATABRICKS_UNITY_LAKEHOUSE_SCOPE_AND_SCAN.md](PLAN_DATABRICKS_UNITY_LAKEHOUSE_SCOPE_AND_SCAN.md) ou o backlog de conectores; **decisão do maintainer** conforme [TOKEN_AWARE_USAGE.md](TOKEN_AWARE_USAGE.md) e pressão comercial.

---

## Changelog

- **2026-08-27:** Survey v1.8.0 **[#1058](https://github.com/DataBoar/data-boar/issues/1058)** — formatos de tag de catálogo (OpenMetadata / DataHub / Apache Atlas) e sidecar opt-in **PII-as-quality-check**; a discovery permanece somente-leitura (sem write-back na origem).
- **2026-04-28:** Plano inicial — **repositório / export de findings** corporativo além do SQLite; formato **Pro/Ent**; gating **customer-pull**; links para lakehouse, object storage, notificações, segurança.

---

## Onda v1.8.0 — formato de catálogo + PII-as-quality-check ([#1058](https://github.com/DataBoar/data-boar/issues/1058))

**Motivo:** Survey competitivo (dossiê privado). **Docs-first** nesta fatia; o código continua no esboço **opcional de export / sink** (Fases **A–D**). Esta onda **não** adiciona conector, cliente REST nem orquestrador de pipeline.

**Invariante (doutrina):** A **discovery do scan permanece somente-leitura**. Um exportador OpenMetadata / DataHub / Atlas é **opt-in** e pode **enviar tags ou entidades para o catálogo do cliente**. **Nunca** deve escrever de volta na **origem varrida** (sem `UPDATE`/`ALTER`/`DELETE` em tabelas, arquivos ou chaves de objeto do cliente). Escrita no catálogo ≠ escrita na origem. O **scan** de lakehouse ([PLAN_DATABRICKS_UNITY_LAKEHOUSE_SCOPE_AND_SCAN.md](PLAN_DATABRICKS_UNITY_LAKEHOUSE_SCOPE_AND_SCAN.md)) continua trilha de **fonte**; este plano é **sink / export**.

**O que não se afirma (alinhado a [COMPLIANCE_AND_LEGAL.md](../COMPLIANCE_AND_LEGAL.md) e [ADR 0025](../adr/ADR-0025-compliance-positioning-evidence-inventory-not-legal-conclusion-engine.md)):** Tags exportadas e **sidecars** de quality-check são **auxílios de inventário e mapeamento técnico** — não determinam juridicamente que uma coluna é dado pessoal sob LGPD/GDPR e **não** são chancela da ANPD (nem de outra autoridade). Um pipeline que coloca um job em quarentena a partir desses hints o faz sob **política do cliente**.

### O que já existe ou já está especificado (não inventar um segundo contrato)

| Superfície | Papel hoje | Relevância para catálogo / DQ |
| ---------- | ---------- | ----------------------------- |
| SQLite local + Excel/relatório | Store primário de evidência | Origem das linhas de finding **orientadas a metadados** (sem amostras brutas em massa por padrão) |
| Fase **A** (este plano) | JSON/CSV de export versionado para um `session_id` | Payload **canônico** que outras ferramentas ingerem — inclusive mapeadores de catálogo |
| [PLAN_FIDESLANG_EXPORT_ADAPTER.md](PLAN_FIDESLANG_EXPORT_ADAPTER.md) | `data_category` lossy opcional **só no export** | Mesmo padrão **só-export, desligado por padrão** das tags de catálogo |
| `--export-remediation-manifest` / JSONL (**#649** / **#1443**) | Localização + `pii_type` + `suggested_profile` | Coordenadas para tags; **não** é cliente de catálogo |
| Sinks de object storage / SQL / Mongo (Fases **B–C**) | Pouso escolhido pelo cliente | Staging **antes** do ETL do catálogo — ainda sem mutar a origem |

### Emissão para catálogo (linguagem do comprador → export já previsto)

SKUs competitivos de “enviar findings ao catálogo” costumam significar **tags em assets que o cliente já cadastrou**. Mapear nomes de vendor para **um** export versionado, depois ids de tag **lossy**:

| Família de catálogo | Pedido típico do comprador | Gancho no produto (sem motor novo nesta fatia de docs) | Barreira |
| ------------------- | -------------------------- | ------------------------------------------------------ | -------- |
| **OpenMetadata** | Tags de classificação / glossário em tabelas e colunas | Mapper opt-in do JSON de export → payload de tag/classificação OM (cliente ou módulo de sink posterior) | Opt-in; **nunca** PATCH no warehouse varrido |
| **DataHub** | Aspects ou tags de dataset / campo de schema | O mesmo JSON de export; o shape de aspect do DataHub é uma **visão**, não um segundo modelo de finding | Desligado por padrão; mapeamento de campos documentado |
| **Apache Atlas** | Classificações de entidade | Nomes de tipo Atlas mapeados de `pattern_detected` / `norm_tag` (lossy, como Fideslang) | O admin Atlas do cliente aplica os tipos; o Data Boar não é dono do Atlas |

**Output-como-input-de-governança:** o catálogo do cliente **recebe** os achados sem redigitar o Excel. Isso é **interop**, não uma afirmação de que o OpenMetadata (ou a ANPD) validou o scan.

### PII-as-quality-check (sidecar opt-in)

Expor findings como **artefato de gate de pipeline** no **estilo** de regra de data-quality (quarentena do **job**, ou emitir um **flag de coluna para o catálogo/orquestrador**):

| Ideia | O que emitir | O que não fazer |
| ----- | ------------ | --------------- |
| **Quarentena** | Sidecar JSON/YAML: `session_id`, ids de asset, severidade, pass/fail do **job de pipeline** | Não pausar nem matar jobs do cliente de dentro do scanner |
| **Flag de coluna** | Flag sugerido para catálogo/orquestrador (`pii_review`, `quarantine_column`) derivado das coordenadas do finding | **Não** `ALTER`/`UPDATE` na coluna de origem |
| **Formato de ferramenta DQ** | Stub opcional posterior no estilo de **resultados de teste** dbt/GE que o cliente conecta | O Data Boar **não** é motor de DQ e não substitui Great Expectations / Soda |

Chaves exatas de CLI/YAML ficam **TBD** até a Fase **B**. Esta PR só trava o contrato **opt-in + origem somente-leitura**.

### Metodologia dos compliance-samples

Mesma disciplina das outras fatias do survey v1.8.0 — **não** criar um dialeto YAML de vendor de catálogo:

1. Manter `norm_tag` nos `docs/compliance-samples/compliance-sample-*.yaml` existentes como **rótulo de framework**, não conclusão jurídica.
2. Ids de tag de catálogo, quando implementados, são uma **visão lossy de export** (mesmo princípio do Fideslang).
3. `recommendation_overrides` posteriores opcionais podem citar “revisar no catálogo” — ainda **não** alteram as origens.
4. Nenhuma afirmação de performance sem arquivo pinado em `tests/benchmarks/`.

### Tabela de execução (docs-first → fatias posteriores)

| Passo | Entregável | Status |
| ----- | ---------- | ------ |
| P1 | Esta seção do plano + resumo no hub + linhas do survey em `PLANS_TODO` | ✅ Feito (PR de docs) |
| P2 | Nota de mapeamento: campos de tag OpenMetadata / DataHub / Atlas ← JSON de export da Fase **A** (tabela lossy; sem código de cliente) | ⬜ Pendente |
| P3 | Esquema de **sidecar** de quality-check opt-in (quarentena / flag de coluna para orquestradores; ainda sem escrita na origem) | ⬜ Pendente |
| P4 | Hook CLI / pós-scan da Fase **B** (esboço já existente) pode emitir JSON de catálogo + sidecar | ⬜ Pendente (tabela de fases já existente) |
| P5 | Sink HTTP nativo de catálogo (customer-pull; ainda sem write-back na origem) | ⬜ Pendente (classe Fase **C**) |

### Revisitar (planos irmãos — só notas do survey)

- [PLAN_FIDESLANG_EXPORT_ADAPTER.md](PLAN_FIDESLANG_EXPORT_ADAPTER.md): manter **uma** família de adapter de taxonomia lossy; vendors de catálogo são **visões** adicionais, não um fork do SQLite.
- [PLAN_DATABRICKS_UNITY_LAKEHOUSE_SCOPE_AND_SCAN.md](PLAN_DATABRICKS_UNITY_LAKEHOUSE_SCOPE_AND_SCAN.md): Unity Catalog como **escopo de scan** permanece separado do **sink de findings**.
- [PLAN_ACTION_PLAN_GENERATOR_POST_SCAN.md](PLAN_ACTION_PLAN_GENERATOR_POST_SCAN.md): ações sugeridas ≠ exportador de catálogo ≠ write-back na origem.
