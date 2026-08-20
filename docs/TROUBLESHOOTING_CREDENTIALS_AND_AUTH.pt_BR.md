# Resolução de problemas: Credenciais e autenticação

**English:** [TROUBLESHOOTING_CREDENTIALS_AND_AUTH.md](TROUBLESHOOTING_CREDENTIALS_AND_AUTH.md)

**Ver também:** [TROUBLESHOOTING.pt_BR.md](TROUBLESHOOTING.pt_BR.md) (visão geral e dicas rápidas).

Este documento ajuda a corrigir **auth_failed** / **authentication_failed** e a evitar **credenciais conflitantes** (ex.: API key no header e no body). Aborda credenciais de banco de dados, REST/API (Basic, Bearer, API key, OAuth2) e a API key do próprio Data Boar quando habilitada.

---

## 1. O que o relatório mostra

**Reason:** `auth_failed` ou `authentication_failed`. **Details:** Mensagem do servidor (ex.: "401 Unauthorized", "invalid_client"). **Suggested next step:** "Verify username/password, tokens or OAuth client credentials…". Se não bastar, use as seções abaixo.

---

## 2. Credenciais conflitantes (header vs body)

**Cenário:** Você configura uma API key (ou token Bearer) em **dois lugares**: ex. no `headers` do alvo e também no body ou em outro bloco de auth. Alguns servidores rejeitam quando a mesma credencial aparece duas vezes ou quando header e body discordam.

**O que evitar:** Não envie a mesma API key no header e no body, a menos que a API permita. Não defina Basic e Bearer para o mesmo alvo, salvo se a API esperar ambos. Para a API **do Data Boar** (quando `api.require_api_key: true`): envie a chave só em `X-API-Key` ou `Authorization: Bearer <key>`, não em ambos com valores diferentes.

**Passos:** Escolha **um** método de auth por alvo (só `headers` com a chave ou o campo `auth`/`bearer`/`api_key` do alvo). Remova o duplicado e reexecute. Se a API exige a chave em um header específico, use só esse header no config.

---

## 3. Banco de dados (SQL, NoSQL) auth failed

Verifique usuário/senha no config (`user`, `pass` ou `password`); conta bloqueada ou expirada; acesso por host (IP do host/container permitido no servidor); SSL/TLS (se o servidor exige SSL, ative no driver/connection string). Teste as credenciais com um cliente (psql, mysql) no mesmo host/container; desbloqueie a conta ou crie um usuário somente leitura para o scanner.

---

## 4. REST/API (Basic, Bearer, API key, OAuth2)

**Basic/Bearer/API key:** Use apenas um (Basic com user/pass, ou Bearer, ou header de API key). Evite enviar a mesma chave no header e no body. **OAuth2 (ex. Power BI, Dataverse):** Verifique tenant_id, client_id, client_secret e permissões do app no IdP; não envie o mesmo token no fluxo OAuth e em um header customizado.

---

## 5. API key do Data Boar (quando habilitada)

Com `api.require_api_key: true`, envie a chave em **um** de: `X-API-Key: <key>` ou `Authorization: Bearer <key>`. Não envie ambos com valores diferentes. `GET /health` continua público.

---

## 6. Bloqueios de conta e restrições de IP

Muitas falhas de login podem bloquear a conta; aguarde o desbloqueio ou peça ao admin. O IdP ou a API podem permitir só certos IPs; garanta que o IP do host/container esteja permitido.

---

## 7. `pass_from_env` / `api_key_from_env` não resolve

**Cenário:** O config aponta para uma variável de ambiente (`pass_from_env: "VAR_NAME"`, ou `password_from_env`, `user_from_env`, `api_key_from_env`, `token_from_env`, `client_secret_from_env`, `auth.token_from_env`, `auth.client_secret_from_env`) mas essa variável está **ausente, vazia ou com nome errado** no processo que inicia o Data Boar.

**O que o app realmente faz:** não é só um 401 opaco.

- No carregamento do config, variável ausente ou em branco emite **UserWarning**: `Environment variable 'VAR_NAME' is unset or empty; <chave> falls back to inline or default values when present.` (issue #508).
- `--validate-config` emite **WARN** para nomes `*_from_env` não definidos — veja [USAGE.pt_BR.md](USAGE.pt_BR.md).
- Sem fallback inline (`pass` / `api_key` ou equivalente), o conector pode seguir com segredo vazio e falhar depois como **auth_failed** ou connection refused. A coluna **Details** do Scan failures costuma mostrar o erro do **servidor**, não “variável de ambiente ausente”.

**Checklist:**

1. Confirme que a variável está definida **no mesmo ambiente do processo**: `echo "$VAR_NAME"` (bash) ou `$env:VAR_NAME` (PowerShell). No Linux o nome é **sensível a maiúsculas**.
1. Docker / Podman: passe `--env VAR_NAME=value` ou `--env-file` (Compose `environment:` / `env_file:`). Variável só no shell do laptop **não** entra no container.
1. systemd: `Environment=VAR_NAME=value` ou `EnvironmentFile=` na unidade do **serviço**.
1. Rode `--validate-config` e procure WARN com o nome da variável.

**Correção:** Exporte a variável antes de subir, ou injete via Docker/Podman/systemd. Nunca grave segredos reais em YAML rastreado. Contrato do operador: [OPERATOR_CREDENTIALS_FROM_ENV.pt_BR.md](ops/OPERATOR_CREDENTIALS_FROM_ENV.pt_BR.md) ([EN](ops/OPERATOR_CREDENTIALS_FROM_ENV.md)). Hábitos de cofre: [OPERATOR_SECRETS_BITWARDEN.pt_BR.md](ops/OPERATOR_SECRETS_BITWARDEN.pt_BR.md) ([EN](ops/OPERATOR_SECRETS_BITWARDEN.md)).

---

**Índice da documentação:** [README.md](README.md) · [README.pt_BR.md](README.pt_BR.md). **Visão geral:** [TROUBLESHOOTING.pt_BR.md](TROUBLESHOOTING.pt_BR.md).
