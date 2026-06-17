# Testes

**English:** [TESTING.md](TESTING.md)

Este documento descreve como executar a suíte de testes e o que cada módulo de teste cobre. Todos os testes devem passar **sem erros ou avisos** (`-W error`). O CI executa o mesmo comando a cada push e pull request.

## Executando os testes

A partir da raiz do projeto:

```bash
# Suíte completa (recomendado; usa addopts do pyproject.toml incluindo -W error)
uv run pytest -v -W error

# Ou confiar apenas nos addopts
uv run pytest -v

# Executar um único arquivo de teste
uv run pytest tests/test_routes_responses.py -v -W error

# Executar testes que correspondem a uma palavra-chave
uv run pytest -v -W error -k "session_id"

# Opcional: lint do docs/private/ ignorado pelo git (Markdown + *.ps1 / *.sh)
uv run pytest -v -W error --include-private
# Ou: INCLUDE_PRIVATE_LINT=1 (mesmo efeito para markdown e scripts privados)
```

**Opcional — `docs/private/`:** Por padrão, os testes de **lint de Markdown** e **sintaxe de scripts** **ignoram** a árvore **`docs/private/`** (gitignored). Para incluí-la localmente (ex.: após editar notas privadas), use **`pytest --include-private`** ou defina **`INCLUDE_PRIVATE_LINT=1`**. Para corrigir Markdown lá: **`uv run python scripts/fix_markdown_sonar.py --include-private`** (ou a mesma variável de ambiente). O **CI não** define essa flag.

**Requisitos:** Python **3.12 ou 3.13** (veja `CONTRIBUTING.md` / `SECURITY.md`), dependências instaladas (`uv sync --group dev` ou `pip install -e .`). Nenhum serviço externo é necessário; os testes usam configs temporários e SQLite em memória ou temporário quando preciso.

## Visão geral dos módulos de teste

