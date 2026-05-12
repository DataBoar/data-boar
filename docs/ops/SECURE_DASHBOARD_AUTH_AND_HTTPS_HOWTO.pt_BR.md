# Dashboard seguro: autenticação na API e HTTPS (guia para técnico)

**English:** [SECURE_DASHBOARD_AUTH_AND_HTTPS_HOWTO.md](SECURE_DASHBOARD_AUTH_AND_HTTPS_HOWTO.md)

**Público:** Técnicos que vão ligar **proteção por chave de API** e **TLS** no dashboard web do Data Boar (`main.py --web`). Este guia **complementa** (não substitui) [USAGE.md](../USAGE.md) ([EN](../USAGE.md)), [SECURITY.md](../../SECURITY.md) ([EN](../../SECURITY.md)) na raiz e [deploy/DEPLOY.md](../deploy/DEPLOY.md) ([EN](../deploy/DEPLOY.md)).

**Runbooks relacionados:** [API_KEY_FROM_ENV_OPERATOR_STEPS.md](API_KEY_FROM_ENV_OPERATOR_STEPS.md) (detalhe de variável de ambiente; **somente EN**), [SECURE_BY_DEFAULT_BLOCKERS_AND_MIGRATION.pt_BR.md](SECURE_BY_DEFAULT_BLOCKERS_AND_MIGRATION.pt_BR.md) (ordem de rollout), [PLAN_DASHBOARD_HTTPS_BY_DEFAULT_AND_HTTP_EXPLICIT_RISK.md](../plans/PLAN_DASHBOARD_HTTPS_BY_DEFAULT_AND_HTTP_EXPLICIT_RISK.md) (racional e anti-padrões).

