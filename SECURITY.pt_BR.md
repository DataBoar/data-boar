# Política de segurança

**English:** [SECURITY.md](SECURITY.md)

Este documento descreve quais versões da aplicação são suportadas, qual linha de base de dependências é esperada e como reportar vulnerabilidades de segurança aos mantenedores. Sobre direitos autorais e licença: [NOTICE](NOTICE); para tornar direitos autorais e marca oficial: [docs/COPYRIGHT_AND_TRADEMARK.pt_BR.md](docs/COPYRIGHT_AND_TRADEMARK.pt_BR.md) (português) · [docs/COPYRIGHT_AND_TRADEMARK.md](docs/COPYRIGHT_AND_TRADEMARK.md) (inglês).

## Versões suportadas

- **Aplicação (marca):** **Data Boar**. Id da distribuição PyPI: **`data-boar`** (veja [CONTRIBUTING.pt_BR.md](CONTRIBUTING.pt_BR.md#repositório-e-identidade-de-instalação-data-boar)). O desenvolvimento atual tem como alvo **Python 3.12+**.
- Objetivamos suportar as últimas versões estáveis minor do Python 3.12 e 3.13 em Linux, macOS e Windows.
- Versões antigas do Python (< 3.12) não são testadas e devem ser consideradas não suportadas.

## Dependências e ambiente

O **`pyproject.toml`** é a fonte de verdade para a toolColleague-Nn **uv**. O arquivo **`uv.lock`** fixa a árvore exata de dependências resolvidas para que as instalações sejam reproduzíveis e os usuários fiquem protegidos de quebras acidentais quando uma dependência atualiza (“funcionou ontem”). **pip** e **`requirements.txt`** são derivados (o requirements.txt é exportado do lockfile para ambientes pip ou legados). As dependências são declaradas em **`pyproject.toml`** e gerenciadas via **uv**:

- Para instalar em um ambiente limpo (usa o **uv.lock** para versões reproduzíveis):

  ```bash
  uv sync
  ```

- Para exportar um **requirements.txt** bloqueado para ambientes que usam **pip** puro (mesmas versões do **uv.lock**):

  ```bash
  uv export --no-emit-package pyproject.toml -o requirements.txt
  ```

### Lockfile e mitigação da cadeia de suprimentos (`uv.lock`)

Fazer commit do **`uv.lock`** é um **controle de cadeia de suprimentos**: ele fixa a **árvore completa resolvida** (dependências diretas e transitivas) para que `uv sync` e o CI instalem **as mesmas versões de pacotes** com base nos hashes registados no lockfile. Isso **reduz** deriva não revisada por resolução flutuante de `>=` no PyPI, quebras do tipo “funcionou na minha máquina” e divergência entre **`uv.lock`** e o export **`requirements.txt`** para pip.

O lockfile **não prova**, por si só, que esses pins estão **livres de CVEs conhecidos** ou que são **benignos**. A **mitigação de vulnerabilidade** no caminho de instalação Python se **empilha** sobre o lockfile: **`pip-audit`** no CI, **GitHub Dependabot** (este repositório usa **`package-ecosystem: uv`** para PRs alinharem `pyproject.toml` e **`uv.lock`** — veja [ADR 0044](docs/adr/ADR-0044-dependabot-uv-ecosystem-for-pyproject-lock-closure.md)), revisão humana e artefatos **SBOM** ([abaixo](#lista-de-materiais-de-software-sbom)). Ao triar advisories ou aplicar atualizações, regenere **`uv.lock`** pelo fechamento de um único passo (**`pyproject.toml` → `uv lock` → `uv export`**) em [ADR 0030](docs/adr/ADR-0030-python-dependency-update-closure-single-pass.md) — **não** edite o lockfile à mão para “consertar” auditorias.

### Pré-requisitos de runtime (exemplo Linux)

No Ubuntu/Debian você deve ter pelo menos:

```bash
sudo apt update
sudo apt install -y \
  python3.12 python3.12-venv python3.12-dev build-essential \
  libpq-dev libssl-dev libffi-dev unixodbc-dev
```

Bibliotecas cliente adicionais podem ser necessárias dependendo de quais conectores você usa (ex.: Oracle, SQL Server, Snowflake); veja o `README.md` principal para notas específicas por conector.

## Lista de materiais de software (SBOM)

SBOMs formais em **CycloneDX JSON** apoiam **visibilidade da cadeia de suprimentos** e **resposta a incidentes** (veja [docs/adr/0003](docs/adr/ADR-0003-sbom-roadmap-cyclonedx-then-syft.md)). Complementam o **`pip-audit`**; **não** são gestão de risco organizacional ISO 31000 (veja [COMPLIANCE_FRAMEWORKS.pt_BR.md](docs/COMPLIANCE_FRAMEWORKS.pt_BR.md)).

| Artefato | Conteúdo | Como é gerado |
| -------- | -------- | ------------- |
| **`sbom-python.cdx.json`** | Dependências Python alinhadas ao **`uv.lock`** (via `uv export` + **`cyclonedx-py`**) | Workflow **`SBOM`**, local **`scripts/generate-sbom.ps1`** |
| **`sbom-docker-image.cdx.json`** | Pacotes na imagem OCI **construída** (camadas OS + Python) | **`syft`** em **`anchore/syft:v1.28.0`** sobre a imagem `data_boar:sbom` gerada pelo **`Dockerfile`** no mesmo commit |

**Onde baixar:** o workflow do GitHub Actions [**SBOM**](.github/workflows/sbom.yml) faz upload dos dois arquivos como **artefatos da execução** (em tags de versão `v*`, em **`release: published`**, em **`workflow_dispatch`** e em PRs filtrados por caminho para `main`). Quando já existe um **GitHub Release** para a tag, os mesmos arquivos são **anexados a essa release**.

**Docker Hub:** seguindo [docs/ops/DOCKER_IMAGE_RELEASE_ORDER.md](docs/ops/DOCKER_IMAGE_RELEASE_ORDER.md), a imagem publicada **`fabioleitao/data_boar:<semver>`** deve corresponder à mesma árvore de código da tag usada no workflow de SBOM; o SBOM da **imagem** vem de um **build local** na CI (camadas equivalentes a um `docker build` limpo nesse commit), não de um pull separado no registry.

## Manter as dependências atualizadas

- As dependências em **`pyproject.toml`** usam versões mínimas (`>=`) para permitir correções de segurança. O **lockfile (`uv.lock`)** é commitado para que todos (e o CI) instalem a mesma árvore; ele é atualizado quando as dependências mudam ou antes de uma release estável, mantendo o app atualizado, compatível e seguro. O **Dependabot** (veja `.github/dependabot.yml`) abre PRs semanais para pip e GitHub Actions e ajuda a sinalizar quando agir: ao aplicar uma atualização (ou antes de uma release), atualize primeiro o **`pyproject.toml`**, execute `uv lock` e `uv export --no-emit-package pyproject.toml -o requirements.txt`, e faça commit de **pyproject.toml**, **uv.lock** e **requirements.txt**. Não faça merge de alteração que edite só `requirements.txt` ou `uv.lock` sem atualizar o outro. Faça merge dos PRs de dependência somente após o CI (testes e auditoria) passar.

### Fechamento de atualização de dependências (um passe, qualquer origem)

O **gatilho** da mudança (CI, Dependabot, Docker Scout, revisão externa, decisão do mantenedor ou outro sinal) **não muda** o **fluxo**. Quando você concluir que uma atualização é **justificada e segura** após testes e auditoria:

1. Declare a intenção no **`pyproject.toml`**, depois **`uv lock`** e **`uv export --no-emit-package pyproject.toml -o requirements.txt`** — faça commit dos três juntos.
2. Rode **`uv sync`** localmente para o **`.venv`** bater com o lockfile.
3. Rode **`.\scripts\check-all.ps1`** (gate completo) antes do merge — sem PR de dependência “meio verde”.
4. Atualize artefatos de **SBOM** quando o release ou o trilho de compliance exigir lista de materiais no **mesmo commit** — veja [ADR 0003](docs/adr/ADR-0003-sbom-roadmap-cyclonedx-then-syft.md) e **`scripts/generate-sbom.ps1`** / workflow **`SBOM`**.
5. Acrescente ou atualize um **ADR** quando o bump refletir **política ou arquitetura** (limites de extras opcionais, toolColleague-Nns, restrição upstream documentada), não para cada patch de rotina.

Isto **não** é licença para churn cego de dependências; adie ou rejeite mudanças sem fundamento ou que falhem nos gates. Decisão registrada: [ADR 0030](docs/adr/ADR-0030-python-dependency-update-closure-single-pass.md).

- Localmente, instale e execute uma auditoria de dependências (o CI faz o mesmo em todo push/PR):

  ```bash
  uv sync
  uv pip install pip-audit
  uv run pip-audit
  ```

- Sempre que alterar dependências (incluindo ao aplicar Dependabot ou automação), edite primeiro o **`pyproject.toml`**, depois execute `uv lock` e `uv export --no-emit-package pyproject.toml -o requirements.txt` para que **uv.lock** e **requirements.txt** permaneçam em sincronia com o lockfile.

- **Triagem local (Dependabot + CVEs de imagem):** No Windows, na raiz do repositório, execute **`.\scripts\maintenance-check.ps1`** após `gh auth login` (lista PRs abertos do Dependabot) e com Docker Desktop se quiser **`docker scout quickview`** na imagem publicada. O script não altera o repositório. Depois de corrigir deps ou o **Dockerfile**, reconstrua e publique a imagem e rode o Scout de novo no novo digest. O **Dockerfile** atualiza **pip** e **wheel** no builder e no runtime para evitar ferramentas antigas em camadas copiadas; o **`requirements.txt`** é exportado pelo uv e em geral não lista `wheel` como dependência da aplicação.
- **Alertas Dependabot pyOpenSSL (#9 / #10) e Snowflake:** Não é possível subir para **pyOpenSSL ≥ 26** enquanto o **`snowflake-connector-python`** declarar limite **`<26`** (extra opcional **`bigdata`**). Veja **[docs/ops/DEPENDABOT_PYOPENSSL_SNOWFLAKE.md](docs/ops/DEPENDABOT_PYOPENSSL_SNOWFLAKE.md)** para triagem, link upstream e orientação de dispensa opcional.
- **Pygments Dependabot / pip-audit (CVE-2026-4539):** Ainda **não há release corrigido no PyPI** além do **2.19.2**. Veja **[docs/ops/DEPENDABOT_PYGMENTS_CVE.md](docs/ops/DEPENDABOT_PYGMENTS_CVE.md)** para triagem e dispensa opcional; suba o piso de **`pygments`** quando o upstream publicar o patch.
- **Linha de base de code scanning:** O workflow de CodeQL usa **`security-and-quality`** para Python e deve permanecer ativo em push/PR/agendado. Mantenha essa cobertura ampla junto com regras/testes de hardening do projeto; se uma query nova gerar ruído, triar e documentar antes de considerar supressão.
- **Semgrep (OSS):** O workflow **Semgrep** no GitHub Actions roda o conjunto **`p/python`** em push/PR (complementa o CodeQL). Exclusões e justificativa: **`docs/plans/completed/PLAN_SEMGREP_CI.md`**.
- **Bandit:** O job **Bandit (strict)** corre dentro do workflow **CI** em push/PR (`[tool.bandit]` no **`pyproject.toml`**). Detalhes e triagem de achados **low**: **`docs/plans/completed/PLAN_BANDIT_SECURITY_LINTER.md`**.
- **Cadeia de suprimentos da CI:** Os workflows em **`.github/workflows/`** fixam Actions de terceiros em **SHA de commit completo** (tag de versão em comentários YAML para humanos). O passo **`astral-sh/setup-uv`** fixa um **semver específico** do CLI **uv** — não **`latest`** — para as instalações não variarem silenciosamente entre execuções. O **Dependabot** pode propor bumps de SHA; revisar notas de release antes do merge. Isso **reduz** risco de tag móvel e de atualizações inesperadas da action, mas **não garante** proteção contra zero-day no commit fixo, ataques à cadeia que passem na revisão ou riscos fora da CI (por exemplo ferramentas no ambiente local do desenvolvedor). Veja **`docs/adr/ADR-0005-ci-github-actions-supply-Colleague-Nn-pins.md`**.

Essa abordagem faz parte da linha de base de segurança do projeto. Para a lista completa de medidas de endurecimento e status, veja **`docs/plans/completed/PLAN_SECURITY_HARDENING.md`**.

## Resistência a vulnerabilidades comuns

- **Injeção SQL:** Nomes de tabelas e colunas usados em SQL dinâmico (conectores) vêm do inspetor do banco (discover), não de entrada do usuário. Identificadores são escapados por dialeto: aspas duplas para SQLite/Postgres/Oracle (`"` → `""`), backtick para MySQL (`` ` `` → ` `` `). O banco de auditoria local (SQLite) usa apenas ORM do SQLAlchemy e consultas parametrizadas; `session_id` e outros valores fornecidos pelo usuário nunca são concatenados em SQL bruto. Veja **`tests/test_security.py`** para testes de regressão.
- **Path traversal:** O `session_id` nos caminhos da API é validado com um padrão estrito (alfanumérico e sublinhado, 12–64 caracteres) antes do uso em caminhos de arquivo ou buscas; valores inválidos retornam HTTP 400. Veja **`api/routes.py`** `_validate_session_id` e **`tests/test_security.py`**.
- **Validação de entrada (tenant/técnico):** Os valores de tenant e técnico (corpo de início de varredura, PATCH de sessão, varredura via config) são validados quanto ao tamanho e caracteres permitidos (imprimíveis, sem caracteres de controle), depois sanitizados antes do armazenamento, para que relatórios e o dashboard nunca exibam entrada não sanitizada. Veja **`core/validation.py`** `sanitize_tenant_technician` e **`tests/test_security.py`**.
- **Injeção de credenciais em URLs de conexão:** Usuário e senha são codificados para URL ao montar as URLs de conexão com bancos (conector SQL, conector MongoDB), de modo que caracteres especiais (`@`, `:`, `/`, `#`) em credenciais não quebrem o parsing da URL nem sejam interpretados como host/caminho. Veja **`connectors/sql_connector.py`** `_quote_userinfo` / `_build_url`, **`connectors/mongodb_connector.py`** `connect()`, e **`tests/test_security.py`** (ex.: `test_sql_connector_build_url_encodes_password_special_chars`, `test_mongodb_connector_uri_encodes_password_special_chars`).
- **Config e serialização:** O config YAML é carregado com `yaml.safe_load` (sem deserialização de objetos Python arbitrários). Veja **`tests/test_security.py`** para um teste que rejeita tags YAML inseguras.
- **Exposição do endpoint de config:** Quando `api.require_api_key` é true, GET `/config` retorna 401 sem uma chave de API válida, de modo que o config bruto (que pode conter segredos) não fique exposto. **GET `/config` sempre redige valores secretos** (senhas, API key, tokens, client_secret, etc.) antes de enviar o YAML ao navegador, de modo que a UI nunca exiba nem transmita segredos em claro; ao salvar, placeholders são mesclados ao arquivo atual para que segredos reais não sejam sobrescritos. Veja **`config/redact_config.py`** e **`tests/test_security.py`**.
- **Arquivo de config e segredos:** Restrinja as permissões do arquivo (ex.: `chmod 600` em `config.yaml`) para que só usuários confiáveis leiam. **Não commite** `config.yaml` nem arquivos com credenciais; use **`config.example.yaml`** ou **`deploy/config.example.yaml`** como modelo e mantenha o config local no **`.gitignore`** (o projeto ignora `config.yaml`, `config.local.yaml` e `*.vault`). Se o `config.yaml` da raiz já foi commitado, use **`git rm --cached config.yaml`** para o Git parar de rastreá-lo (o arquivo permanece no disco); commits antigos podem ainda conter o blob—reescreva o histórico ou **rotacione** segredos expostos se o repositório foi público. Prefira variáveis de ambiente (`pass_from_env`, `api_key_from_env`). Um **gerenciador de senhas** (ex. **Bitwarden**) é um bom **lugar** para o **operador** guardar cópias das credenciais; veja **`docs/ops/OPERATOR_SECRETS_BITWARDEN.pt_BR.md`**. **Homelab** (hostnames, IPs RFC1918, inventário): **`docs/private/homelab/`** (gitignored) — **`docs/PRIVATE_OPERATOR_NOTES.pt_BR.md`**. Veja também **`docs/USAGE.pt_BR.md`** (Configuração), **`CONTRIBUTING.pt_BR.md`** (higiene do repositório) e **`docs/plans/PLAN_SECRETS_VAULT.md`** (fase A).
- **Notificações ao operador (webhooks):** O bloco opcional `notifications` pode enviar resumos para Slack, Teams, URL genérico (ex.: ponte Signal) ou campos Telegram em configurações legadas/de terceiros. A política do mantenedor no repositório canónico é **não** usar Telegram para o Data Boar — veja **`docs/ops/OPERATOR_NOTIFICATION_CHANNELS.pt_BR.md`**. Trate URLs de webhook e tokens de bot como segredos; use `${VAR_DE_AMBIENTE}` no YAML ou só variáveis de ambiente. Veja **`docs/USAGE.pt_BR.md`** (Notificações ao operador). O envio repete em falhas transitórias (HTTP 5xx / rede); isso **não** substitui TLS nem política de rede.
- **Bind da API vs chave de API:** Ao subir com **`--web`**, se o endereço de bind resolvido **não** for loopback (ex.: `0.0.0.0`) e não houver chave de API **efetiva**, o processo imprime um **aviso em stderr** (veja **`main.py`** e **`core/host_resolution.py`**). Em produção, prefira loopback + proxy reverso ou `api.require_api_key` com chave forte.
- **Limite de tamanho do corpo da requisição:** A API rejeita requisições cujo **Content-Length** exceda **1 MB** (ex.: POST `/config`, POST `/scan`, POST `/scan_database`) com **HTTP 413 Payload Too Large** para reduzir DoS por corpos JSON ou form grandes. Veja **`api/routes.py`** `request_body_size_middleware` e **`tests/test_security.py`**.
- **Política de logging:** Chave de API, senhas e strings de conexão não devem aparecer em logs de auditoria ou da aplicação. Detalhes de falha e mensagens de exceção usam **`core.validation.sanitize_log_text`** (segredos mais formas de PII alinhadas ao detector, como CPF, e-mail, cartão) e **`core.validation.clean_error`** para exceções antes do SQLite ou de handlers de log; URLs de conexão e valores no estilo `password=` / `api_key=` são mascarados. Veja **`core/database.py`** (`save_failure`) e **`tests/test_security.py`**.
- **Acesso a relatório e heatmap:** Os endpoints de relatório e heatmap validam o formato do `session_id` antes do uso; IDs inválidos retornam 400, sessões desconhecidas ou inexistentes retornam 404 (sem enumeração de sessões nem distinção 403/404 para IDs desconhecidos). Veja **`api/routes.py`** e **`docs/SECURITY.md`**.

Para um **resumo orientado ao técnico** (o que observar, testes de regressão, recomendações), veja **`docs/SECURITY.md`** (EN) e **`docs/SECURITY.pt_BR.md`** (pt-BR). Para etapas de endurecimento concluídas e planejadas, veja **`docs/plans/completed/PLAN_SECURITY_HARDENING.md`**.

## Cabeçalhos HTTP de segurança (web e API)

A aplicação adiciona os seguintes cabeçalhos a todas as respostas web e da API por padrão:

- **X-Content-Type-Options: nosniff** — evita detecção de tipo MIME.
- **X-Frame-Options: DENY** — evita que o app seja incorporado em frames (mitigação de clickjacking).
- **Content-Security-Policy** — restringe origens de script, estilo e recursos ao app e ao CDN do Chart.js; permite scripts/estilos inline exigidos pelo dashboard atual.
- **Referrer-Policy: strict-origin-when-cross-origin** — limita informações de referrer enviadas em requisições cross-origin.
- **Permissions-Policy** — desabilita recursos do navegador não usados pelo app (câmera, microfone, geolocalização, etc.).
- **Strict-Transport-Security (HSTS)** — definido apenas quando a requisição é considerada HTTPS (direta ou via `X-Forwarded-Proto: https` de um proxy confiável), para que implantações somente HTTP não fiquem bloqueadas. Quando presente, usa `max-age=31536000; includeSubDomains; preload`.

Quando o app estiver atrás de um proxy reverso (ex.: nginx, Caddy, load balancer), garanta que o proxy defina **X-Forwarded-Proto: https** para requisições com TLS terminado para que o HSTS seja aplicado corretamente. Não habilite HSTS na camada do app para HTTP puro; o proxy pode adicionar HSTS ao servir via HTTPS.

## Chave de API opcional (empresarial)

A API não implementa autenticação por padrão; proteja o app no proxy reverso ou no nível de rede quando exposto. Para empresas que desejam um gate de segredo compartilhado simples sem alterar o modelo “proteger no proxy”, a aplicação suporta uma **chave de API opcional**:

- No config, defina `api.require_api_key: true` e `api.api_key` (literal — evite commit de segredo) ou `api.api_key_from_env: "VAR"` (lê a chave do ambiente na subida do processo). Quando habilitado, **GET /health** permanece **sem autenticação** de propósito: devolve JSON de liveness (`status`, resumo **público** de `license`, `dashboard_transport`) para probes. **Todas as outras rotas** precisam de **X-API-Key** ou **Authorization: Bearer** quando a chave foi resolvida a partir do config/ambiente. **401** = chave ausente ou inválida. **503** = `require_api_key` true porém nenhuma chave resolvida (misconfig). O **`main.py --web` encerra com código 2** antes de escutar se a chave é obrigatória e está ausente, evitando API aberta por engano.
- **Boa prática:** Use uma chave forte e aleatória e armazene-a em uma variável de ambiente (ex.: `api_key_from_env: "AUDIT_API_KEY"`). Não registre em log nem faça commit da chave no controle de versão. Isso é apenas um gate simples; para autenticação e autorização completas, use o proxy reverso ou um provedor de identidade.
- **Passos concretos (EN, para evitar ambiguidade):** nome da variável no YAML vs segredo no SO, precedência, exemplos `curl` — [API_KEY_FROM_ENV_OPERATOR_STEPS.md](docs/ops/API_KEY_FROM_ENV_OPERATOR_STEPS.md). Ordem sugerida (inventário, staging, monitorar `dashboard_transport` / audit export): [SECURE_BY_DEFAULT_BLOCKERS_AND_MIGRATION.pt_BR.md](docs/ops/SECURE_BY_DEFAULT_BLOCKERS_AND_MIGRATION.pt_BR.md).
- **Guia ponta a ponta para técnico (chave de API + caminhos TLS, Let’s Encrypt, autoassinado em lab, Docker):** [SECURE_DASHBOARD_AUTH_AND_HTTPS_HOWTO.pt_BR.md](docs/ops/SECURE_DASHBOARD_AUTH_AND_HTTPS_HOWTO.pt_BR.md) ([EN](docs/ops/SECURE_DASHBOARD_AUTH_AND_HTTPS_HOWTO.md)).

## Endurecimento de implantação e proxy reverso

Os cabeçalhos de segurança (incluindo CSP) são implementados em **`api/routes.py`** (middleware aplicado às respostas web e da API). Para endurecer implantações em container e cluster:

- **Docker e Kubernetes:** Veja **`docs/deploy/DEPLOY.md`** ([pt-BR](docs/deploy/DEPLOY.pt_BR.md)), seção **“Security and hardening (optional)”**, para:
- Executar como não-root, limites de recursos e healthchecks.
- Exemplos opcionais Kubernetes: **securityContext** (runAsNonRoot, readOnlyRootFilesystem, drop capabilities), **NetworkPolicy** (`deploy/kubernetes/network-policy.example.yaml`) e **PodDisruptionBudget** (`deploy/kubernetes/pdb.example.yaml`).

Quando a API ou o dashboard for **exposto à internet ou a redes não confiáveis**, execute-o atrás de um **proxy reverso** com **TLS**, **autenticação/autorização** adequadas e considere um **WAF** (web application firewall). A chave de API e o rate limiting do app (veja [docs/USAGE.md](docs/USAGE.md) ([pt-BR](docs/USAGE.pt_BR.md))) complementam, mas não substituem, a segurança no nível do proxy.

## Reportar uma vulnerabilidade

Se você acredita ter encontrado uma vulnerabilidade de segurança neste projeto:

1. **Não abra uma issue pública com detalhes de exploração.**
1. Em vez disso:
   - Abra uma nova issue na aba **Issues** com uma descrição curta e em alto nível (sem dados sensíveis de PoC), **ou**
   - Se os security advisories do GitHub ou o reporte privado estiver disponível para este repositório, prefira esse canal.
1. Inclua pelo menos:
   - Versão/commit do projeto que você está usando.
   - Versão do Python e detalhes do SO.
   - Uma descrição mínima do impacto (ex.: divulgação de informação, escalação de privilégio, DoS).
1. Os mantenedores irão:
   - Confirmar o recebimento o mais rápido possível.
   - Investigar e, se confirmado, trabalhar em uma correção e coordenar a divulgação.

Se não tiver certeza se algo é sensível do ponto de vista de segurança, prefira o canal privado (ou uma issue pública mínima) para que possamos triar com segurança.

## Resposta de segurança (SLAs opcionais)

Estes são **metas** para mantenedores e reportadores, não obrigações contratuais. Ajuste conforme a capacidade da equipe.

| Área                               | Meta opcional                                                                                                                                                                                                                                                                |
| ------                             | ----------------                                                                                                                                                                                                                                                             |
| **Reportes de vulnerabilidade**    | Objetivamos **confirmar recebimento** em até **5 dias úteis** e, para achados **altos/críticos**, **corrigir ou documentar** (ex.: advisory, mitigação ou “não corrigir” com justificativa) em até **30 dias**.                                                              |
| **PRs de segurança do Dependabot** | Tratamos os PRs **de segurança** do Dependabot como **P0**: objetivamos **fazer merge ou responder** (ex.: merge, fechar com comentário ou adiar com justificativa) em até **5 dias úteis**. PRs de dependência que não sejam de segurança seguem o ciclo normal de revisão. |

Veja **CONTRIBUTING** para como aplicar atualizações de dependências e executar `pip-audit`; veja **`.github/dependabot.yml`** para a configuração do Dependabot.

## Matriz rápida de triagem CodeQL (P0/P1/P2)

Use esta matriz para priorizar alertas do CodeQL por impacto e risco de release. Mapeie cada alerta para a família de regra e superfície de código mais próxima, então decida correção imediata vs agendamento.

| Prioridade                              | Rule IDs (exemplos)                                                                                                                                                                                                              | Superfície típica neste repositório                                                                                                                                   | Ação                                                                                            |
| ---                                     | ---                                                                                                                                                                                                                              | ---                                                                                                                                                                   | ---                                                                                             |
| **P0** (corrigir antes da release)      | `py/path-injection`, `py/sql-injection`, `py/nosql-injection`, `py/code-injection`, `py/command-line-injection`, `py/template-injection`, `py/full-ssrf`, `py/unsafe-deserialization`, `py/xxe`                                  | Servir arquivos e caminhos de relatório na API (`api/routes.py`), conectores/construção de query (`connectors/*`, `database/*`), caminhos de config/load (`config/*`) | Corrigir imediatamente, adicionar teste de regressão e validar com nova execução do CodeQL.     |
| **P1** (corrigir no ciclo atual)        | `py/weak-sensitive-data-hashing`, `py/clear-text-logging-sensitive-data`, `py/clear-text-storage-sensitive-data`, `py/insecure-protocol`, `py/insecure-default-protocol`, `py/url-redirection`, `py/regex-injection`, `py/redos` | Helpers de licensing/integridade (`core/licensing/*`), logging/persistência de falhas (`core/database.py`, `core/validation.py`), conectores de rede (`connectors/*`) | Corrigir ou documentar mitigação neste ciclo de release; adicionar testes quando viável.        |
| **P2** (hardening agendado / monitorar) | `py/bind-socket-all-network-interfaces`, `py/flask-debug`, `py/client-exposed-cookie`, `py/insecure-cookie`, `py/samesite-none-cookie`, `py/stack-trace-exposure`, `py/use-of-input`                                             | Configuração de host/runtime (`core/host_resolution.py`, defaults de Docker), middleware/templates web (`api/routes.py`, `api/templates/*`)                           | Manter habilitado, monitorar tendência e agrupar correções de baixo risco em PRs de manutenção. |

Notas:

- **Não desabilitar suites amplas por padrão.** Mantenha `security-and-quality` e priorize correções pontuais + testes.
- Se um alerta precisar ser adiado, registrar justificativa + controle compensatório no PR/issue e revisitar no próximo loop `-1/-1b`.
