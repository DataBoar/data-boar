# Chave de API via variável de ambiente — passos concretos para o operador

**English:** [API_KEY_FROM_ENV_OPERATOR_STEPS.md](API_KEY_FROM_ENV_OPERATOR_STEPS.md)

**Objetivo:** Eliminar ambiguidades sobre `api.api_key_from_env`. O valor do YAML é o **nome** da variável de ambiente; o **segredo** é fornecido apenas em runtime (shell, systemd, Docker, Kubernetes Secret, etc.), compatível com **`config/loader.py`** (config normalizado).

**Guia completo (chave de API + HTTPS, Let's Encrypt, certificados de lab, Docker):** [SECURE_DASHBOARD_AUTH_AND_HTTPS_HOWTO.pt_BR.md](SECURE_DASHBOARD_AUTH_AND_HTTPS_HOWTO.pt_BR.md).

**Atenção:** A chave sintética abaixo é **apenas** para aprendizado. Em qualquer deploy real, gere um **novo** segredo aleatório forte; nunca reutilize exemplos de documentação.

---

## 1. O que você configura vs o que nunca commita

| Item                       | Significado                                                                                                                         |
| ----                       | -------                                                                                                                             |
| **`api.api_key_from_env`** | Uma **string**: o **nome** da variável de ambiente do OS (ex.: `AUDIT_API_KEY`). Esse nome pode aparecer em YAML rastreado no git. |
| **A chave de API real**    | O **valor** dessa variável no início do processo. **Não deve ser commitado**; defina-o no ambiente ou num cofre de segredos.        |

**Precedência (importante):** Se `api.api_key` estiver definido no YAML com uma string **não vazia**, esse literal vence e **`api_key_from_env` é ignorado** ao carregar a chave. Para o fluxo somente via env, **omita** `api_key` ou deixe-o vazio e use apenas `api_key_from_env`.

---

## 2. Fragmento mínimo de `config.yaml` (apenas nomes de exemplo)

```yaml
api:
  port: 8088
  host: "127.0.0.1"
  require_api_key: true
  api_key_from_env: "AUDIT_API_KEY"
  # Não definir api_key aqui quando usar variável de ambiente (ou deixar vazio).
```

---

## 3. Segredo sintético (documentação / lab apenas)

Use **somente** para verificar o cabeamento. **Não use** essa string em produção.

- **Nome da variável de ambiente:** `AUDIT_API_KEY`
- **Valor sintético (fictício):** `SYN_EXAMPLE_k7Qm_9pL2_vN4wR8xT1`

---

## 4. Definir a variável e iniciar o app

### Linux / macOS (bash)

```bash
export AUDIT_API_KEY='SYN_EXAMPLE_k7Qm_9pL2_vN4wR8xT1'
uv run python main.py --web --config config.yaml
```

### Windows PowerShell (sessão atual)

```powershell
$env:AUDIT_API_KEY = "SYN_EXAMPLE_k7Qm_9pL2_vN4wR8xT1"
uv run python main.py --web --config config.yaml
```

### Windows PowerShell (env persistente do usuário — opcional)

```powershell
[System.Environment]::SetEnvironmentVariable("AUDIT_API_KEY", "SYN_EXAMPLE_k7Qm_9pL2_vN4wR8xT1", "User")
```

Reinicie o terminal (ou faça logoff/logon) para que novos processos vejam a variável.

### systemd (serviço Linux)

Na unidade de serviço, em `[Service]`:

```ini
Environment="AUDIT_API_KEY=SYN_EXAMPLE_k7Qm_9pL2_vN4wR8xT1"
```

Prefira **`EnvironmentFile=-/etc/data-boar/secrets.env`** com permissão `0600` e **sem** commit desse arquivo.

---

## 5. Verificar se a API aceita sua chave

### Health (sem chave — deve funcionar):

```bash
curl -sS http://127.0.0.1:8088/health
```

Esperado: HTTP **200** e JSON com `"status":"ok"` (ou equivalente).

### Rota protegida sem chave (deve falhar):

```bash
curl -sS -o /dev/null -w "%{http_code}\n" http://127.0.0.1:8088/status
```

Esperado: **401** quando `require_api_key` é verdadeiro e a chave é exigida.

### Mesma requisição com chave:

```bash
curl -sS -H "X-API-Key: SYN_EXAMPLE_k7Qm_9pL2_vN4wR8xT1" http://127.0.0.1:8088/status
```

Esperado: **200** (ou outro sucesso), não 401.

---

## 5b. Homologação antes da produção (ordem recomendada)

1. **Inventariar** os consumidores da API (scripts, cron, CI, probes, dashboards internos). Se a lista estiver vazia, execute os checks assim mesmo para que o primeiro usuário em produção não encontre surpresas de 401/503.
2. **Homologação:** defina `api.require_api_key: true`, `api.api_key_from_env: "AUDIT_API_KEY"` (ou seu nome), exporte a variável e use **HTTPS** (`--https-cert-file` / `--https-key-file` ou TLS no proxy reverso) onde aplicável. Confirme **`GET /health`** sem chave (200) vs **`GET /status`** sem chave (**401**).
3. **Clientes:** adicione **`X-API-Key`** ou **`Authorization: Bearer`** a todas as requisições que não sejam de health; fixe a **confiança TLS** (CA empresarial, `mkcert` somente em lab, etc.).
4. **Produção:** lance com uma **curta** janela de compatibilidade apenas se necessário (ex.: `--allow-insecure-http` em texto claro ou HTTP atrás de proxy TLS-terminador). **Encerre-a** usando **`GET /status` / `GET /health`** (`dashboard_transport`) e **`python main.py --export-audit-trail`** para que a postura insegura fique rastreável.
5. Narrativa completa: **[SECURE_BY_DEFAULT_BLOCKERS_AND_MIGRATION.md](SECURE_BY_DEFAULT_BLOCKERS_AND_MIGRATION.md)**.

---

## 6. Docker / Compose (padrão)

Defina o **mesmo** nome de variável que o config referencia; valor do env do host ou de `secrets` do Compose:

```yaml
environment:
  - AUDIT_API_KEY=${AUDIT_API_KEY}
```

**Não** fixe segredos reais em `docker-compose.yml` no git.

---

## 7. Kubernetes (padrão)

Use um **Secret** e injete como env:

- Referencie o nome da variável **`AUDIT_API_KEY`** na spec do Pod.
- Monte ou gere o Secret fora deste repo; veja **`deploy/kubernetes/README.md`** § Security.

---

## 8. Solução de problemas

| Sintoma                                                          | Verificação                                                                                                                                                                                |
| -------                                                          | -----                                                                                                                                                                                      |
| **401** em todas as rotas exceto `/health`                       | O **nome** da variável no YAML bate exatamente; a variável está definida **antes** do início do processo; sem erro de digitação em `export` / systemd / env do contêiner.                 |
| **503** em rotas (exceto `/health`) com `require_api_key: true`  | Nenhuma chave resolvida: variável ausente, nome errado ou valor vazio; ou `api.api_key` deixado em branco sem `api_key_from_env`. O `main.py --web` deve **sair com código 2** antes do listen nesse caso. |
| Chave parece ser ignorada                                        | `api.api_key` não vazio no YAML sobrepõe o env — remova o literal ou deixe-o vazio.                                                                                                       |
| Funciona no shell, falha como serviço                            | A unidade de serviço não herda o env de login — defina **`Environment`** ou **`EnvironmentFile`**.                                                                                         |

---

## Relacionado

- **`SECURITY.md`** (raiz do repo) — § Chave de API opcional (enterprise)
- **`docs/USAGE.md`** — Configuração / Autenticação
- **`config/loader.py`** — Resolução de `api_key_from_env`
- **`tests/test_api_key.py`** — Comportamento quando `require_api_key` é verdadeiro