**WebAuthn JSON opcional (fase 1a):** Com **`api.webauthn.enabled: true`** e o segredo de token no ambiente (padrão **`DATA_BOAR_WEBAUTHN_TOKEN_SECRET`**) antes da subida, a API expõe **`/auth/webauthn/*`** para registro e autenticação **FIDO2 / passkey** ([ADR 0033](../adr/ADR-0033-webauthn-open-relying-party-json-endpoints.md)). **`api.require_api_key`** **não** se aplica a esses caminhos. O **HTML do painel** **ainda não** exige login por isso; sessão no browser e RBAC ficam no **[#86](https://github.com/FabioLeitao/data-boar/issues/86)**. Subconjunto pytest: [SMOKE_WEBAUTHN_JSON.pt_BR.md](SMOKE_WEBAUTHN_JSON.pt_BR.md).

---

## Parte A — Exigir autenticação na API (chave compartilhada)

### A.0 O que a aplicação faz (comportamento que você precisa espelhar)

1. Com **`api.require_api_key: true`**, o processo precisa de um segredo **resolvido**: ou **`api.api_key`** não vazio no config, ou **`api.api_key_from_env: "VAR"`** com **`VAR` definida no ambiente antes da subida**.
1. **`main.py --web`** **encerra com código 2** se `require_api_key` estiver true e **nenhuma chave** puder ser resolvida (evita dashboard aberto por engano).
1. **`GET /health`** **nunca** exige autenticação (probes e load balancers continuam simples). Devolve JSON com `status`, resumo público de `license` e `dashboard_transport`.
1. **Todas as outras rotas** (páginas HTML, `GET /status`, `POST /scan`, `GET /config`, OpenAPI `/docs`, …) exigem chave válida quando a exigência está ativa: envie **`X-API-Key: <segredo>`** ou **`Authorization: Bearer <segredo>`**.
1. **401** = chave ausente ou incorreta. **503** = `require_api_key` true mas a chave não foi resolvida em runtime (misconfig); corrija YAML/ambiente e reinicie.

**YAML rastreado:** coloque **só** o **nome** da variável de ambiente no config (ex.: `api_key_from_env: "AUDIT_API_KEY"`). **Nunca** faça commit do segredo real. Precedência: **`api.api_key`** literal não vazio no YAML **sobrepõe** o caminho por env — para fluxo só por ambiente, omita `api_key` ou deixe vazio.

### A.1 Gerar um segredo forte (uma vez)

Use gerenciador de senhas ou CSPRNG. Exemplo (64 caracteres hex):

```bash
openssl rand -hex 32
```

Guarde o valor no cofre / vault / gerenciador; injete no ambiente no deploy (veja [API_KEY_FROM_ENV_OPERATOR_STEPS.md](API_KEY_FROM_ENV_OPERATOR_STEPS.md)).

### A.2 Trecho de config (seguro para commit)

```yaml
api:
  port: 8088
  host: "127.0.0.1"   # ou seu bind; precedência em USAGE vs CLI / API_HOST
  require_api_key: true
  api_key_from_env: "AUDIT_API_KEY"
  # Não defina api_key aqui quando usar ambiente (ou deixe vazio).
```

### A.3 Definir variável de ambiente e subir

## Linux / macOS:

```bash
export AUDIT_API_KEY='cole-o-segredo-gerado-aqui'
uv run python main.py --web --config /caminho/para/config.yaml
```

## Windows PowerShell (sessão):

```powershell
$env:AUDIT_API_KEY = "cole-o-segredo-gerado-aqui"
uv run python main.py --web --config C:\caminho\para\config.yaml
```

Em produção use **systemd**, **Secret do Kubernetes → env**, **Docker `environment:`**, etc. (padrões em [API_KEY_FROM_ENV_OPERATOR_STEPS.md](API_KEY_FROM_ENV_OPERATOR_STEPS.md)).

### A.4 Verificar no shell

```bash
# Tem que funcionar sem chave (200)
curl -sS http://127.0.0.1:8088/health

# Tem que falhar sem chave com require_api_key true (401)
curl -sS -o /dev/null -w "%{http_code}\n" http://127.0.0.1:8088/status

# Tem que funcionar com header (200)
curl -sS -H "X-API-Key: cole-o-segredo-gerado-aqui" http://127.0.0.1:8088/status
```

Com listener **HTTPS**, use `https://` e a porta; em **laboratório** com cert autoassinado pode ser preciso `-k` (não vire hábito em produção).

### A.5 Clientes (navegador, scripts, CI)

- **Navegador:** Com a chave ligada, o dashboard costuma ser exposto atrás de **proxy reverso** com TLS e, se necessário, camada extra de auth. A UI não pede chave em todo request; o padrão **produção** costuma ser **auth no proxy** + chave no app, ou **bind em loopback** + proxy.
- **Scripts:** O helper [poll_dashboard_scan.py](../../scripts/poll_dashboard_scan.py) aceita **`DATA_BOAR_API_KEY`** / **`--api-key`** com `require_api_key` ativo.
- **curl / automação:** Envie **`X-API-Key`** ou **`Authorization: Bearer`** em todo request exceto **`GET /health`**.

---

## Parte B — HTTPS no dashboard

### B.0 Postura padrão (o que `main.py --web` exige)

É obrigatório **um** dos caminhos:

1. **TLS direto no app:** **`--https-cert-file`** e **`--https-key-file`** (PEM), ou os mesmos caminhos em **`api.https_cert_file`** / **`api.https_key_file`** no config, **ou**
1. **Aceitar HTTP texto plano de forma explícita:** **`--allow-insecure-http`** ou **`api.allow_insecure_http: true`** (aviso em stderr + faixa no dashboard; só em redes controladas).

Caso contrário **`main.py --web` encerra com código 2**. A imagem **Docker** padrão inclui **`--allow-insecure-http`** no `CMD` para subir sem certificados montados; **sobreponha o `CMD`** e monte PEMs quando quiser TLS no container.

### B.1 Padrão recomendado em produção: TLS no proxy reverso

Para Internet ou LAN com vários clientes, prefira:

1. Bind do app em **loopback** (`127.0.0.1` ou interface só do container).
1. **TLS** em **nginx**, **Traefik**, **Caddy** ou load balancer gerenciado.
1. **`X-Forwarded-Proto: https`** a partir do proxy para cabeçalhos de segurança (ex.: HSTS) funcionarem certo.

Veja [deploy/DEPLOY.md](../deploy/DEPLOY.pt_BR.md) e **SECURITY.md** na raiz.

### B.2 HTTPS nativo no Data Boar (PEM no host)

**1.** Obtenha **`fullColleague-Nn.pem`** (ou certificado + cadeia) e **`privkey.pem`**. Restrinja permissões da chave (ex.: `chmod 600` no Linux).

**2.** Suba:

```bash
uv run python main.py --web --config config.yaml \
  --https-cert-file /etc/data-boar/certs/fullColleague-Nn.pem \
  --https-key-file /etc/data-boar/certs/privkey.pem
```

Ou no YAML:

```yaml
api:
  https_cert_file: "/etc/data-boar/certs/fullColleague-Nn.pem"
  https_key_file: "/etc/data-boar/certs/privkey.pem"
```

**3.** Abra **`https://<host>:<port>/`**. Use **`GET /status`** ou **`GET /health`** e confira **`dashboard_transport`** no JSON (`mode`, `tls_active`, `summary`).

**4.** Evidência opcional: **`python main.py --export-audit-trail -`** (sem `--web`) inclui **`dashboard_transport`** no JSON exportado.

### B.3 Let’s Encrypt (host público ou DNS validável)

**Quando faz sentido:** nome na Internet pública (HTTP-01) ou DNS que você automatiza (DNS-01). **Somente lab interno** sem DNS público costuma precisar de **PKI interna**, **autoassinado só em lab** ou **`mkcert`** na máquina de desenvolvimento — não emissão por CA pública.

## Fluxo típico (Linux, Certbot, HTTP-01):

1. Aponte DNS **A/AAAA** de `dashboard.exemplo.com` para o servidor (ou use plugin DNS).
1. Rode o Certbot (standalone ou webroot); anote caminhos (muitas vezes `/etc/letsencrypt/live/<nome>/fullColleague-Nn.pem` e `privkey.pem`).
1. Aponte **`--https-cert-file`** / **`--https-key-file`** do Data Boar para esses PEMs **ou** configure o **proxy** para usá-los e deixe o app em HTTP em loopback (renovação costuma ser mais simples no proxy).
1. **Renovação:** timer com **certbot renew**; se o app lê PEM direto, reinicie ou recarregue após renovação (ou use proxy que recarrega certificado.

**Nota:** Let’s Encrypt é opção **válida em produção** quando automação e validação de hostname batem com o seu ambiente; CA empresarial ou PKI interna também são válidas conforme política.

### B.4 Certificado autoassinado (alternativa — só lab / QA / UAT)

**Não** é a recomendação padrão para confiança de usuário em produção. O navegador alerta salvo instalação de âncora de confiança (anti-padrões em [PLAN_DASHBOARD_HTTPS_BY_DEFAULT_AND_HTTP_EXPLICIT_RISK.md](../plans/PLAN_DASHBOARD_HTTPS_BY_DEFAULT_AND_HTTP_EXPLICIT_RISK.md)).

## Exemplo rápido com openssl (foco em localhost, 365 dias):

```bash
openssl req -x509 -newkey rsa:2048 -sha256 -days 365 -nodes \
  -keyout server-key.pem -out server-cert.pem \
  -subj "/CN=localhost"
```

Use **`server-cert.pem`** como **`--https-cert-file`** e **`server-key.pem`** como **`--https-key-file`**. Em **QA/UAT** com nome corporativo, prefira **PKI interna** ou certificados com **validação DNS** para a cadeia ser confiável sem instalar raiz ad hoc.

**Desenvolvimento local:** ferramentas como **`mkcert`** instalam uma **CA local só na máquina do dev** — útil para testar TLS sem ruído de browser; **não** use isso como distribuição de confiança em produção.

### B.5 Docker: TLS sem `CMD` em texto plano

Monte os PEMs como somente leitura e sobrescreva o comando para rodar **`main.py --web`** **sem** **`--allow-insecure-http`**, passando **`--https-cert-file`** / **`--https-key-file`** (ou config equivalente).

Padrões em [deploy/DEPLOY.md](../deploy/DEPLOY.pt_BR.md) e [deploy/kubernetes/README.md](../../deploy/kubernetes/README.md).

### B.6 Verificar e monitorar

| Verificação             | O que observar                                                                                                                                                         |
| -----------             | --------------                                                                                                                                                         |
| **Runtime**             | `GET /status` e `GET /health` → campo **`dashboard_transport`** com **`https`** vs **http** com opt-in explícito.                                                      |
| **Export de auditoria** | `python main.py --export-audit-trail -` → JSON com **`dashboard_transport`** (export roda sem `--web`; valores refletem ambiente/processo salvo workflow documentado). |
| **Auth**                | Com **`require_api_key`**, **`/health`** sem chave; **`/status`** com chave.                                                                                           |

---

## Ordem de rollout (staging → produção)

Siga [SECURE_BY_DEFAULT_BLOCKERS_AND_MIGRATION.pt_BR.md](SECURE_BY_DEFAULT_BLOCKERS_AND_MIGRATION.pt_BR.md): inventário de clientes da API, **staging** com **chave + TLS** (ou TLS no proxy), atualizar chamadas com headers e confiança no certificado, depois produção com janela curta de compatibilidade se precisar (`--allow-insecure-http` / HTTP atrás de proxy que termina TLS), e por fim reduzir modos inseguros usando **`dashboard_transport`** e logs.

---

## Documentação relacionada

| Tema                                       | Português (pt-BR)                                    | English                                                                  |
| ----                                       | -----------------                                    | -------                                                                  |
| Uso (CLI, API)                             | [USAGE.pt_BR.md](../USAGE.pt_BR.md)                  | [USAGE.md](../USAGE.md)                                                  |
| Política de segurança + semântica da chave | [SECURITY.pt_BR.md](../../SECURITY.pt_BR.md)         | [SECURITY.md](../../SECURITY.md)                                         |
| Resumo técnico (testes)                    | [SECURITY.pt_BR.md](../SECURITY.pt_BR.md) (em docs/) | [SECURITY.md](../SECURITY.md)                                            |
| Deploy / proxy                             | [DEPLOY.pt_BR.md](../deploy/DEPLOY.pt_BR.md)         | [DEPLOY.md](../deploy/DEPLOY.md)                                         |
| Chave via env (detalhado)                  | — (use o EN)                                         | [API_KEY_FROM_ENV_OPERATOR_STEPS.md](API_KEY_FROM_ENV_OPERATOR_STEPS.md) |
