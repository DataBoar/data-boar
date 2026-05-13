# Auditoria de sincronização da ajuda ao operador — checklist

**English:** [OPERATOR_HELP_AUDIT.md](OPERATOR_HELP_AUDIT.md)

**Objetivo:** Manter todas as **superfícies** onde operadores aprendem sobre flags e opções alinhadas à implementação real. Este documento é uma **lista de verificação / lembrete de auditoria**, não a referência canônica (veja `docs/USAGE.pt_BR.md`, `docs/data_boar.1`, `/help` na web, OpenAPI).

**Quando usar:** Diga **`docs`** + "operator help audit" numa sessão, ou percorra esta lista após adicionar flags de CLI, bodies de API ou controles do dashboard.

**Automação:** Estenda **`tests/operator_help_sync_manifest.py`** ao adicionar comportamento visível ao operador; execute **`uv run pytest tests/test_operator_help_sync.py`**. A regra do Cursor **`.cursor/rules/operator-help-sync.mdc`** se aplica ao editar os caminhos listados; a skill **`.cursor/skills/operator-help-sync/SKILL.md`** resume o fluxo para agentes.

## Superfícies a manter sincronizadas

| Superfície               | Local / como                              | Notas                                                                                                                          |
| -------                  | --------------                            | -----                                                                                                                          |
| **`--help` da CLI**      | `main.py` (`argparse`)                    | Fonte de verdade para flags; testes de contrato em `tests/test_operator_help_sync.py` + manifesto `tests/operator_help_sync_manifest.py`. |
| **Man page**             | `docs/data_boar.1`                        | Synopsis + `.SH OPTIONS`; caminho de instalação varia por distro/pacote.                                                       |
| **USAGE (EN + pt-BR)**   | `docs/USAGE.md`, `docs/USAGE.pt_BR.md`   | Tabelas e seções "Servidor REST API" devem refletir a resolução de bind/porta (`core/host_resolution.py`).                     |
| **Quick start do README** | `README.md`, `README.pt_BR.md`          | Pelo menos linkar para USAGE para flags completas; mencionar `--host` ao discutir exposição.                                   |
| **Ajuda in-app (web)**   | Templates de `/help` no dashboard        | Não deve contradizer USAGE para opções de scan e entrypoints de API.                                                          |
| **OpenAPI / Swagger**    | `api/routes` e relacionados              | Bodies de requisição (ex.: JSON de `/scan`) e query params documentados.                                                       |
| **Deploy / segurança**   | `docs/deploy/DEPLOY*.md`, `SECURITY.md`  | Binding, `API_HOST`, proxy reverso — consistente com o padrão loopback por padrão.                                             |

## Ordem de resolução (bind da API)

Documentado no código: **`main.py --host`** → **`api.host`** → **`API_HOST`** → padrão **`127.0.0.1`**. Qualquer nova sobrescrita (ex.: outra variável de ambiente) deve atualizar `core/host_resolution.py`, USAGE, man e esta tabela, se publicada.

## Concluído recentemente (changelog)

