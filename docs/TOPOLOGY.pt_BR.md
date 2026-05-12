# Topologia da aplicação

**English:** [TOPOLOGY.md](TOPOLOGY.md)

Descrição textual dos módulos, classes e funções principais e como eles se conectam.

---

## Pontos de entrada

- **main.py** — CLI: `main()` analisa `--config`, `--web`, `--port`, opcionalmente `--tenant`, `--technician`; carrega config via `config.loader.load_config`; se não for `--web`, cria `AuditEngine(config)`, executa `start_audit(...)` e `generate_final_reports()`; se `--web`, executa uvicorn com `api.routes.app` na porta informada.
- **api/routes.py** — App FastAPI: na inicialização carrega config e cria `AuditEngine`. Rotas da API: POST `/scan`, `/start`; GET `/status`, `/report`, `/list`, `/reports/{session_id}`; PATCH `/sessions/{session_id}` e `/sessions/{session_id}/technician`. POST `/scan_database` aceita tenant e technician opcionais. Dashboard web (Jinja2): GET `/` (dashboard com inputs opcionais de tenant/technician e gráfico de progresso), GET `/reports`, GET/POST `/config`. Estáticos: `/static` → `api/static`.

---

## Config

- **config/loader.py** — `load_config(path)` carrega YAML ou JSON; `normalize_config(data)` normaliza para o esquema unificado: `targets[]`, `file_scan`, `report`, `api`, `ml_patterns_file`, `regex_overrides_file`, `sqlite_path`, `scan.max_workers`. Legacy `databases` + `file_scan.directories` convertidos em `targets`.

---

## Core

- **core/session.py** — `new_session_id()` retorna UUID4 hex (12 chars) + timestamp para a sessão de scan. **Futuro:** avaliar UUID v7 (RFC 9562) para ids ordenáveis no tempo (docstring do módulo e `PLAN_BUILD_IDENTITY_RELEASE_INTEGRITY.md`); não substitui integridade por hash/assinatura.
- **core/database.py** — Modelos **ScanSession**, **DatabaseFinding**, **FilesystemFinding**, **ScanFailure**; **LocalDBManager** com `save_finding`, `save_failure`, `get_findings`, `list_sessions`, `get_previous_session`, `get_previous_sessions`, `create_session_record`, `update_session_tenant`, `update_session_technician`, `finish_session`, etc.
- **core/detector.py** — **SensitivityDetector**: carrega regex (embutido + overrides) e padrões ML; `analyze(column_name, sample_text)` → (sensitivity_level, pattern_detected, norm_tag, confidence). Usa TF-IDF + RandomForest. Helpers: `_load_regex_overrides`, `_load_ml_patterns`.
- **core/scanner.py** — **DataScanner** encapsula SensitivityDetector; `scan_column`, `scan_file_content`, `analyze_data` (retrocompatível).
- **core/connector_registry.py** — `register`, `get_connector`, `list_connector_types`, `connector_for_target`.
- **core/engine.py** — **AuditEngine**: mantém db_manager e scanner; `start_audit()` → session_id; `_run_audit_targets` executa cada target via registry (sequencial ou paralelo); `_run_target` resolve conector e chama `connector.run()`. `generate_final_reports` chama report.generator e opcionalmente write_learned_patterns. Propriedades: `is_running`, `get_current_findings_count`, `get_last_report_path`. Importa conectores para que se registrem.
- **core/learned_patterns.py** — `collect_learned_entries`, `write_learned_patterns` (grava YAML compatível com ml_patterns_file quando `learned_patterns.enabled`).

---

## Conectores

