# Segurança: correções, testes e orientações para o técnico

**English:** [SECURITY.md](SECURITY.md)

Este documento resume as **medidas de segurança de severidade crítica e alta** implementadas na aplicação, os **testes de regressão** que as protegem e **recomendações para técnicos**, para que você saiba o que observar ao configurar e operar a ferramenta de auditoria.

Para política completa, versões suportadas, auditoria de dependências e como reportar vulnerabilidades, consulte **[SECURITY.md](../SECURITY.md)** ([pt-BR](../SECURITY.pt_BR.md)).

---

## O que está protegido (e como)

| Área                                          | Proteção                                                                                                                                                                                                                                                                                                                                                                                                       | Testes de regressão                                                                                                                                                             |
| ------                                        | ----------                                                                                                                                                                                                                                                                                                                                                                                                     | ----------------------                                                                                                                                                          |
| **Injeção de credenciais em URLs de conexão** | Usuário e senha de banco são **codificados para URL** ao montar as strings de conexão (conector SQL, conector MongoDB). Senhas com `@`, `:`, `/` ou `#` não quebram mais o parsing da URL nem são interpretadas como host/caminho.                                                                                                                                                                             | `test_sql_connector_build_url_encodes_password_special_chars`, `test_sql_connector_build_url_encodes_user_with_at`, `test_mongodb_connector_uri_encodes_password_special_chars` |
| **Injeção SQL**                               | Nomes de tabela/coluna em SQL dinâmico vêm do inspetor do banco (discover), não de entrada do usuário. Identificadores são escapados por dialeto (aspas duplas ou backtick). `session_id` é usado apenas via ORM/consultas parametrizadas.                                                                                                                                                                     | `test_sqlite_identifier_escaping_prevents_second_statement`, `test_sql_connector_sample_uses_escaped_identifiers_sqlite`, `test_database_filters_use_orm_not_raw_sql`           |
| **Path traversal**                            | O `session_id` nos caminhos da API é validado com um padrão estrito (alfanumérico e sublinhado, 12–64 caracteres) antes do uso em caminhos de arquivo. Valores inválidos retornam HTTP 400. Fragmentos **`sql_sampling_file`** ficam sob o diretório do config. | `test_session_id_validation_rejects_dangerous_patterns`; `tests/test_config_sql_sampling_files.py` |
| **Config / YAML**                             | O config é carregado apenas com `yaml.safe_load` (sem deserialização de objetos Python arbitrários). Tags YAML maliciosas (ex.: execução de código) são rejeitadas.                                                                                                                                                                                                                                            | `test_config_save_uses_safe_load`, `test_config_loader_uses_safe_load_not_load`                                                                                                 |
| **Exposição do endpoint de config**           | Quando `api.require_api_key` é true, GET `/config` retorna **401** sem uma chave de API válida, de modo que o arquivo de config bruto (que pode conter senhas e segredos) não fica exposto a usuários não autenticados.                                                                                                                                                                                        | `test_config_endpoint_requires_api_key_when_required`                                                                                                                           |
| **Acesso a relatórios e heatmap**             | Os endpoints de relatório e heatmap (`/report`, `/heatmap`, `/reports/{session_id}`, `/heatmap/{session_id}`) validam o formato do `session_id` antes (padrão estrito, 12–64 caracteres). IDs inválidos retornam **400**; sessão desconhecida ou inexistente retorna **404**. Não se distingue “ID inválido” de “sessão não encontrada” para IDs desconhecidos, evitando enumeração e vazamento de informação. | Mesmo que path traversal; handlers retornam 404 quando não há dados.                                                                                                            |
| **Logs de texto de auditoria (`audit_*.log`)** | Depois da normalização do config, cada target recebe um **`audit_log_name`** único (higienizado a partir de `name`) para não colidir em linhas de log. Em filesystem, linhas **Connected** e **Finding** evitam caminho absoluto bruto: raiz de varredura como `pasta?8-hex`, arquivos como caminho POSIX **relativo** à raiz resolvida, ou `audit_log_name?12-hex` quando o arquivo resolve **fora** dessa raiz (ex.: symlink). O SQLite/Excel do relatório continua sendo a evidência canônica; veja **docs/USAGE.md** (formato do audit log). | `tests/test_audit_log_display.py`, `tests/test_database.py` (`test_normalize_config_sets_unique_audit_log_names`) |

Esses testes estão em **`tests/test_security.py`** e nos testes de audit log acima. Executar `pytest tests/test_security.py tests/test_audit_log_display.py -v` com frequência (ex.: no CI) ajuda a garantir que essas proteções não sejam removidas por engano.

---