- **2026-04-08 (data soup / stego / help sync):** CLI **`--scan-stego`**, web **`/help`** e marcador em **`tests/operator_help_sync_manifest.py`**, **`docs/data_boar.1`**, **`USAGE*.md`** (formatos Tier 1 + `scan_for_stego`). Execute **`uv run pytest tests/test_operator_help_sync.py`** após alterar superfícies do operador.
- **2026-04 (POC de maturidade — exportação web):** **`GET /{locale}/assessment/export`** (`format=csv|md`, **attachment**) documenta o mesmo POC que **`GET /{locale}/assessment`** — **USAGE** (EN/pt-BR) é canônico para URL, **`api.require_api_key`** e "download vs disco" (sem caminho de servidor em **`report.output_dir`**). CLI **`--export-audit-trail`** continua o snapshot JSON de governança (**`maturity_assessment_integrity`**); **man** (`docs/data_boar.1`) permanece focado em CLI. Testes: **`tests/test_api_assessment_poc.py`**, **`tests/test_api_route_matrix_plan_sync.py`**.
- **2026-04 (POC de maturidade / exportação de auditoria):** **`--export-audit-trail`** JSON inclui **`maturity_assessment_integrity`** (mesmo objeto de **`GET /status`**). Atualizado **`main.py --help`**, **`docs/USAGE*.md`**, **`docs/data_boar.1`**. Testes: **`tests/test_audit_export.py`**, **`tests/test_maturity_assessment_integrity.py`** (vetor HMAC dourado).
- **2026-03:** Conectado **`--host`** à CLI (`main.py`) e estendido man + USAGE; adicionado teste de regressão para `--help` listando flags principais; corrigido texto de binding no USAGE (incorretamente sugeria `0.0.0.0` por padrão para `main.py --web`).
- **2026-03-25:** Transporte do dashboard — **`--https-cert-file`**, **`--https-key-file`**, **`--allow-insecure-http`**; `GET /status` + `/health` **`dashboard_transport`**; marcadores em **`tests/operator_help_sync_manifest.py`**; Docker **`CMD`** explícito em texto claro para imagem padrão.
- **2026-03-25 (hardening de chave de API):** Quando **`api.require_api_key`** é verdadeiro mas nenhuma chave é resolvida, **`main.py --web`** encerra com código **2**; a API retorna **503** em rotas protegidas; **`GET /health`** permanece público. Docs: **USAGE** (EN/pt-BR), **SECURITY** raiz, **`docs/SECURITY*`**, **`docs/ops/API_KEY_FROM_ENV_OPERATOR_STEPS.pt_BR.md`**, **`SECURE_BY_DEFAULT_BLOCKERS_AND_MIGRATION*`**. Testes: **`tests/test_api_key.py`**, **`tests/test_host_resolution.py`**.
- **2026-04-08 (M-LOCALE-V1):** HTML do dashboard usa **`/{locale_slug}/…`** (ex.: **`/en/help`**, **`/pt-br/help`**). **`/help`** sem prefixo (e **`/`**, **`/config`**, **`/reports`**, **`/about`**) faz **302** para o slug negociado; **`GET /help`** em **`tests/test_operator_help_sync.py`** ainda passa porque o **`TestClient` do Starlette segue redirecionamentos** para o template de locale (marcadores inalterados). USAGE / TECH_GUIDE descrevem prefixo vs API JSON; bloco **`locale`** opcional em **`deploy/config.example.yaml`**.

## Próxima verificação (código ↔ docs objetivo)

Após trabalho de realinhamento em superfícies CLI/API/help, da raiz do repo:

```bash
uv run pytest tests/test_operator_help_sync.py -v
```

Em seguida, percorra novamente os **Follow-ups** abaixo (OpenAPI vs bodies de `POST /scan`, README com `--host` ao discutir exposição, `/help` web após novas flags). Esse é o gate de sincronização objetivo — executar antes de marcar a fatia como completa.

## Follow-ups (opcionais)

- [x] **OpenAPI** vs `POST /scan` / `POST /start` — modelo de body é **`ScanStartBody`** em **`api/routes.py`**: `tenant`, `technician`, `scan_compressed`, `content_type_check`, `scan_for_stego`, `jurisdiction_hint` opcionais (booleans/strings nullable). FastAPI serve o schema gerado em **`/openapi.json`** / **`/docs`** com `--web` ativo — verificar após mudanças de schema; USAGE documenta o comportamento de scan.
- [x] **README** one-liner: mencionar **`--host`** ao descrever execuções em LAN/sem Docker — **feito** em EN + pt-BR quick start (bind `127.0.0.1`, `--host 0.0.0.0` apenas com controles de rede); reabrir se o texto de quick start mudar.
- [ ] Re-comparar **`/help` web** após cada nova flag CLI ou controle do dashboard.