- **connectors/sql_sampling.py** — `SamplingManager` orquestra `SELECT` de amostra por dialeto (filtro **não nulo** antes do teto); `SqlColumnSampleQueryBuilder.build` delega ao mesmo plano por compatibilidade. `resolve_sql_sample_limit` aplica o env opcional **`DATA_BOAR_SQL_SAMPLE_LIMIT`** (clamp **1..10000**). **`core/sampling_policy.py`** resolve o YAML opcional **`sql_sampling.overrides`** (por alvo / por tabela / padrões `fnmatch`) antes desse clamp. `TableSamplingMetadata` opcional (ex.: contagem estimada de linhas) ajusta **rótulos de estratégia** hoje e no futuro habilitará `TABLESAMPLE`/modo prudente ([ADR 0043](adr/ADR-0043-sql-column-sampling-non-null-and-strategy-hook.md); notas em [USAGE.pt_BR.md](USAGE.pt_BR.md)).
- **connectors/sql_connector.py** — **SQLConnector**: connect, close, discover, sample (pede um **`ColumnSamplePlan`** ao `SamplingManager`, registra **estratégia** uma vez por tabela em INFO), run. Registrado para postgresql, mysql, mariadb, sqlite, mssql, oracle.
- **connectors/filesystem_connector.py** — **FilesystemConnector**: walk no path; para `.sqlite`/`.db` com `scan_sqlite_as_db` abre como DB e faz discover+sample+detect; para outros arquivos usa `_read_text_sample` e scanner. `_read_text_sample` extrai texto de txt/csv/pdf/docx/odt/ods/odp/xlsx/pptx/msg/eml. `_scan_sqlite_file_as_db` abre SQLite, discover + sample + detect.
- **connectors/mongodb_connector.py** (opcional) — **MongoDBConnector**: connect, list collections, sample, scanner em nomes de campos + texto. Registrado para mongodb.
- **connectors/redis_connector.py** (opcional) — **RedisConnector**: connect, SCAN keys, scanner em nomes. Registrado para redis.
- **connectors/rest_connector.py** — **RESTConnector**: auth (basic, bearer, oauth2_client, custom); GET em cada path, parse JSON, flatten, scanner, save_finding. Registrado para `api` e `rest`.
- **connectors/smb_connector.py**, **webdav_connector.py**, **sharepoint_connector.py**, **nfs_connector.py** — Conectores para SMB/CIFS, WebDAV, SharePoint, NFS (path = ponto de montagem local); listam/baixam arquivos e usam o mesmo fluxo de scan (ou SQLite-as-DB quando aplicável).

---

## Report

- **report/generator.py** — `generate_report` lê get_findings(session_id), escreve Excel (Report info, Database findings, Filesystem findings, Scan failures, Recommendations, Praise / existing controls, Trends, Heatmap data), chama `_create_heatmap` (PNG). `_praise_rows`, `_trends_rows` (comparação com até 3 sessões anteriores; colunas Prev run 1/2/3 e Note agregada), `_recommendations_rows`.

---

## API

- **api/routes.py** — App FastAPI; arquivos estáticos em `/static`; templates Jinja2 em api/templates. Rotas de API e dashboard (GET /, /reports, /config; POST /scan, /config). Helpers: _get_config_path, _get_config_raw, _save_config_yaml.

---

## Utils

- **utils/logger.py** — get_logger(), setup_live_logger(), log_connection(), log_finding(), notify_violation().

---

## Fluxo de dados (resumo)

1. **Config** → config/loader → dict normalizado.
1. **Engine** → cria LocalDBManager, DataScanner; para cada target, connector_for_target → connector.run(). Para filesystem, repassa scan_sqlite_as_db e sample_limit.
1. **Conectores** → connect, discover (e sample para DB); para filesystem, arquivos .sqlite/.db opcionalmente abertos como SQLite; outros usam _read_text_sample e scanner.
1. **Report** → report/generator lê SQLite, escreve Excel + heatmap.
1. **API** → rotas usam o mesmo AuditEngine; /scan inicia _run_audit_targets em background; /report e /reports/{id} chamam generate_final_reports.

---

## Direção de dependências (sem ciclos)

config.loader, core.session, core.database não importam o projeto. core.detector (opcional yaml/sklearn/pandas). core.scanner → core.detector. core.connector_registry — nenhum. connectors.* → core.connector_registry, core.database, core.scanner, utils.logger. core.engine → registry, database, scanner, session; importa conectores. report.generator → core.database, pandas, openpyxl, matplotlib/seaborn. api.routes → config.loader, core.engine. main → config.loader, core.engine, api.routes, uvicorn.

**Índice da documentação** (todos os tópicos, ambos os idiomas): [README.md](README.md) · [README.pt_BR.md](README.pt_BR.md).