| Módulo                                        | Objetivo                                                                                                                                                                                                                                                                                                                                                |
| -------------------------------------         | -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------                                                                                       |
| **test_aggregated_identification.py**         | Mapeamento de categorias, regras de agregação e saída do relatório para agregação de quasi-identificadores (LGPD/compliance).                                                                                                                                                                                                                           |
| **test_api_key.py**                           | Chave de API opcional: quando `api.require_api_key` é true, X-API-Key ou Bearer é obrigatório; GET /health permanece público.                                                                                                                                                                                                                           |
| **test_api_assessment_poc.py**                | POC de autoavaliação GRC: HTML em `/{locale}/assessment` + POST, pack YAML, tier e JWT `dbtier` com **`licensing.mode: enforced`**, export e histórico — referência interna ao plano: `docs/plans/PLAN_MATURITY_SELF_ASSESSMENT_GRC_QUESTIONNAIRE.md`.                                                                                                                                                                                                              |
| **test_api_scan.py**                          | POST /scan dispara auditoria completa usando o config carregado; sessão e comportamento em background.                                                                                                                                                                                                                                                  |
| **test_audit.py**                             | Detecção de sensibilidade: CPF, e-mail, religião, filiação política, classificação de baixa sensibilidade.                                                                                                                                                                                                                                              |
| **test_audit_export.py**                      | Export JSON do audit trail: objeto **`maturity_assessment_integrity`** alinhado ao helper de verificação no DB (`verify_maturity_assessment_integrity`).                                                                                                                                                                                                |
| **test_confidential_commercial_guard.py**     | **Política:** `git ls-files` não pode listar **`docs/private/`**, **`.cursor/private/`** nem **`docs/.../commercial/...`** fora de **`docs/private.example/commercial/`**; basenames em **`docs/`** rastreado não podem coincidir com tokens de estudo de precificação interno (ver docstring do módulo). Pre-commit **confidential-commercial-guard**. |
| **test_csp_headers.py**                       | Cabeçalhos de segurança e Content-Security-Policy no dashboard e páginas de ajuda (sem `unsafe-inline` em script-src).                                                                                                                                                                                                                                  |
| **test_pii_guard.py**                         | **Guarda:** todo arquivo no índice do Git é varrido por literais/regex de PII que só pertencem ao **`docs/private/`** (gitignored); o arquivo externo opcional **`docs/private/pii-patterns.txt`** estende a lista interna. Também sinaliza chaves AWS/GitHub/Slack/Stripe, cabeçalhos PEM e tokens Bearer. Evita reincidência de PII em árvores rastreadas. |
| **test_data_scanner.py**                      | Registro de conectores: filesystem, banco (Postgres), API, resolução de target desconhecido.                                                                                                                                                                                                                                                            |
| **test_format_length_hint.py**                | Hint de comprimento CHAR/VARCHAR do conector → MEDIUM **`FORMAT_LENGTH_HINT_ID`** (parse de tipo declarado, heurísticas de inteiro-like e comprimento de e-mail) — Plano §4.                                                                                                                                                                            |
| **test_rest_connector_format_hint.py**        | Conector REST: escalar JSON → **`connector_data_type`** (`BIGINT`, `VARCHAR(n)` limitado por `max_varchar`) alimentando o hint de comprimento de formato do Plano §4.                                                                                                                                                                                   |
| **test_database.py**                          | Normalização de config (vazio, legado, rate_limit, scan.max_workers), LocalDBManager, sessões, wipe.                                                                                                                                                                                                                                                    |
| **test_detector_entertainment_regression.py** | **Regressão:** classificação só-ML não deve retornar ``HIGH`` + ``ML_DETECTED`` em contexto de letras / Markdown OSS / cifra / **cifra entrelaçada** (linha de acorde + linha de letra); patch em ``predict_proba`` cobre ``ML_POTENTIAL_ENTERTAINMENT``. Roda com ``check-all.ps1``.                                                                   |
| **test_github_workflows.py**                  | Workflows Slack do operador em **`.github/workflows/`** fazem parse YAML; o teste impõe forma **`workflow_run`** de **`slack-ci-failure-notify.yml`**, lista **`workflows:`** upstream e o mesmo **guard de passo de webhook** que nos outros **`slack-*.yml`** que fazem POST (ver [OPERATOR_NOTIFICATION_CHANNELS.pt_BR.md](ops/OPERATOR_NOTIFICATION_CHANNELS.pt_BR.md) §4.1.1). **Não** envia POST ao Slack (precisa GitHub + secret).                                                                                                                                                   |
| **test_docs_markdown.py**                     | Qualidade da documentação: README e docs/USAGE existem, têm título e conteúdo chave; links relativos resolvem; SECURITY.md tem conteúdo.                                                                                                                                                                                                                |
| **test_readme_stakeholder_pitch_contract.py** | Bloco executivo do README (antes de **Visão técnica** / **Technical overview**) mantém os títulos **Farejando com critério** / **Sniffing with judgment** e exclui rótulos só-deck **Data Sniffing** / **Deep Boring** — [ADR 0035](../docs/adr/ADR-0035-readme-stakeholder-pitch-vs-deck-vocabulary.md) (texto canônico em inglês).                         |
| **test_about_version_matches_pyproject.py**   | Metadados de versão alinhados ao `pyproject.toml`; **User-Agent** HTTP de saída **`DataBoar-Prospector/<versão>`** — [ADR 0034](../docs/adr/ADR-0034-outbound-http-user-agent-data-boar-prospector.md) (texto canônico em inglês).                                                                                                                            |
| **test_learned_patterns.py**                  | Padrões aprendidos: coleta (sensibilidade, padrão, filesystem), grava YAML, exclusões.                                                                                                                                                                                                                                                                  |
| **test_logic.py**                             | Lógica de auditoria: CPF no conteúdo, downgrade de letras/tablatura, compatibilidade retroativa dos resultados do scan.                                                                                                                                                                                                                                 |
| **test_minor_detection.py**                   | Detecção de menor: heurísticas de idade/DOB, flag possible_minor, fiação de config, priorização no relatório.                                                                                                                                                                                                                                           |
| **test_maturity_assessment_integrity.py**     | Helpers de selagem HMAC por linha, vetor dourado, detecção de adulteração no SQLite, carregamento do segredo de integridade — [core/maturity_assessment/integrity.py](../core/maturity_assessment/integrity.py).                                                                                                                                      |
| **test_markdown_lint.py**                     | Regras estilo SonarQube/markdownlint em `.md` / `.mdc` (incl. `.cursor/`). Exclui **`private/`** por padrão; opcional **`--include-private`** ou **`INCLUDE_PRIVATE_LINT=1`** para **`docs/private/`**. Veja [Executando os testes](#executando-os-testes).                                                                                             |
| **test_ml_engine.py**                         | MLSensitivityScanner: seed random_state (S6709), hiperparâmetros (S6973), nomenclatura de variáveis locais (S117), comportamento de predict.                                                                                                                                                                                                            |
| **test_rate_limit_api.py**                    | Limite de taxa: 429 quando máximo de scans concorrentes ou min_interval excedido; desabilitado por padrão para configs legados.                                                                                                                                                                                                                         |
| **test_report_path_safety.py**                | Caminhos de relatório/heatmap (`FileResponse`) sob `report.output_dir`: contenção (CodeQL py/path-injection), basenames permitidos, rejeita caminhos fora do diretório configurado.                                                                                                                                                                     |
| **test_report_recommendations.py**            | Recomendações do relatório, overrides, resumo executivo, min_sensitivity, linha/prioridade possible_minor, config_scope_hash.                                                                                                                                                                                                                           |
| **test_report_trends.py**                     | Aba de tendências e informações do relatório (tenant, technician) nos relatórios gerados.                                                                                                                                                                                                                                                               |
| **test_routes_responses.py**                  | Contrato da API e OpenAPI: session_id inválido → 400; 429/400/404 documentados no OpenAPI; página de config usa constante do template.                                                                                                                                                                                                                  |
| **test_scripts.py**                           | Verificações de scripts Shell/PowerShell: sintaxe bash de `prep_audit.sh`, parse do `scripts/commit-or-pr.ps1`. Opcional **`--include-private`**: `*.ps1` / `*.sh` em **`docs/private/`**. Veja [Testes de scripts](#testes-de-scripts).                                                                                                                |
| **test_security.py**                          | Resistência a injeção SQL, validação de session_id (path traversal), uso apenas ORM para session_id, YAML safe_load. Veja [SECURITY.md](../SECURITY.md).                                                                                                                                                                                                |
| **test_sonarqube_python.py**                  | Guardas estilo SonarQube: regex session_id, constantes de resposta/relatório, helpers de refatoração, sem except nu em módulos chave.                                                                                                                                                                                                                   |
| **test_sql_connector.py**                     | Conector SQL: conjuntos de skip por dialeto (Oracle, PostgreSQL com casefold, MSSQL/Snowflake em maiúsculas), `should_skip_schema`, discover (fallback SQLite), amostra em coluna esparsa (SQL com não nulo).                                                                                                                                                                                                         |
| **test_sql_sampling.py**                      | `SamplingManager` / `ColumnSamplePlan` (rótulos + `human_strategy`), `SqlColumnSampleQueryBuilder` por dialeto (`IS NOT NULL`, Oracle `ROWNUM`, MSSQL `TOP` + `WITH (NOLOCK)` — nunca emite o `OPTION (MAX_EXECUTION_TIME)` inválido em T-SQL, PostgreSQL `TABLESAMPLE SYSTEM` em tabela grande + env **`DATA_BOAR_PG_TABLESAMPLE_SYSTEM_PERCENT`**), `column_sample_sql_for_cursor` (tupla de 5 com hint humano), `resolve_sql_sample_limit` e **`DATA_BOAR_SQL_SAMPLE_LIMIT`**, **`resolve_statement_timeout_ms_for_sampling`**.                                                                                                                                                                                |
| **test_sql_table_row_estimate.py**            | Contagem aproximada só por dicionário (`estimate_table_rows`); SQLite retorna `None` sem `COUNT(*)`.                                                                                                                                                                                                                           |
| **test_sampling_policy.py**                   | Precedência de `SamplingPolicy.get_effective_sample_limit` (por tabela → por alvo → padrões `fnmatch` → global); bloco **`sql_sampling`** em `normalize_config`.                                                                                                                                                                                                                                                                                                                                          |
| **test_config_sql_sampling_files.py**         | Mesclagem de fragmentos **`sql_sampling_file`** / **`sql_sampling_files`** (inline ganha), ordem de merge, expansão só com `config_path`, rejeição de path com `..`, alias **`get_effective_limit`**.                                                                                                                                                                                                                                                                                                    |
| **test_pwsh_venv_activate_docs.py**           | **Guarda de docs:** `.md` / `.mdc` rastreados não devem grafar o caminho contíguo **`.venv`…`Scripts`…`activate` sem extensão** para PowerShell (*not recognized* no pwsh). Prefira **`Activate.ps1`** ou **`uv run`** — ver **CONTRIBUTING.md**.                                                                                                      |
| **test_webauthn_rp.py**                       | WebAuthn fase 1a (JSON neutro de fornecedor): `/auth/webauthn/*` com `api.webauthn.enabled`, opções e verificação, status, logout; caminhos negativos (sem credencial, registro duplicado, state inválido); falha de startup sem segredo; config desabilitada retorna 404. Subconjunto: `scripts/smoke-webauthn-json.ps1`. Veja ADR 0033.              |
| **test_webauthn_session_cookie.py**           | Helpers de cookie de sessão pós-verificação assinado (`itsdangerous`) usados pelo fluxo JSON WebAuthn.                                                                                                                                                                                                                                                  |
| **test_webauthn_html_gate.py**                | Gate de sessão HTML e CSRF do WebAuthn para rotas HTML do dashboard quando `api.webauthn` está habilitado (Fase 1b, GitHub #86).                                                                                                                                                                                                                        |
| **test_html_csrf.py**                         | Helpers de token CSRF HTML (`issue_html_csrf_token` / `verify_html_csrf_token`): rejeição de adulteração e de segredo cruzado (WebAuthn Fase 1b).                                                                                                                                                                                                       |
| **test_rbac.py**                              | RBAC do dashboard (GitHub #86 Fase 2): `api.rbac` opt-in com gate de tier Pro via JWT.                                                                                                                                                                                                                                                                  |
| **test_licensing.py**                         | Licenciamento comercial opcional (aberto por padrão): verificação de JWT, claims de tier, helpers de assinatura. Subconjunto: `scripts/license-smoke.ps1`.                                                                                                                                                                                              |
| **test_licensing_fingerprint.py**             | Fingerprint de máquina (`compute_machine_fingerprint`): digest determinístico de 64 hex a partir de hostname + `DATA_BOAR_MACHINE_SEED`; muda quando a seed muda. Subconjunto: `scripts/license-smoke.ps1`.                                                                                                                                             |

## Testes de qualidade e segurança

Esses testes codificam regras **SonarQube** ou de **contrato da API** para que regressões sejam detectadas no CI. A suíte já cobre o **backend via HTTP** (`test_api_scan.py`, `test_routes_responses.py`, …). **Playwright** ou **Selenium** para E2E no browser são opcionais no futuro; prefira ampliar testes de API enquanto o fluxo crítico for exposto por endpoints.

Ao adicionar ou alterar comportamento da API, esquema de config ou regras de qualidade, atualize o módulo de teste relevante e mantenha este documento em sincronia.

- **test_pwsh_venv_activate_docs.py** – Evita que a documentação volte a sugerir ativar o venv no **pwsh** com o caminho sem **`.ps1`** (ver **CONTRIBUTING.md**).

### Testes de scripts

Scripts são validados apenas quanto a **sintaxe e estrutura**; não é necessário root nem rede:

- **prep_audit.sh** – Em não-Windows: `bash -n prep_audit.sh`. Em todas as plataformas: shebang e uso explícito de `exit 1` quando não root. Os testes não executam o script.
- **scripts/commit-or-pr.ps1** – Parse do PowerShell (`Parser::ParseFile`, sem execução); bloco `param` com `ValidateSet('Preview','Commit','PR')`.
- **`docs/private/`** (opcional) – Com **`pytest --include-private`** ou **`INCLUDE_PRIVATE_LINT=1`**, todo **`*.ps1`** em **`docs/private/`** passa por parse; em não-Windows, **`*.sh`** recebe **`bash -n`**. Ignorado se a flag/variável estiver desligada ou o diretório não existir.

### Markdown lint

Arquivos `.md` / `.mdc` do projeto (excl. `.venv`, `.git`, etc.) seguem regras estilo SonarQube/markdownlint (MD009, MD012, MD024, MD036, MD051, MD060, MD031, MD034, tabelas alinhadas). Para corrigir automaticamente em árvores rastreadas: `uv run python scripts/fix_markdown_sonar.py`; use **`--include-private`** ou **`INCLUDE_PRIVATE_LINT=1`** para incluir **`docs/private/`**.

Execute: `uv run pytest tests/test_markdown_lint.py -v -W error`.

## CI

O GitHub Actions (`.github/workflows/ci.yml`) executa:

- **Lint (pre-commit)** — em **Python 3.12**: **`uv run pre-commit run --all-files`** (igual ao **`.pre-commit-config.yaml`**: Ruff check + format, **plans-stats** `--check`, markdown, locale pt-BR, guarda commercial). Localmente: **`uv run pre-commit install`** para rodar no **`git commit`**. O **`tests/test_github_workflows.py`** garante que **`ci.yml`** ainda executa **`pre-commit run --all-files`** (anti-regressão).
- **Testes** — `uv run pytest -v -W error` no Ubuntu para **Python 3.12 e 3.13** (matriz, `fail-fast: false`).
- **Auditoria de dependências** — `uv run pip-audit` após `uv sync` (Python 3.12).
- **SonarQube/SonarCloud** — quando `SONAR_TOKEN` está definido; usa Python 3.12 após os testes passarem.

O CodeQL está em `.github/workflows/codeql.yml`. O mesmo `sonar-project.properties` na raiz do repositório é usado pelo extension no IDE e pelo scanner no CI.

### Workflows Slack do operador (sem teste “vivo” no pytest)

Enviar mensagem ao Slack exige **GitHub Actions** e o secret do repositório **`SLACK_WEBHOOK_URL`**. O **`tests/test_github_workflows.py`** cobre os **`slack-*.yml`** no `origin` (incluindo **`slack-ci-failure-notify.yml`**) para forma YAML e **guard de webhook** ao nível do passo — ver [OPERATOR_NOTIFICATION_CHANNELS.pt_BR.md](ops/OPERATOR_NOTIFICATION_CHANNELS.pt_BR.md) §4.1.1.

| Workflow (nome na aba Actions)     | Arquivo                           | Função                                                       |
| ---------------------------------- | --------------------------------- | ---------------------------------------------------          |
| **Slack operator ping (manual)**   | `slack-operator-ping.yml`         | Teste manual (`workflow_dispatch`)                           |
| **Slack CI failure notify**        | `slack-ci-failure-notify.yml`     | `workflow_run` após **`failure`** dos workflows listados (POST quando o secret existe) |

Montagem pelo operador: [OPERATOR_NOTIFICATION_CHANNELS.md](ops/OPERATOR_NOTIFICATION_CHANNELS.md) §4.1 ([pt-BR](ops/OPERATOR_NOTIFICATION_CHANNELS.pt_BR.md)).

Para montar um **SonarQube Server** em casa (Docker, VM, secrets `SONAR_HOST_URL`, rede com GitHub Actions, IDE/MCP), veja **[SONARQUBE_HOME_LAB.md](ops/SONARQUBE_HOME_LAB.md)** ([pt-BR](ops/SONARQUBE_HOME_LAB.pt_BR.md)).

Para usar a lista de issues do SonarQube de forma automatizada: execute `uv run python scripts/sonar_issues.py` (ou `--json`) com `SONAR_TOKEN` definido; o script usa o `sonar.projectKey` do `sonar-project.properties`.

## Smoke do POC de autoavaliação de maturidade (gate 1)

Subconjunto de **pytest** para o POC de autoavaliação de maturidade (rotas de API, integridade, resumos de batch no DB, paridade do export de audit trail; referência interna ao plano: `docs/plans/PLAN_MATURITY_SELF_ASSESSMENT_GRC_QUESTIONNAIRE.md`), na raiz do repositório:

```powershell
.\scripts\smoke-maturity-assessment-poc.ps1
```

Roda apenas `tests/test_api_assessment_poc.py`, `tests/test_maturity_assessment_integrity.py`, `tests/test_database.py::test_maturity_assessment_batch_summaries_newest_first` e `tests/test_audit_export.py::test_build_audit_trail_maturity_integrity_matches_verify`. **Não** substitui **`.\scripts\check-all.ps1`** antes do merge. **Checklist no browser:** [docs/ops/SMOKE_MATURITY_ASSESSMENT_POC.pt_BR.md](ops/SMOKE_MATURITY_ASSESSMENT_POC.pt_BR.md) §D.

## Smoke de licenciamento (Priority band A6)

Verificação **rápida** dos testes de JWT / licenciamento (sem rede), na raiz do repositório:

```powershell
.\scripts\license-smoke.ps1
```

Executa apenas `tests/test_licensing.py` e `tests/test_licensing_fingerprint.py`. Opcional: mesmo comando no CI (mantenedores: contexto da **Priority band A** em **Interno e referência** em [README.md](README.md) e em [SECURITY.md](../SECURITY.md)).

## Ver também

- **Índice da documentação** (todos os tópicos, ambos os idiomas): [README.md](README.md) · [README.pt_BR.md](README.pt_BR.md).
- [CONTRIBUTING.md](../CONTRIBUTING.md) — Configuração local e fluxo; execute os testes antes de abrir um PR.
- [SECURITY.md](../SECURITY.md) — Versões suportadas e auditoria de dependências.
- [docs/USAGE.md](USAGE.md) · [docs/USAGE.pt_BR.md](USAGE.pt_BR.md) — Comportamento da API e config coberto pelos testes.