## Recomendações para técnicos

- **Validação de tenant e técnico:** Os valores de tenant e técnico (corpo de início de varredura, PATCH de sessão, varredura via config) são validados quanto ao tamanho máximo e caracteres permitidos (imprimíveis, sem caracteres de controle), depois trim e sanitizados antes do armazenamento; entrada inválida ou excessiva é rejeitada ou truncada para que relatórios e o dashboard nunca exibam valores não sanitizados.
- **Limite de tamanho do corpo da requisição:** A API rejeita requisições cujo corpo exceda **1 MB** (ex.: POST `/config`, POST `/scan`, POST `/scan_database`) com **HTTP 413 Payload Too Large**, inclusive transferência chunked sem `Content-Length`.
- **Política de logging:** Chaves de API, senhas e strings de conexão nunca são gravadas em log; detalhes de falha e mensagens de exceção são redigidos (ex.: URLs de conexão e valores no estilo `password=` / `api_key=` mascarados) antes de serem registrados.
- **Audit log vs relatório:** Os logs de texto (`audit_YYYYMMDD.log`) usam rótulos **únicos e higienizados** por target (`audit_log_name`) e localizações de filesystem **redigidas**, conforme **docs/USAGE.pt_BR.md**. Não interprete a terceira coluna do log como caminho literal do SO quando aparecer `nome?hex`; use a linha no banco/relatório para o caminho armazenado. Se a forma `target?hash` para arquivos fora da raiz for pouco clara na operação, uma opção futura poderia ser **só nome de arquivo** mais hash — abra uma issue se precisar desse toggle.
- **Senhas com caracteres especiais:** Você pode usar com segurança senhas de banco ou MongoDB que contenham `@`, `:`, `/` ou `#`. A aplicação as codifica ao montar as URLs de conexão. Nenhuma configuração extra é necessária.
- **Proteger o config na interface:** A página **Configuração** (GET `/config`) exibe e permite editar o arquivo de config principal. **GET `/config` sempre redige valores secretos** (senhas, chave de API, tokens, client_secret, etc.) antes de enviar o YAML ao navegador, para que a interface nunca exiba nem transmita segredos em texto claro; ao salvar, placeholders são mesclados com o arquivo atual para não sobrescrever os segredos reais. Se a API estiver exposta a usuários ou redes não confiáveis, defina **`api.require_api_key: true`** e forneça uma chave de API forte (ou `api.api_key_from_env`).
- **Chave de API vs /health:** **`GET /health`** permanece **sem autenticação** (liveness para orquestradores). Demais rotas exigem a chave quando habilitado. **401** = chave ausente ou inválida; **503** = `require_api_key` true porém chave não resolvida; **`main.py --web` encerra com código 2** antes de escutar nesse caso. Veja **[SECURITY.pt_BR.md](../SECURITY.pt_BR.md)** (chave opcional), **[USAGE.pt_BR.md](USAGE.pt_BR.md)** (Autenticação) e **[SECURE_DASHBOARD_AUTH_AND_HTTPS_HOWTO.pt_BR.md](ops/SECURE_DASHBOARD_AUTH_AND_HTTPS_HOWTO.pt_BR.md)** ([EN](ops/SECURE_DASHBOARD_AUTH_AND_HTTPS_HOWTO.md)).
- **Arquivo de config e segredos:** Restrinja as permissões do arquivo de config (ex.: `chmod 600` em `config.yaml`) para que apenas usuários confiáveis leiam. **Não faça commit** de `config.yaml` ou de qualquer arquivo com credenciais no controle de versão; use **`config.example.yaml`** (ou **`deploy/config.example.yaml`**) como modelo e mantenha o config local no **`.gitignore`** (o projeto ignora `config.yaml`, `config.local.yaml` e `*.vault`). Prefira armazenar segredos em variáveis de ambiente (ex.: `pass_from_env`, `api_key_from_env`). Veja **docs/USAGE.md** (Configuration) e **docs/plans/PLAN_SECRETS_VAULT.md** (Phase A).
- **Session IDs nas URLs:** A API usa `session_id` em caminhos (ex.: `/reports/{session_id}`). Apenas valores que seguem o padrão permitido (alfanumérico e sublinhado, 12–64 caracteres) são aceitos; qualquer outro retorna 400. Isso evita path traversal por session IDs forjados.
- **Notificações ao operador (webhooks):** O bloco opcional `notifications` pode enviar resumos de varredura para Slack, Teams, Telegram ou um URL genérico. Trate URLs de webhook e tokens de bot como segredos; prefira `${VAR_DE_AMBIENTE}` no YAML ou só variáveis de ambiente. Veja **`docs/USAGE.pt_BR.md`** (Notificações ao operador) e a política de segurança em **`SECURITY.pt_BR.md`**. O envio repete em falhas transitórias; isso **não** substitui TLS nem política de rede.
- **Implantação:** Quando o dashboard ou a API estiver exposto à internet ou a redes não confiáveis, execute atrás de um **proxy reverso** com **TLS** e autenticação adequada. Use a chave de API opcional e o rate limiting como camada extra; veja **SECURITY.md** e **docs/deploy/DEPLOY.md** (Security and hardening).
- **Downloads de relatório e heatmap:** Os endpoints de relatório e heatmap só retornam dados após validar o **formato** do `session_id`. Formato inválido retorna 400; formato válido mas sessão desconhecida ou inexistente retorna 404. Assim evita-se enumeração de sessões e vazamento de informação (sem distinção 403 vs 404 para sessões desconhecidas).

---

## Filosofia de Resposta a Incidentes

O Data Boar é uma ferramenta de detecção de dados pessoais e sensíveis. O padrão com que trata o próprio repositório precisa ser ao menos tão rigoroso quanto o que recomenda aos clientes.

Não afirmamos um histórico perfeito. Afirmamos uma **resposta determinística**.

Quando ocorreu um incidente de higiene no histórico do projeto, a resposta foi:

1. **Encontrar:** auditoria completa do histórico via `scripts/pii_history_guard.py --full-history` e clone limpo auditado via `scripts/pii-fresh-clone-audit.ps1`.
2. **Corrigir:** remediação do histórico via `git filter-repo`; todas as tags anteriores do Docker Hub depreciadas; Golden Clean Slate publicado como `v1.7.2-safe`.
3. **Construir:** guardrails determinísticos em camadas implementados:
   - `tests/test_pii_guard.py` — padrões em arquivos rastreados (regex + literais codificados)
   - `scripts/gatekeeper_audit.py` — gate de arquivos staged contra seeds privados do operador
   - `.pre-commit-config.yaml` — hooks em todo commit, todas as plataformas
   - `scripts/pii_history_guard.py` — gate anti-reincidência de branch (`origin/main..HEAD`)
4. **Verificar:** cadência em camadas (semanal / mensal / trimestral) com gate de revisão manual obrigatório antes de marcar SAFE — documentado em [PII_PUBLIC_TREE_OPERATOR_GUIDE.pt_BR.md](ops/PII_PUBLIC_TREE_OPERATOR_GUIDE.pt_BR.md) ([EN](ops/PII_PUBLIC_TREE_OPERATOR_GUIDE.md)).
5. **Governar:** [ADR-0018](adr/ADR-0018-pii-anti-recurrence-guardrails-for-tracked-files-and-branch-history.md) (arquitetura de guardrails) e [ADR-0019](adr/ADR-0019-pii-verification-cadence-and-manual-review-gate.md) (cadência de verificação) são decisões arquiteturais permanentes — não workarounds, não to-dos.

Encontrar um incidente de sensibilidade no próprio repositório e responder com controles permanentes e verificáveis é um sinal de confiança mais forte do que afirmar que o incidente nunca aconteceu. A tag `v1.7.2-safe` existe no histórico público para que essa afirmação possa ser verificada de forma independente.

**Para clientes:** a mesma disciplina que governa este repositório governa como a ferramenta trata os dados durante um scan — achados apenas de metadados, sem exfiltração, Audit Trail por sessão, limites de amostragem configuráveis. Veja [COMPLIANCE_FRAMEWORKS.pt_BR.md](COMPLIANCE_FRAMEWORKS.pt_BR.md) e [USAGE.pt_BR.md](USAGE.pt_BR.md).

---

## Documentação relacionada

- **Índice da documentação** (todos os tópicos, ambos os idiomas): [README.md](README.md) · [README.pt_BR.md](README.pt_BR.md).
- **SECURITY.md** ([pt-BR](../SECURITY.pt_BR.md)) — Política de segurança, cabeçalhos, chave de API opcional, reporte de vulnerabilidades.
- **docs/deploy/DEPLOY.md** ([pt-BR](deploy/DEPLOY.pt_BR.md)) — Implantação e endurecimento (Docker, Kubernetes, proxy reverso).
- **docs/USAGE.md** ([pt-BR](USAGE.pt_BR.md)) — CLI, API e configuração (incluindo `api.require_api_key`).
- **Páginas de manual:** `man data_boar` ou `man lgpd_crawler` (seção 1), `man 5 data_boar` ou `man 5 lgpd_crawler` (seção 5) — incluem notas breves sobre segurança e credenciais.
