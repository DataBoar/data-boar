# Data Boar: motor de descoberta de dados e governança de risco corporativa — pt-BR

Esta página é o **guia de uso do operador**: **CLI**, **API web e dashboard**, **configuração** (alvos, amostragem, detecção, credenciais) e **entregáveis** (Excel, heatmap, Markdown executivo, manifesto de evidência — sessões atuais e anteriores). Complementa o [guia técnico](TECH_GUIDE.pt_BR.md) e o [README raiz](../README.pt_BR.md). Identidade de instalação e PyPI **`data-boar`**: [CONTRIBUTING.pt_BR.md](../CONTRIBUTING.pt_BR.md#repositório-e-identidade-de-instalação-data-boar).

**Data Boar** faz **descoberta e mapeamento com consciência de conformidade** de dados pessoais e sensíveis em bases, arquivos, APIs e compartilhamentos (**LGPD**, **GDPR**, **CCPA**, **GLBA** e *frameworks* configuráveis — não é só LGPD). Os entregáveis são **adjacentes a GRC** (narrativa executiva, prioridades estilo APG, manifestos de evidência): apoiam **avaliação de risco** e **descoberta para conformidade**; **não** substituem assessoria jurídica nem uma plataforma GRC corporativa completa. O repositório ainda contém o pacote Python histórico **`lgpd_crawler`** (imports) — detalhe de implementação, não o nome do produto.

**Data warehouse e SQL corporativo:** o mesmo motor cobre alvos **SQLAlchemy** (**Microsoft SQL Server**, **PostgreSQL**, **MySQL/MariaDB**, **Oracle**, …) e **Snowflake** opcional (instale com ``uv sync --extra bigdata`` — ver [Snowflake (optional, .[bigdata])](USAGE.md#snowflake-optional-bigdata) no guia em inglês). A amostragem usa **timeouts por motor** e *hints* documentados (por exemplo **`/*+ MAX_EXECUTION_TIME(N) */`** no MySQL e **`SET LOCAL statement_timeout`** no PostgreSQL — ver **amostragem SRE** nas opções globais e bullets em [USAGE.md](USAGE.md)). Se a política do **DBA** usar leituras **read-uncommitted** (por exemplo *hints* **`NOLOCK`** no SQL do conector), registre isso em **runbooks** e no **`scan_manifest_*.yaml`** / texto de evidência para que *stakeholders* vejam a **postura atribuída**, não semântica de isolamento omitida.

O documento descreve, em português, como:

- Executar a aplicação via **CLI** e **API web**;
- Entender os parâmetros (`--demo`, `--config`, `--web`, `--port`, `--host`, `--https-cert-file`, `--https-key-file`, `--allow-insecure-http`, `--validate-config`, `--tenant`, `--technician`, `--scan-compressed`, `--content-type-check`, `--scan-stego`, `--jurisdiction-hint`);
- Navegar pelo **dashboard web**;
- Iniciar varreduras e baixar relatórios/heatmaps usando **curl**.

**English:** [USAGE.md](USAGE.md)

> **Importante:** sempre que `docs/USAGE.md` for atualizado, mantenha este arquivo sincronizado (mesmas rotas, parâmetros e exemplos, traduzidos).

---

## 1. Interface de linha de comando (CLI)

O ponto de entrada é `main.py`.

### Argumentos

<!-- markdownlint-disable MD060 -->
| Argumento               | Padrão               | Descrição                                                                                                                                                                                                                                                                                |
| ---                     | ---                  | ---                                                                                                                                                                                                                                                                                      |
| `--demo`                | *(flag)*             | **Demonstração zero-config:** cria workspace temporário em `/tmp/data_boar_demo/` (ou diretório temp do SO) com `demo.config.yaml`, corpus sintético de filesystem, relatórios e SQLite; executa varredura inicial e sobe o dashboard em loopback. **Ignora o `config.yaml` do diretório atual.** Implica `--web` e `--allow-insecure-http`. Arquivos temporários são removidos ao sair. Incompatível com `--validate-config`, `--reset-data`, `--export-audit-trail`, `--export-dsar` e `--diff`. |
| `--config`              | `config.yaml`        | Caminho do arquivo de configuração (YAML ou JSON). Usado em varredura única e para resolver `api.port` / `api.host` ao subir a API.                                                                                                                                                      |
| `--web`                 | *(flag)*             | Inicia o servidor FastAPI em vez de executar uma varredura única.                                                                                                                                                                                                                        |
| `--port`                | `8088`               | Porta da API quando `--web` é usado. Pode ser sobrescrita por `api.port` no config, salvo se você passar `--port` explicitamente. Ignorado em modo varredura única.                                                                                                                      |
| `--host`                | *(resolvido)*        | Endereço de bind quando `--web` (ex.: `127.0.0.1`, `0.0.0.0`). **Prevalece** sobre `api.host` e `API_HOST`. Se omitido: `api.host` → `API_HOST` → padrão seguro **`127.0.0.1`**. Ver §2.                                                                                                 |
| `--https-cert-file`     | *(vazio)*            | Caminho PEM do certificado para TLS com `--web`; exige `--https-key-file` (ou `api.https_cert_file` / `api.https_key_file`). TLS **≥ 1.2**. Sem os dois arquivos, a inicialização **falha** salvo `--allow-insecure-http`.                                                               |
| `--https-key-file`      | *(vazio)*            | Caminho PEM da chave privada para TLS com `--web`; pareado com `--https-cert-file` ou as chaves `api.*` correspondentes.                                                                                                                                                                 |
| `--allow-insecure-http` | *(flag)*             | **Aceite explícito de risco:** servir o dashboard em **HTTP em texto plano** (risco de interceptação/alteração). Em produção, prefira TLS ou proxy reverso. Equivale a `api.allow_insecure_http: true`. A imagem **Docker** padrão passa essa flag para rodar sem certificados montados. |
| `--validate-config`     | *(flag)*             | Pré-voo: analisa o config, reconhece conectores e chaves obrigatórias por target; **WARN** em `*_from_env` ausentes (não é erro). Sem rede nem DB. Sai **0** com `[OK]` ou **1** com `[INVALID]`. Incompatível com `--web`, `--reset-data` e `--export-audit-trail`. |
| `--diff`                | `SESSION_A SESSION_B` | Compara achados entre dois UUIDs de sessão no SQLite; imprime novos, resolvidos e mudanças de severidade. Sai **0**, salvo `--fail-on-new-high` com novo **HIGH** (sai **1**). Sessão inexistente → sai **2**. Incompatível com `--web`, `--reset-data`, `--export-audit-trail` e `--validate-config`. |
| `--fail-on-new-high`    | *(flag)*             | Com `--diff`: sai **1** se `SESSION_B` tiver achado **HIGH** novo em relação a `SESSION_A` (gate de regressão em CI). |
| `--export-dsar`         | `SESSION_ID`         | Exporta achados de uma sessão em JSON orientado a DSAR (metadados primeiro; enquadramento LGPD Art. 18 / GDPR Art. 15). Imprime em **stdout** ou use `--dsar-output PATH`. Sessão inexistente ou vazia → `findings_by_source` vazio, sai **0**. Incompatível com `--web`, `--reset-data`, `--export-audit-trail`, `--validate-config` e `--diff`. |
| `--dsar-output`         | `PATH`               | Grava o JSON DSAR em `PATH` em vez de stdout. Exige `--export-dsar`. |
| `--dsar-include-samples`| *(flag)*             | Com `--export-dsar`: inclui campos de amostra bruta nas linhas de achado quando existirem (SQLite guarda só metadados por padrão). |
| `--reset-data`          | *(flag)*             | Operação de manutenção perigosa: apaga todas as sessões/achados/falhas do SQLite, remove relatórios/heatmaps em `report.output_dir` e registra o wipe na tabela `data_wipe_log`. Não inicia varredura.                                                                                   |
| `--export-audit-trail`  | *(caminho opcional)* | Exporta Rastro de Auditoria (Audit Trail) em JSON a partir do SQLite (`data_wipe_log`, resumo de sessões, `dashboard_transport`, **`maturity_assessment_integrity`** quando houver linhas do POC de maturity — mesmos totais que **`GET /status`**). Sem caminho ou com `-` → **stdout**; caso contrário grava no arquivo. **Não** altera o banco. Incompatível com `--web` e `--reset-data`.                             |
| `--tenant`              | *(vazio)*            | Nome do cliente/tenant na execução CLI; gravado na sessão e exibido em dashboard/relatórios.                                                                                                                                                                                             |
| `--technician`          | *(vazio)*            | Nome do técnico/operador na execução CLI; também gravado na sessão e relatórios.                                                                                                                                                                                                         |
| `--scan-compressed`     | *(flag)*             | Sobrescrita pontual: ativa varredura dentro de arquivos compactados como se `file_scan.scan_compressed` estivesse true.                                                                                                                                                                  |
| `--content-type-check`  | *(flag)*             | Sobrescrita pontual: inferência por magic bytes como se `file_scan.use_content_type` estivesse true (extensão vs formato real — disfarce simples).                                                                                                                                                       |
| `--scan-stego`          | *(flag)*             | Sobrescrita pontual: dicas de esteganografia (heurística de entropia de bytes) como se `file_scan.scan_for_stego` estivesse true — não prova dado oculto; pode aumentar leitura em imagens/áudio/vídeo.                                                                                                    |
| `--jurisdiction-hint`   | *(flag)*             | Opt-in nesta execução: notas heurísticas de jurisdição na planilha **Report info** (ex.: EUA-CA CCPA/CPRA, Colorado, Japão APPI) quando metadados sugerem relevância. Não é conclusão jurídica. Equivale a `report.jurisdiction_hints.enabled: true` neste processo e grava o opt-in na sessão. |
<!-- markdownlint-enable MD060 -->

### Evidência opcional de adulteração na camada de licenciamento (`licensing.mode: enforced`)

Implantações corporativas podem exigir *hooks* de **tamper-evidence** paralelos ao enforcement:

- **`DATA_BOAR_EXPECTED_BUILD_DIGEST`** — compara com a linha embutida em **`core/licensing/_build_digest.txt`** (gerada no build via **`scripts/generate_build_digest.py`** — ver **`docs/RELEASE_INTEGRITY.pt_BR.md`**). Divergência ⇒ **TAMPERED** e bloqueio de varreduras com enforcement ligado.
- **`DATA_BOAR_RELEASE_MANIFEST_PATH`** ou **`licensing.manifest_path`** — JSON opcional de SHA-256 de arquivos críticos verificado na subida (**mesmo documento**).

**Roadmap:** *anchor* SQLite, re-hash na inicialização e degradação de confiança além da camada de licenciamento continuam **planejadas** (**`docs/plans/PLAN_BUILD_IDENTITY_RELEASE_INTEGRITY.md`** — export **E.11** via **`--export-audit-trail`** ✅; *anchors* ⬜).

### Resultados

#### Demonstração zero-config (`--demo`)

```bash
data-boar --demo
# ou a partir do clone:
uv run python main.py --demo
```

- **Não** é varredura pontual orientada ao seu config: `--demo` **não** lê o `config.yaml` do diretório atual.
- Prepara `/tmp/data_boar_demo/` (temp do SO + `data_boar_demo/`) com `demo.config.yaml`, corpus sintético, `reports/` e `audit_results.db`, executa varredura inicial e mantém o dashboard em **`127.0.0.1`** com HTTP em texto plano.
- **Saída:** banner no console com caminho do workspace e URL do dashboard (porta padrão **8088**). A árvore temporária é removida ao encerrar o processo.
- Veja também [QUICKSTART.md](../QUICKSTART.md) (*Caminho 0*) e `man 1 data-boar` (`--demo`).

#### Varredura única (sem `--web`)

```bash
# Execução mínima
python main.py --config config.yaml

# Execução com tags de tenant e técnico
python main.py --config config.yaml --tenant "Acme Corp" --technician "Alice V."
```

- Carrega a configuração, varre todos os alvos (`targets`) e grava achados em `audit_results.db`.
- Cria uma nova sessão (UUID + timestamp) com metadados (`tenant_name`, `technician_name` opcionais).
- Gera um relatório Excel e um heatmap PNG para essa sessão.
- O relatório também inclui a aba **Data source inventory** com metadados best-effort das fontes (alvo, tipo, produto/versão, dica de versão de API/protocolo, dica de transporte e detalhes brutos).
- Imprime linhas `INFO` de confiança do runtime (stdout + stderr); em estado inesperado, alerta explícito: **THERE IS SOMETHING DIFFERENT AND UNEXPECTED IN THIS RUNTIME**.
- No console, você verá algo como:
- `Scan session: <session_id>`
- `Report written: <caminho_do_relatorio>`

#### Servidor API (`--web`)

**Transporte:** é preciso usar **HTTPS** (certificado + chave PEM na CLI ou em `api` no config) ou **aceitar explicitamente** texto plano com **`--allow-insecure-http`** (ou `api.allow_insecure_http: true`). Caso contrário, `main.py --web` termina com código **2**. **`GET /status`** e **`GET /health`** incluem `dashboard_transport` e **`enterprise_surface`** (transporte + confiança da licença + postura global da chave de API; **RBAC** opcional por rota aparece em **`enterprise_surface.access_surface.rbac`** — **`enabled`** quando `api.rbac` está ligado e o tier permite **`dashboard_rbac`**, senão **`not_implemented`**); em HTTP texto plano há **faixa de aviso** nas páginas do dashboard.

```bash
python main.py --config config.yaml --web --https-cert-file server.crt --https-key-file server.key --port 8088
python main.py --config config.yaml --web --allow-insecure-http --port 8088
# Escutar em todas as interfaces (sobrescreve config / API_HOST; use só com controles de rede):
python main.py --config config.yaml --web --allow-insecure-http --host 0.0.0.0 --port 8088
```

- Inicia o FastAPI em **`<bind>:<port>`**. O bind padrão é **`127.0.0.1`**, salvo `api.host`, `API_HOST` ou **`--host`** (a CLI ganha). A imagem Docker oficial define `API_HOST=0.0.0.0` e inclui **`--allow-insecure-http`** no `CMD` para subir sem certificados montados; para HTTPS, monte cert/chave e ajuste o `CMD`.
- Nenhuma varredura é executada automaticamente; você controla tudo via HTTP (dashboard ou curl).
- Configuração para a API:
- Se `--config` não for usado, a API lê de `CONFIG_PATH` ou `config.yaml` no diretório atual.

### Arquivo de configuração (primeira execução)

**Prefira YAML** (`.yaml` / `.yml`) em projetos novos: dá para comentar, revisar diff e mesclar com segurança. **`--config`** usa por padrão **`config.yaml`** no diretório de trabalho atual; esse nome está no **`.gitignore`** na raiz do repositório para não versionar caminhos de LAN ou segredos — use uma **cópia** de uma amostra versionada num caminho privado ou defina **`CONFIG_PATH`**.

| O que copiar | Quando usar |
| ------------ | ----------- |
| **[`deploy/samples/config.starter-lgpd-eval.yaml`](../deploy/samples/config.starter-lgpd-eval.yaml)** | **Recomendado** para primeiro laboratório ou avaliação: duas pastas fictícias de sistema de arquivos, um alvo estilo PostgreSQL com `pass_from_env`, `scan.max_workers`, timeouts, **`rate_limit`**, termos ML/DL mínimos e blocos opcionais **comentados** (arquivos compactados, `file_passwords`, `learned_patterns`, arquivos de padrões, `detection.cnpj_alphanumeric`, `connector_format_id_hint`, chave de API, dicas de jurisdição). Substitua caminhos e defina variáveis de ambiente — os valores usam **IPs de documentação RFC 5737** e caminhos placeholder apenas. |
| **[`deploy/config.example.yaml`](../deploy/config.example.yaml)** | Arquivo **mínimo** válido para Docker (`targets: []`, caminhos `/data`). |
| **JSON legado** em [`config/config.json`](../config/README.md) | O carregador ainda aceita o formato antigo **`databases`** + **`file_scan.directories`**; **trabalhos novos devem usar YAML** — veja [`config/README.md`](../config/README.md). |

**Índice (mesmos links a partir de `docs/`):** [samples/README.pt_BR.md](samples/README.pt_BR.md) ([EN](samples/README.md)). **Montar alvos a partir de planilha:** [deploy/scope_import.example.csv](../deploy/scope_import.example.csv) e [ops/SCOPE_IMPORT_QUICKSTART.pt_BR.md](ops/SCOPE_IMPORT_QUICKSTART.pt_BR.md) ([EN](ops/SCOPE_IMPORT_QUICKSTART.md)) — texto para jurídico, DPO e gestores que **não** são equipe de infra em tempo integral.

---

## 2. API web e dashboard

### Implantar o servidor

### Implantação automatizada com Ansible (dois caminhos)

Para implantações reproduzíveis com um único comando em servidores Debian/Ubuntu, o Data Boar inclui playbooks Ansible em `deploy/ansible/`. Há dois caminhos:

**Caminho A — Simples (Docker Compose, Docker já instalado):**

```bash
# 1. Instale o Ansible na máquina de controle
sudo apt install ansible
ansible-galaxy collection install community.docker

# 2. Clone o repositório
git clone https://github.com/DataBoar/data-boar.git
cd data-boar/deploy/ansible

# 3. Configure o inventário
cp inventory/hosts.ini.example inventory/hosts.ini
# Edite hosts.ini: IP do servidor e usuário SSH

# 4. Simulação (--check) e depois aplicação
ansible-playbook site.yml --check
ansible-playbook site.yml
```

**Caminho B — Pilha completa (Docker CE + Swarm + ctop + serviço Data Boar, servidor novo):**

```bash
# Passos 1–3 iguais ao Caminho A, depois:
ansible-playbook site-full.yml --check
ansible-playbook site-full.yml
```

Isso instala o Docker CE a partir do repositório oficial, inicializa um Swarm de nó único, instala `ctop` para monitoramento de containers e implanta o Data Boar como serviço Swarm.

Após qualquer caminho, o Data Boar fica acessível em `http://<servidor>:8088`.
Veja `deploy/ansible/README.md` para variáveis, Swarm multi-nó e solução de problemas.

## Opção: executar via Docker (sem clonar o Git)

Imagens pré-construídas estão no Docker Hub: `fabioleitao/data_boar:latest` ([hub.docker.com/r/fabioleitao/data_boar](https://hub.docker.com/r/fabioleitao/data_boar)). Faça pull e execute com um config montado em `/data/config.yaml` (veja o README “Deploy com Docker” e [docs/deploy/DEPLOY.pt_BR.md](deploy/DEPLOY.pt_BR.md) ([EN](deploy/DEPLOY.md))). Você pode usar esse container em vez de instalar a partir do código.

**Instalação `pipx` por distro (Linux):** antes de rollout em frotas RHEL/Void/musl/no-AVX, confira [TROUBLESHOOTING.pt_BR.md](TROUBLESHOOTING.pt_BR.md) e a matriz [ops/OS_COMPATIBILITY_TESTING_MATRIX.pt_BR.md](ops/OS_COMPATIBILITY_TESTING_MATRIX.pt_BR.md) (RHEL 8/9 com passo explícito de Python 3.12; Void-musl/no-AVX em caminho wheelhouse-ou-Docker; RHEL/CentOS 7 somente Docker).

### URLs principais

As páginas HTML usam **prefixo de idioma** (`/en/…`, `/pt-br/…`). Acessar `/`, `/reports`, `/config`, `/help` ou `/about` **sem** prefixo redireciona conforme cookie `db_locale`, cabeçalho `Accept-Language` e `locale.default_locale` no YAML (veja bloco `locale` em [USAGE.md](USAGE.md)). As rotas JSON da API continuam **sem** prefixo.

**Passo a passo (não técnico, primeira execução):**

1. **Abra** o painel no navegador: `http://127.0.0.1:8088/pt-br/` (ou `/en/`). O servidor precisa estar no ar antes — veja [Servidor API (`--web`)](#servidor-api---web) (texto plano exige `--allow-insecure-http`; fora do loopback use TLS).

   ![Painel — formulário de varredura](img/dashboard/pt-br/scan-start.png)

2. **(Opcional) Identifique a execução:** preencha **Cliente / tenant** e **Técnico / operador** nos campos do formulário — aparecem na planilha **Report info** do relatório.
3. **Confira os alvos (opcional):** abra **Configuração** e verifique bancos, sistemas de arquivos ou outros alvos listados — a próxima varredura usa exatamente esse arquivo.

   ![Configuração — alvos em YAML](img/dashboard/pt-br/config.png)

4. **Inicie a varredura:** clique em **Iniciar varredura**. A página acompanha o status enquanto a auditoria roda (`POST /scan` por baixo).
5. **Abra Relatórios:** ao terminar, vá para a página **Relatórios** (`/pt-br/reports` ou `/en/reports`).
6. **Baixe:** clique em **Baixar** na linha da sessão para obter o relatório Excel (e o mapa de calor). Sem shell nem chamada de API.

   ![Relatórios — botão Baixar por sessão](img/dashboard/pt-br/reports-download.png)

### Baixar relatórios pelo painel web

Para **DPO, jurídico e outros perfis não técnicos** (veja [AUDIENCE_GUIDE.pt_BR.md](AUDIENCE_GUIDE.pt_BR.md)), use o navegador — a captura abaixo mostra o caminho **antes** de qualquer `curl`.

1. Abra **Relatórios** no menu superior.
2. Clique em **Baixar** na linha da sessão desejada.

![Página Relatórios — clique em Baixar](img/dashboard/pt-br/reports-download.png)

O Excel é salvo na pasta de downloads do navegador; o mapa de calor PNG é gerado junto com a planilha quando o relatório é montado.

- **Dashboard:** `http://<host>:<port>/en/` (ou `/pt-br/`)
- **Reports:** `http://<host>:<port>/en/reports`
- **Configuration:** `http://<host>:<port>/en/config`
- **Help:** `http://<host>:<port>/en/help` — início rápido, exemplos de config, detecção de sensibilidade e `recommendation_overrides`, links para README e USAGE (EN/pt-BR)
- **Entrar (WebAuthn):** `http://<host>:<port>/en/login` — registro e login por passkey no navegador quando **`api.webauthn.enabled`**; script **`webauthn-login.js`**. Com WebAuthn desligado, a página explica isso. Enquanto **não** houver passkey registrada, o dashboard HTML continua acessível sem esta página (bootstrap). Depois de **uma ou mais** passkeys, visitantes sem sessão são redirecionados para cá a partir das outras URLs do painel.
- **About:** `http://<host>:<port>/en/about` — aplicação, versão, autor e licença (conforme LICENSE)
- **Autoavaliação (POC):** `http://<host>:<port>/en/assessment` — placeholder quando **`api.maturity_self_assessment_poc_enabled`** está ligado; **404** se desligado. **Tier:** `licensing.effective_tier` no YAML para lab, ou claim **`dbtier`** no JWT com `licensing.mode: enforced` (**Pro+** para esta funcionalidade). Com enforcement ligado e JWT de licença válido, **`dbtier` prevalece sobre `effective_tier` no YAML** neste gate (mesma regra das outras funcionalidades do painel com tier). Opcional **`api.maturity_assessment_pack_path`** para YAML do questionário (`core/maturity_assessment/pack.py`); **`scores`** opcionais por resposta no YAML alimentam o **total da rubrica** no resumo pós-envio. Opcional **`DATA_BOAR_MATURITY_INTEGRITY_SECRET`** (ou **`api.maturity_integrity_secret_from_env`**) para **HMAC-SHA256 por linha** (integridade / anti-adulteração casual; **não** é criptografia). **`GET /status`** expõe **`maturity_assessment_integrity`** para demonstrar o resumo. Após **POST**, o redirect traz **`saved=1`** e **`batch=`**; o HTML mostra **resumo do envio** (linhas gravadas, pontuação da rubrica quando configurada, totais HMAC daquele batch) e, com respostas no SQLite, uma tabela de **envios recentes** por **batch** (mais recente primeiro). **Exportação:** `GET /{locale}/assessment/export?batch=<id>&format=csv` ou `format=md` devolve **anexo** (download); não há exportação automática em disco no produto — salve pelo navegador ou redirecione `curl` para arquivo. Com **`api.require_api_key`** ativo, envie **`X-API-Key`** ou **`Authorization: Bearer`** como nas outras rotas do painel. Sem texto proprietário do questionário no repositório público.
- **Swagger UI:** `http://<host>:<port>/docs` — documentação interativa da API (OpenAPI)
- **Health:** `http://<host>:<port>/health` — sonda de liveness/readiness para Docker/Kubernetes (sempre público mesmo com API key exigida)
- **Autenticação (API key opcional):** Por padrão a API não exige autenticação. Para exigir chave, use `api.require_api_key: true` e `api.api_key` **ou** `api.api_key_from_env: "VAR"` com a variável definida **antes** de subir o processo — passos em **[API_KEY_FROM_ENV_OPERATOR_STEPS.md](ops/API_KEY_FROM_ENV_OPERATOR_STEPS.md)** (EN, operador). **Passo a passo (chave + HTTPS, Let’s Encrypt, cert de lab):** **[SECURE_DASHBOARD_AUTH_AND_HTTPS_HOWTO.pt_BR.md](ops/SECURE_DASHBOARD_AUTH_AND_HTTPS_HOWTO.pt_BR.md)** ([EN](ops/SECURE_DASHBOARD_AUTH_AND_HTTPS_HOWTO.md)). Em produção, prefira **`api_key_from_env`** para não versionar segredo em YAML rastreado.
- **WebAuthn (opcional — fase 1 API JSON + fase 1b sessão HTML):** Com **`api.webauthn.enabled: true`**, defina a variável de ambiente indicada por **`api.webauthn.token_secret_from_env`** (padrão **`DATA_BOAR_WEBAUTHN_TOKEN_SECRET`**) **antes** de subir o processo; a falta do segredo faz o processo **encerrar na inicialização**. Habilita endpoints JSON **sem lock-in de vendor** (biblioteca open-source **`webauthn`** no PyPI) em **`/auth/webauthn/`** para registro e autenticação por passkey. **`api.require_api_key` não se aplica** a esses caminhos nem a **`GET /{locale}/login`** (para abrir a página de entrada com chave global ligada). Alinhe **`api.webauthn.origin`** e **`api.webauthn.rp_id`** com a URL do navegador (HTTPS recomendado). Credenciais ficam no SQLite (`webauthn_credentials`); **`--reset-data` / wipe** apaga essas linhas. **Depois que existir pelo menos uma passkey registrada**, as páginas do painel com prefixo de idioma (**`/`, `/config`, `/reports`, `/assessment`, …**) exigem cookie de sessão WebAuthn válido, exceto **`help`**, **`about`** e **`login`** (GET). Use **`/{locale}/login`** no navegador ( **`/static/webauthn-login.js`** ) para registrar ou entrar; formulários HTML mutáveis (**`POST …/config`**, **`POST …/assessment`**) **sempre** exigem token **CSRF** assinado (**#1231** — independente do gate WebAuthn; chave estável opcional via **`DATA_BOAR_HTML_CSRF_SECRET`**, senão o segredo WebAuthn quando configurado, senão segredo efêmero do processo). RBAC por rota (opcional; item seguinte) pode complementar quando habilitado. Ver **[ADR 0033](adr/ADR-0033-webauthn-open-relying-party-json-endpoints.md)** (EN).
- **RBAC (opcional — fase 2, Pro+ `dashboard_rbac`):** Com **`api.rbac.enabled: true`** e tier efetivo que permita **`dashboard_rbac`** (`licensing.effective_tier` no YAML ou claim **`dbtier`** no JWT com enforcement — mesma regra das outras funções com tier), rotas protegidas exigem **papéis**: `admin` (tudo), `dashboard`, `scanner`, `reports_reader`, `config_admin`. A **chave global de API** (quando presente e correta) recebe **`api.rbac.api_key_roles`**; sessões WebAuthn usam a coluna **`roles_json`** na linha correspondente de `webauthn_credentials` (array JSON de nomes de papel), ou **`api.rbac.default_roles`** quando **`roles_json`** estiver vazio. **401** sem principal; **403** com papéis insuficientes. **`GET /status`** e **`GET /health`** incluem **`enterprise_surface.access_surface.rbac`** (`enabled` vs `not_implemented`). Tier **Community** não habilita RBAC no produto; use proxy reverso ou rede. Veja o plano interno **`PLAN_DASHBOARD_REPORTS_ACCESS_CONTROL.md`** (na lista **Internal and reference** em `docs/README.md`; **#86**); **SSO/OIDC** enterprise continua como fase **3**.
- **`GET /health` (sempre público):** Sonda liveness/readiness; JSON com `status`, resumo **público** de `license`, `dashboard_transport` e `enterprise_surface`. **Não** é necessário (nem checado) `X-API-Key` / Bearer.
- **Demais rotas** (HTML com prefixo de idioma, `GET /status`, `POST /scan`, `GET /en/config`, OpenAPI `/docs`, etc.): com `require_api_key` e chave resolvida, envie **X-API-Key** ou **Authorization: Bearer**. **401** = chave ausente ou inválida. **503** = `require_api_key` true porém nenhuma chave resolvida (corrija config/ambiente). O **`main.py --web` encerra com código 2** nesse caso para não subir dashboard aberto por engano.
- **Rollout:** Inventário de consumidores da API (scripts, cron, CI, probes), **staging** primeiro com TLS + chave quando couber, depois produção com janela curta de compatibilidade se necessário — **[SECURE_BY_DEFAULT_BLOCKERS_AND_MIGRATION.pt_BR.md](ops/SECURE_BY_DEFAULT_BLOCKERS_AND_MIGRATION.pt_BR.md)**. Com HTTPS ou HTTP explícito, use **`GET /status` / `GET /health`** e **`--export-audit-trail`** (campos `dashboard_transport`, e **`maturity_assessment_integrity`** quando aplicável) para auditar postura.
- Veja [SECURITY.pt_BR.md](../SECURITY.pt_BR.md) (chave opcional).

### O que o dashboard mostra

- Estado da varredura (`Running`/`Idle`), ID da sessão atual, contagem de achados.
- Estatísticas da última execução (achados em bancos, filesystem, falhas, total).
- Gráfico **“Progress over time”** com total de achados e score de risco (0–100) por sessão.
- Campos de entrada para **cliente/tenant** e **técnico/operador**, usados ao clicar em “Start scan”.
- Tabela de sessões recentes com:
- ID, data de início, tenant, técnico, achados DB/FS, falhas e link “Download” (gera o Excel dessa sessão).

### Rotas de API (resumo)

| Método  | Endpoint                            | Finalidade                                                                                              |
| ---     | ---                                 | ---                                                                                                     |
| `POST`  | `/scan` ou `/start`                 | Inicia uma varredura completa em background; retorna `session_id`. Corpo JSON opcional: `tenant`, `technician`, `scan_compressed`, `content_type_check`, `scan_for_stego`, `jurisdiction_hint` (booleanos pontuais por execução). |
| `POST`  | `/scan_database`                    | Inicia varredura pontual de um único banco (body JSON). Pode incluir `tenant` e `technician`.           |
| `GET`   | `/status`                           | Retorna `running`, `current_session_id`, `findings_count`, além de `runtime_trust`, `dashboard_transport`, `enterprise_surface` e **`maturity_assessment_integrity`** (resumo HMAC das respostas do POC quando configurado). |
| `GET`   | `/report`                           | Baixa o último relatório Excel gerado (ou gera a partir da sessão mais recente).                        |
| `GET`   | `/heatmap`                          | Baixa o último heatmap PNG gerado (sessão mais recente).                                                |
| `GET`   | `/logs`                             | Baixa o arquivo de log mais recente (`audit_YYYYMMDD.log`) com registros de conexões e achados.         |
| `GET`   | `/list`                             | Lista sessões anteriores (JSON). A lista HTML fica em `/en/reports` ou `/pt-br/reports`.                |
| `GET`   | `/reports/{session_id}`             | Gera (se necessário) e baixa o relatório Excel para a sessão indicada.                                  |
| `GET`   | `/heatmap/{session_id}`             | Gera (se necessário) e baixa o heatmap PNG para a sessão indicada.                                      |
| `GET`   | `/logs/{session_id}`                | Baixa o log da sessão (`match` por conteúdo primeiro; fallback por dia UTC para `audit_YYYYMMDD.log` quando necessário), para análise detalhada da sessão. |
| `POST`  | `/auth/webauthn/registration/options` | **Opcional.** Com **`api.webauthn.enabled`**, devolve JSON de criação WebAuthn + `state` opaco (ADR 0033, EN). |
| `POST`  | `/auth/webauthn/registration/verify` | **Opcional.** Verifica registro; grava passkey no SQLite; define cookie de sessão. |
| `POST`  | `/auth/webauthn/authentication/options` | **Opcional.** Opções de autenticação + `state`. |
| `POST`  | `/auth/webauthn/authentication/verify` | **Opcional.** Verifica autenticação; atualiza cookie. |
| `GET`   | `/auth/webauthn/status`             | **Opcional.** `{ enabled, registered_credentials, session_authenticated }` quando WebAuthn está ligado. |
| `POST`  | `/auth/webauthn/logout`             | **Opcional.** Remove cookie de sessão WebAuthn. |
| `PATCH` | `/sessions/{session_id}`            | Atualiza/limpa o tenant de uma sessão existente (`{ "tenant": "..." }`).                                |
| `PATCH` | `/sessions/{session_id}/technician` | Atualiza/limpa o técnico de uma sessão existente (`{ "technician": "..." }`).                           |
| `GET`   | `/en/about` (ou outro prefixo de locale) | Página About (HTML): aplicação, versão, autor, licença.                                            |
| `GET`   | `/about/json`                       | Informações de about em JSON (nome, versão, autor, licença, copyright).                                 |
| `GET`   | `/health`                           | Sonda de liveness/readiness para Docker e Kubernetes.                                                   |

---

## 3. Exemplos de uso da API com curl

**Para automação / scripting** — use os exemplos `curl` abaixo em CI, cron ou integrações. Para DPO, jurídico e outros perfis não técnicos, prefira o [passo a passo do painel web](#passo-a-passo-não-técnico-primeira-execução) e [Baixar relatórios pelo painel web](#baixar-relatórios-pelo-painel-web) primeiro.

### Iniciar varredura completa

```bash
# Sem metadados extras
curl -X POST http://localhost:8088/scan

# Com tenant e technician
curl -X POST http://localhost:8088/scan \
  -H "Content-Type: application/json" \
  -d '{ "tenant": "Acme Corp", "technician": "Alice V." }'
```

Resposta típica:

```json
{
  "status": "started",
  "session_id": "a1b2c3d4-20250301_143022"
}
```

### Verificar status

```bash
curl http://localhost:8088/status
```

```json
{
  "running": true,
  "current_session_id": "a1b2c3d4-20250301_143022",
  "findings_count": 42
}
```

### Varredura pontual de banco de dados

```bash
curl -X POST http://localhost:8088/scan_database \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Ad-hoc Postgres",
    "host": "db.example.com",
    "port": 5432,
    "user": "audit",
    "password": "secret",
    "database": "mydb",
    "driver": "postgresql+psycopg2",
    "tenant": "Acme Corp",
    "technician": "Alice V."
  }'
```

### Listar sessões anteriores

```bash
curl http://localhost:8088/list
```

Resposta (exemplo):

```json
{
  "sessions": [
    {
      "session_id": "a1b2c3d4-20250301_143022",
      "started_at": "2025-03-01LAB-NODE-01:30:22",
      "finished_at": "2025-03-01LAB-NODE-01:35:10",
      "status": "completed",
      "tenant_name": "Acme Corp",
      "technician_name": "Alice V.",
      "database_findings": 12,
      "filesystem_findings": 30,
      "scan_failures": 0
    }
  ]
}
```

### Baixar o último relatório Excel

```bash
curl -o report.xlsx http://localhost:8088/report
```

### Baixar o último arquivo de log

```bash
curl -o audit.log http://localhost:8088/logs
```

**Formato das linhas do audit log (leia antes de interpretar caminhos):** As linhas seguem o padrão `Finding: origem | rótulo_do_target | localização | sensibilidade | padrão` e `Connected: rótulo_do_target (tipo) em localização`. O **`rótulo_do_target`** é um nome **único e higienizado** por alvo (`audit_log_name`), derivado do config — pode não ser idêntico ao `name` bruto. Em alvos **filesystem**, a **`localização`** costuma ser um **caminho POSIX relativo à raiz de varredura resolvida** (sem letra de drive nem home). A própria raiz aparece como `nome_da_pasta?8_hex` (não é caminho absoluto completo). Se um arquivo **resolve fora** da raiz (ex.: symlink), a **localização** vira `rótulo_do_target?12_hex` em vez de vazar caminho absoluto — use a linha no SQLite/Excel como evidência canônica. Conectores de compartilhamento remoto que abrem arquivos compactados via temporário mantêm no log estilo `arquivo.zip|caminho/interno.txt`.

### Baixar o último heatmap PNG

```bash
curl -o heatmap.png http://localhost:8088/heatmap
```

### Baixar relatório e heatmap de uma sessão específica

```bash
curl -o report_20250301.xlsx \
  "http://localhost:8088/reports/a1b2c3d4-20250301_143022"

curl -o heatmap_20250301.png \
  "http://localhost:8088/heatmap/a1b2c3d4-20250301_143022"
```

### Baixar o arquivo de log associado a uma sessão específica

```bash
curl -o audit_20250301.log \
  "http://localhost:8088/logs/a1b2c3d4-20250301_143022"
```

Esse endpoint procura, entre os arquivos `audit_YYYYMMDD.log` disponíveis (do mais recente para o mais antigo), o primeiro cujo conteúdo contenha o `session_id` informado e devolve esse arquivo.

### Evidência executiva, prioridades APG e o comando `data-boar-report`

Quando o **`generate_report`** roda (CLI one-shot, **`GET /reports/{session_id}`**, **`GET /report`** ou **Download** no dashboard), o produto pode gravar, **no mesmo diretório do Excel** (`report.output_dir`):

- **`POC_SUMMARY_<primeiros_16_chars_do_session_id>.md`** — Markdown com tom executivo: status, achados **agregados por sensibilidade** (só nomes de **padrão** e contagens), as **três** prioridades de mitigação da **APG Fase A** e um resumo curto de postura DBA/SRE. **Não** lista nomes de colunas, tabelas, caminhos de arquivo nem conteúdo amostrado — adequado para quem não deve ver detalhe operacional.
- **`scan_manifest_<prefixo>.yaml`** — manifesto de evidência (tetos de amostragem, timeouts, bullets de auditoria, recorte de escopo, bloco opcional `apg_phase_a`).

Se a gravação desses artefatos falhar, o fluxo **não** invalida o Excel nem o heatmap; veja os logs se o `.md` ou o `.yaml` não aparecerem.

**Ponto de entrada no console** (instalado com o pacote PyPI **`data-boar`**, ver `[project.scripts]` no repositório):

```bash
uv run data-boar-report --config config.yaml --session-id <session_id>
```

Sem **`-o` / `--output`**, o CLI grava **`executive_report_<prefixo_seguro>.md`** ao lado do YAML de configuração (evita despejar o relatório completo no stdout em logs de CI). Com **`-o`**, define o caminho explicitamente:

```bash
uv run data-boar-report --config config.yaml --session-id <session_id> -o Resumo_executivo.md
```

**Flags úteis:**

| Flag | Significado |
| --- | --- |
| `--sqlite <caminho>` | Sobrescreve `sqlite_path` do config (ex.: cópia do banco de auditoria em outro host). |
| `--trial-rows-capped` | Inclui a mesma nota sobre possível limite de linhas no Excel sob licença de avaliação, alinhada ao `POC_SUMMARY` gerado junto ao relatório. |

**Requisitos:** o mesmo **`config.yaml`** usado nas varreduras (para o manifesto refletir política de amostragem/timeouts) e um **`session_id`** que exista nas tabelas de sessão/achados.

#### Processamento local e privacidade (`data-boar-report`)

O `data-boar-report` lê **apenas** o artefato **SQLite local** da varredura (`sqlite_path`, sobrescrevível com **`--sqlite`**). Ele **reagrega** metadados da sessão em Markdown/YAML **sem abrir conectores ao vivo**. Por desenho, o Markdown executivo padrão (**`POC_SUMMARY_*.md`**) traz **nomes de padrão, contagens, prioridades APG Fase A** e narrativa de postura — **não** valores amostrados brutos nem trechos livres de PII. Literais sensíveis ficam no nível de banco protegido (ou em exportações **redigidas** que **você** controla).

**Estrutura (contrato “mesa” do PoC):** o Markdown segue hierarquia clara (**H1–H4**): status, achados por sensibilidade, **`## 3. Metodologia e segurança`** (amostragem, timeouts, comentário de rastreio, **`WITH (NOLOCK)`** no SQL Server quando esse motor aparece na sessão, mais bullets SRE/DBA do manifesto), depois **`## 4. Plano de ação (APG)`** com **Top 3** e **inventário completo por padrão** (achado → risco → recomendação técnica).

**Ver também:** [REPORTS_AND_COMPLIANCE_OUTPUTS.pt_BR.md](REPORTS_AND_COMPLIANCE_OUTPUTS.pt_BR.md) (mapa de saídas).

---

## 4. Notas sobre configuração

- A aplicação utiliza um único arquivo de configuração (YAML/JSON) com as chaves principais:
- `targets` – alvos a escanear (bancos, diretórios, APIs, compartilhamentos). Não há limite rígido de alvos por varredura; listas muito grandes (ex.: centenas de bancos ou APIs) podem aumentar tempo e uso de memória—considere um escopo razoável por varredura.
- `file_scan` – extensões, recursividade, `scan_sqlite_as_db`, `sample_limit` (estilo linhas/TOPN), `file_sample_max_chars` (orçamento de caracteres para `.txt`/`.md` em FS/shares), opcionalmente `scan_compressed` (varrer dentro de arquivos compactados, ex.: zip, tar, 7z — desligado por padrão), limites de tamanho (`max_inner_size`, faixa válida 1 MB–500 MB; padrão 10 MB) e `compressed_extensions`, e `file_passwords` (senhas para PDFs e documentos ZIP protegidos por senha; ver [USAGE.md](USAGE.md), seção Global options, para exemplo YAML e limitações). Para suporte a .7z instale o extra opcional: `pip install -e ".[compressed]"`. **Amostragem em banco (SQL via SQLAlchemy + conector Snowflake):** a leitura por coluna usa `WHERE <coluna> IS NOT NULL` antes do teto de linhas, para colunas esparsas ainda gerarem amostra útil quando existir valor não nulo. A variável de ambiente opcional **`DATA_BOAR_SQL_SAMPLE_LIMIT`** (inteiro entre **1** e **10000**) **substitui** `file_scan.sample_limit` nesses conectores quando definida — útil em produção sem editar o YAML. Opcional: bloco raiz **`sql_sampling.overrides`** com tetos por **`targets[].name`**, por tabela (`schema.tabela` ou só o nome da tabela) e padrões globais com **`fnmatch`** no nome da tabela (ex.: `*_audit`), nessa ordem, antes de cair no `file_scan.sample_limit`. É possível fatiar overrides em **arquivos** YAML à parte e referenciá-los com **`sql_sampling_file`** (um caminho) e/ou **`sql_sampling_files`** (lista; mesclagem em ordem; o YAML principal por cima ganha em chaves iguais; caminhos relativos ao config principal, sem `..` para fora da pasta). Só **`load_config`** / **`normalize_config(..., config_path=...)`** expandem esses arquivos. Ver exemplo em [USAGE.md](USAGE.md) (Global options). Código: `core/sampling.py` / `core/sampling_policy.py` e `connectors/sql_sampling.py` — `SamplingManager` escolhe um **rótulo de estratégia** por dialeto (e metadados opcionais de tabela); `SQLConnector` / Snowflake / SQLite embutido no filesystem registra esse rótulo **uma vez por tabela** em INFO. Ponto legado: `SqlColumnSampleQueryBuilder.build` gera o mesmo SQL.
- **Resiliência na amostragem SQL (alvos `type: database`):** o SQL gerado começa com o comentário de linha **`-- Data Boar Compliance Scan`** para rastreio em visões do motor. No alvo você pode definir **`sample_statement_timeout_ms`** ou **`sample_statement_timeout_seconds`** (**`0`** desliga); se omitido, o conector usa **5000 ms** por padrão. Esse orçamento aciona o hint **`/*+ MAX_EXECUTION_TIME(N) */`** no MySQL e **`SET LOCAL statement_timeout`** no PostgreSQL (transação curta por amostra). **No SQL Server não existe hint equivalente** (T-SQL não aceita `OPTION (MAX_EXECUTION_TIME = …)`); o orçamento fica registrado apenas no log de auditoria — para limitar leituras MSSQL use o **`connect_timeout`** do driver e o resource governor lado DBA. A variável de ambiente **`DATA_BOAR_SAMPLE_STATEMENT_TIMEOUT_MS`** sobrescreve o valor. Opcional: **`inter_query_delay_ms`** (pausa entre colunas). Estimativa de tamanho de tabela para modo “tabela grande” vem só de **estatísticas de dicionário** (`connectors/sql_table_row_estimate.py`), sem **`COUNT(*)`** na tabela de negócio.
- **Aviso (scan_compressed):** Habilitar `scan_compressed: true` pode **aumentar bastante** o tempo de execução, I/O em disco e uso de espaço temporário. Use só quando precisar inspecionar o interior de arquivos compactados; na primeira vez, prefira um escopo menor (ex.: um diretório ou poucos caminhos).
- **`use_content_type` (opt-in):** Quando `true`, o scanner usa um helper de **magic bytes** para que **disfarce simples** (extensão no nome diferente do formato real) não vença só pela extensão: o **nome** pode sugerir um tipo (ex.: `.txt` ou extensão que não é de texto, como `.mp3`) e os **primeiros bytes** revelam outro (ex.: `%PDF-...`). Quem só segue a extensão se engana; com o flag, filesystem e compartilhamentos aplicam o **recorte PDF** (tratar como PDF quando o cabeçalho é PDF) e o **remapeamento de mídia rica** onde existir — ver [TECH_GUIDE.pt_BR.md](TECH_GUIDE.pt_BR.md). Aumenta I/O e CPU por **arquivo**; o padrão é só por extensão. **CLI:** `--content-type-check` força isso numa execução one-shot. **API/dashboard:** `content_type_check: true` no corpo de **`POST /scan`** ou a caixa no dashboard aplica só àquela varredura; o `config.yaml` gravado não é alterado. Detalhes e exemplos YAML: [USAGE.md](USAGE.md) (seção Global options / file_scan).
- **Rich media (opt-in):** `file_scan.scan_rich_media_metadata: true` lê amostras limitadas de metadados: EXIF de imagens (Pillow), tags de áudio (**mutagen** — `uv pip install -e ".[richmedia]"`) e tags de vídeo com **ffprobe** (binário no `PATH`). `file_scan.scan_image_ocr: true` aciona **Tesseract** numa miniatura limitada (`pytesseract` + pacote do sistema `tesseract-ocr`). **Privacidade:** OCR lê **pixels visíveis**; habilite só onde houver base legal e política clara. Padrão **false** para ambos. `ocr_lang` (padrão `eng`) e `ocr_max_dimension` (padrão 2000, entre 256 e 8000) ajustam o OCR.
- **Legendas (padrão):** `.srt`, `.vtt`, `.ass`, `.ssa` entram na lista padrão de extensões e são lidas como texto UTF-8 (normalização de tempos), sem flag extra.
- **Formatos adicionais (Tier 1 “data soup”):** o scanner pode amostrar texto de **`.epub`** (ZIP/XHTML) e, com dependências opcionais (`uv pip install -e ".[dataformats]"`), de **`.parquet`**, **`.feather`**, **`.orc`** (PyArrow), **`.avro`** (fastavro) e **`.dbf`** (dbfread). Sem esses extras, a extração fica vazia nos binários colunares/legados (análise por caminho/nome continua). Inclua essas extensões em `file_scan.extensions` se usar lista explícita.
- **Extensão `.doc` (extra opcional `legacy-doc`):** amostra de corpo usa **`mammoth`** quando você instala **`pip install -e ".[legacy-doc]"`** ou `uv sync --extra legacy-doc`. O mammoth mira **OOXML em ZIP** (mesma família que `.docx`); `.doc` **binário Word 97-2003** em geral ainda gera amostra de conteúdo **vazia** — só caminho/nome entram na análise. Veja [TROUBLESHOOTING.pt_BR.md](TROUBLESHOOTING.pt_BR.md) (*Arquivos `.doc` legados*).
- **Dicas de esteganografia (opt-in):** `file_scan.scan_for_stego: true`, **`--scan-stego`**, caixa no dashboard ou `scan_for_stego: true` em **`POST /scan`** acrescenta uma linha de **entropia de bytes** em imagens/áudio/vídeo (heurística fraca; não é extração de stego). Mesmo padrão de restauração após a execução que `scan_compressed` / `use_content_type`.
- `report` – `output_dir` para relatórios/heatmaps; opcionalmente `recommendation_overrides` (lista de mapeamentos por `norm_tag` para Base legal, Risco, Recomendação, Prioridade, Relevante para). Exemplo completo em [USAGE.md](USAGE.md) (seção 4, Global options); exemplo para categorias sensíveis (saúde, religião, política, PEP, raça, sindicato, genético, biométrico, vida sexual) em [USAGE.md#recommendation_overrides](USAGE.md) e abaixo em pt-BR (ver também [SENSITIVITY_DETECTION.pt_BR.md](SENSITIVITY_DETECTION.pt_BR.md)).
- **`jurisdiction_hints` (opt-in):** notas heurísticas na planilha **Report info** para DPO/advogado quando **metadados dos achados** (nomes de coluna/arquivo/caminho, tags) sugerem possível relevância a **EUA-CA (CCPA/CPRA)**, **Colorado** ou **Japão (APPI)**. Não é conclusão jurídica; taxa alta de falso positivo/negativo. Ative com `report.jurisdiction_hints.enabled: true`, **`--jurisdiction-hint`** na CLI, caixa no dashboard ou `"jurisdiction_hint": true` em **`POST /scan`**. Sub-chaves: `us_ca`, `us_co`, `jp` e limiares `min_score_*`. Não altera níveis de sensibilidade. Detalhes: [USAGE.md](USAGE.md) (Global options / file_scan — mesmo tema em inglês no parágrafo sobre **jurisdiction hints**).
- `api` – porta da API; opcionalmente `require_api_key`, `api_key` ou `api_key_from_env` para exigir chave de API (cabeçalho X-API-Key ou Authorization: Bearer); GET /health permanece público. **Em produção recomenda-se** `require_api_key: true` e chave forte via variável de ambiente (ex.: `api.api_key_from_env: "AUDIT_API_KEY"`) para não armazenar a chave no config. Ver [SECURITY.md](../SECURITY.md).
- Por padrão, quando você inicia a API via CLI (`python main.py --web ...`), o servidor web faz bind em **`127.0.0.1` (loopback)**. No container oficial (Docker image), ele define `API_HOST=0.0.0.0` para que a porta publicada funcione a partir de fora do Docker Desktop/WSL.

- Se você estiver atrás de proxy reverso ou com restrições de rede específicas, ainda pode sobrescrever com `api.host` no config (por exemplo, `0.0.0.0` / `127.0.0.1`) — mas mantenha o default seguro em `127.0.0.1` a menos que o runtime esteja explicitamente cercado por regras de rede/Ingress.
- `sqlite_path` – caminho do banco SQLite com resultados.
- `scan` – `max_workers` para paralelismo.
- `timeouts` – timeouts globais para conexões (ex.: `connect_seconds`, `read_seconds`); cada alvo pode sobrescrever com `connect_timeout`, `read_timeout` ou `timeout`. Ver abaixo.
- `api.workers` – número de workers uvicorn (padrão 1; 2+ para mais requisições concorrentes).
- Opcionais: **`sql_sampling`** (tetos hierárquicos de amostragem SQL/Snowflake; ver bullet `file_scan` acima e [USAGE.md](USAGE.md)), `ml_patterns_file`, `dl_patterns_file`, `regex_overrides_file`, `sensitivity_detection` (termos ML/DL inline), `learned_patterns` (export de termos classificados), **`pattern_files_encoding`** (encoding dos arquivos de padrões; ver abaixo).
- **Pedindo acesso à TI:** Quando for preciso solicitar permissões à equipe de TI (ex.: pastas compartilhadas, contas de banco, tokens de API), solicite o **mínimo** necessário. Veja [OPERATOR_IT_REQUIREMENTS.pt_BR.md](ops/OPERATOR_IT_REQUIREMENTS.pt_BR.md) para o checklist por fonte (somente leitura, sem admin), o que não precisamos e uma breve justificativa, alinhada a zero-trust ou IAM restrito. ([EN](ops/OPERATOR_IT_REQUIREMENTS.md))

### Config inicial (copiar e colar) e onde começar {#config-inicial-exemplos}

Se você está **começando agora** (jurídico, DPO, liderança de auditoria ou **validação de capacidades**) e precisa de **um único arquivo** para alinhar com a TI **sem** ler todos os guias primeiro:

1. Abra o **hub** **[docs/samples/README.pt_BR.md](samples/README.pt_BR.md)** ([EN](samples/README.md)) — ele aponta para o YAML *starter*, o modelo mínimo Docker, o CSV de escopo e explica **`config/config.json`** (JSON legado só para referência).
1. Copie **[deploy/samples/config.starter-lgpd-eval.yaml](../deploy/samples/config.starter-lgpd-eval.yaml)** para a sua máquina como **`config.yaml`**. O arquivo traz **valores padrão utilizáveis** (duas pastas + um banco + timeouts + limite de taxa + termos ML/DL) e **blocos opcionais comentados** (ex.: arquivos compactados, `file_passwords`, `learned_patterns`) para ir habilitando aos poucos.
1. Substitua os caminhos **fictícios** (`/opt/lgpd-demo/...`) e o host **`192.0.2.10`** (rede só de documentação) pelos valores de laboratório reais.
1. Defina a variável de ambiente de **`pass_from_env`** (exemplo: `DEMO_DB_PASSWORD`) **antes** de subir o processo — não coloque senhas reais no YAML em produção.
1. Execute uma varredura one-shot: `uv run python main.py --config config.yaml` ou suba o painel com o mesmo `--config`.

O *starter* **não** substitui os grandes YAML de **`docs/compliance-samples/`** (ajuste fino por norma).

Em **Docker**, comece por **[deploy/config.example.yaml](../deploy/config.example.yaml)** e una trechos do *starter* se precisar de um perfil de laboratório mais completo.

**JSON legado:** O arquivo **`config/config.json`** no repositório só ilustra o formato antigo `databases` + `file_scan.directories` — veja **[config/README.pt_BR.md](../config/README.pt_BR.md)**. **Prefira YAML** em projetos novos.

### Importação de escopo a partir de CSV (fragmento de config) {#scope-import-csv-fragment}

Dá para **montar a lista de `targets`** a partir de um **CSV canônico** (por exemplo exportado de uma planilha) e gerar um **fragmento YAML** para colar em `targets:` ou salvar em arquivo para revisão. O produto **não** mescla automaticamente com um `config.yaml` existente; o operador revisa e integra manualmente ou com ferramentas próprias.

- **Script:** `uv run python scripts/scope_import_csv.py <arquivo.csv>` imprime YAML no stdout; `-o saida.yaml` grava arquivo. `--no-merge-hint` omite o bloco inicial de comentários.
- **Coluna obrigatória:** `type` (ex.: `filesystem`, `postgresql`, `mysql`, `database`, `smb`, `nfs`). Cabeçalhos são reconhecidos sem distinção de maiúsculas/minúsculas; espaços viram `_`.
- **Colunas usuais:** `name`, `path`, `host`, `port`, `database`, `driver`, `user`, `pass_from_env`, `user_from_env`, `share`, `domain`, `export_path`, `recursive`, além de breadcrumbs opcionais: `asset_id`, `hostname`, `ip`, `tags` (vários valores com `|` ou `;`), `path_hints`, `port_hints`, `source_system`, `source_export_type`, `confidence`. Metadados opcionais ficam em `scope_import` em cada alvo.
- **Segredos:** Prefira `pass_from_env` / `user_from_env` no CSV; **não** coloque senhas reais no arquivo.
- **Privacidade:** Exportações podem listar infraestrutura sensível — trate como config (permissões, evite commit acidental). Ver [SECURITY.md](../SECURITY.md).
- **Exemplo:** [`deploy/scope_import.example.csv`](../deploy/scope_import.example.csv).
- **Quem não é de TI:** [docs/ops/SCOPE_IMPORT_QUICKSTART.pt_BR.md](ops/SCOPE_IMPORT_QUICKSTART.pt_BR.md) ([EN](ops/SCOPE_IMPORT_QUICKSTART.md)) — montar o CSV a partir de planilha ou memória quando ainda não houver export do CMDB.

O comportamento está em `config/scope_import_csv.py` (v1: `filesystem`, `database` / aliases SQL, `smb`, `nfs`). Detalhes em inglês: [USAGE.md](USAGE.md) (mesma seção).

### Encoding de arquivos (config e arquivos de padrões) {#file-encoding-config-and-pattern-files}

Config e amostras de conformidade podem usar diferentes conjuntos de caracteres. A aplicação suporta isso para que termos multilíngues (ex.: japonês, árabe, francês) e ambientes legados não quebrem em produção.

- **Arquivo de config:** Lido com **auto-detecção**: UTF-8, UTF-8 com BOM, ANSI Windows (cp1252) e Latin-1 são tentados em ordem. Não é necessário definir encoding para o config principal.
- **Arquivos de padrões** (`regex_overrides_file`, `ml_patterns_file`, `dl_patterns_file`): Lidos com o encoding definido por **`pattern_files_encoding`** (padrão **`utf-8`**). Use quando seus YAML/JSON estiverem em outro encoding (ex.: `cp1252`, `latin_1`, `utf-8-sig`). Bytes inválidos são substituídos para que um caractere problemático não derrube a varredura.
- **Recomendação:** Salve todos os configs e amostras em **UTF-8** para melhor compatibilidade com conteúdo multilíngue (amostras para APAC, EMEA etc.). O relatório Excel e o heatmap suportam Unicode.

Exemplo no config:

```yaml
pattern_files_encoding: utf-8   # padrão; ou cp1252, latin_1, utf-8-sig para legado
regex_overrides_file: docs/compliance-samples/compliance-sample-uk_gdpr.yaml
ml_patterns_file: docs/compliance-samples/compliance-sample-pipeda.yaml
```

**Padrões regex customizados:** Para a aplicação se atentar a **novos valores possivelmente pessoais ou sensíveis** (ex.: RG, placa, número de plano de saúde), defina **`regex_overrides_file`** no config com o caminho de um arquivo YAML/JSON contendo uma lista de `{ name, pattern, norm_tag }`. O detector aplica cada padrão ao nome da coluna e ao texto amostrado; qualquer match é reportado com sensibilidade HIGH (ou MEDIUM em contexto de letras/cifras). Formato e exemplos (RG, placa, CEP, telefone EUA, etc.): [SENSITIVITY_DETECTION.pt_BR.md#padrões-regex-customizados-detectar-novos-dados-pessoaissensíveis](SENSITIVITY_DETECTION.pt_BR.md#padrões-regex-customizados-detectar-novos-dados-pessoaissensíveis) (pt-BR) · [SENSITIVITY_DETECTION.md#custom-regex-patterns-detecting-new-personalsensitive-values](SENSITIVITY_DETECTION.md#custom-regex-patterns-detecting-new-personalsensitive-values) (EN). Para **múltiplas regulamentações e exemplos de configuração** (embutidas: LGPD, GDPR, CCPA, HIPAA, GLBA; extensibilidade para UK GDPR, PIPEDA, POPIA, APPI, PCI-DSS ou custom) e ajuda com ajuste fino, veja [COMPLIANCE_FRAMEWORKS.pt_BR.md](COMPLIANCE_FRAMEWORKS.pt_BR.md) ([EN](COMPLIANCE_FRAMEWORKS.md)).

**Outras regulamentações e amostras de conformidade:** Amostras de config prontas para **UK GDPR**, **EU GDPR**, **Benelux**, **PIPEDA**, **POPIA**, **APPI**, **PCI-DSS** e outras regiões estão em [compliance-samples/](compliance-samples/). Defina `regex_overrides_file` e `ml_patterns_file` com o arquivo da amostra e mescle o `recommendation_overrides` da amostra em `report.recommendation_overrides`. Lista completa, o que vai onde e como usar: [COMPLIANCE_FRAMEWORKS.pt_BR.md – Amostras de conformidade](COMPLIANCE_FRAMEWORKS.pt_BR.md#amostras-de-conformidade) ([EN](COMPLIANCE_FRAMEWORKS.md#compliance-samples)).

**Checklist ao usar arquivo de amostra de compliance:**

1. **Mesclar** o `recommendation_overrides` da amostra em `report.recommendation_overrides` na config principal — sem isso, a aba **Recomendações** cai só no texto genérico embutido.
1. **Revisar** entradas `regex` opcionais; padrões regionais com dígitos podem gerar ruído em texto amplo (veja [SENSITIVITY_DETECTION.pt_BR.md](SENSITIVITY_DETECTION.pt_BR.md#padrões-genéricos-de-dígitos-e-escopo-de-falso-positivo)).
1. **Ordenar** `recommendation_overrides` com `norm_tag_pattern` **mais específico** **antes** de substrings genéricas (ex.: **UK GDPR** antes de **GDPR**). O casamento usa **primeira entrada** (semântica de substring).

**Exemplo `recommendation_overrides` para categorias sensíveis (LGPD Art. 5 II, 11; GDPR Art. 9):** Você pode adicionar entradas para que achados de saúde, religião, política, PEP, raça, sindicato, genético, biométrico e vida sexual tenham Base legal, Risco e Prioridade corretos na aba Recomendações. Exemplo (inglês): [USAGE.md](USAGE.md). Em pt-BR, use os mesmos `norm_tag_pattern` (ex.: `health`, `religious`, `political`, `PEP`, `race`, `union`, `genetic`, `biometric`, `sex life`) e preencha `base_legal`, `risk`, `recommendation`, `priority`, `relevant_for` conforme sua política. Ver [SENSITIVITY_DETECTION.pt_BR.md](SENSITIVITY_DETECTION.pt_BR.md).

### Rate limiting e segurança contra abuso

Para evitar DoS acidental ou abuso (muitas varreduras em sequência ou sessões demais em paralelo), use o bloco `rate_limit` no config:

```yaml
rate_limit:
  enabled: true               # quando presente, o padrão é true
  max_concurrent_scans: 1     # máximo de varreduras em execução ao mesmo tempo (API)
  min_interval_seconds: 0     # intervalo mínimo em segundos entre inícios de varredura
  grace_for_running_status: 0 # opcional; tolerância extra quando o status ainda mostra running
```

- Quando `rate_limit.enabled` for true, os endpoints de início de varredura (`POST /scan`, `POST /start`, `POST /scan_database`) podem responder **HTTP 429** com JSON:

  ```json
  {
    "detail": {
      "error": "rate_limited",
      "reason": "too_many_running_scans",
      "running_scans": 2,
      "max_concurrent_scans": 1,
      "source": "scan"
    }
  }
  ```

- A CLI usa a mesma lógica apenas para imprimir **avisos** (não muda o código de saída), de forma a manter scripts existentes funcionando enquanto você enxerga quando sua política bloquearia chamadas via API/dashboard.
- É possível sobrescrever os valores via variáveis de ambiente: `RATE_LIMIT_ENABLED`, `RATE_LIMIT_MAX_CONCURRENT_SCANS`, `RATE_LIMIT_MIN_INTERVAL_SECONDS`, `RATE_LIMIT_GRACE_FOR_RUNNING_STATUS`.
- **Produção:** O rate limiting é a primeira linha de defesa contra abuso e sobrecarga de varreduras. Desabilitar ou relaxar os limites (ex.: `max_concurrent_scans` alto ou `min_interval_seconds` zero) aumenta o risco de abuso e esgotamento de recursos; mantenha os limites ativos com valores conservadores em produção.

### Timeouts para conexões com fontes de dados

É possível configurar timeouts de conexão e de leitura (em segundos) usados ao abrir e ler bancos, APIs ou outros alvos. Os padrões globais valem para todos os alvos; cada alvo pode sobrescrevê-los.

```yaml
timeouts:
  connect_seconds: 25   # padrão 25 — tempo máximo para estabelecer conexão
  read_seconds: 90      # padrão 90 — tempo máximo de espera para leitura/resposta
```

- **Sobrescrita por alvo:** Em qualquer alvo você pode definir `connect_timeout`, `read_timeout` ou um único `timeout` (usado para connect e read quando o outro não for definido). Os valores do alvo sobrescrevem os timeouts globais quando presentes. Valores em segundos; mínimo 1.

Exemplo (padrões globais e um alvo mais lento):

```yaml
timeouts:
  connect_seconds: 25
  read_seconds: 90

targets:

- name: fast-db

    type: database
    # usa 25 / 90
- name: slow-api

    type: api
    connect_timeout: 60
    read_timeout: 120

- name: legacy

    type: database
    timeout: 45   # 45 para connect e read
```

Os conectores usam os valores mesclados (global ou por alvo) ao abrir conexões e fazer I/O; veja o esquema do config e a documentação dos conectores.

### Timeouts e carga

Recomendações para que as varreduras permaneçam estáveis sem sobrecarregar os alvos nem esperar indefinidamente:

1. **Não espere para sempre:** Defina timeouts de conexão e de leitura para que um alvo travado não bloqueie toda a varredura. Use as dicas de falha no relatório para identificar falhas por timeout e qual alvo falhou.
1. **Não seja agressivo demais:** Timeouts muito baixos geram falsos timeouts em redes ocupadas ou lentas (ex.: durante backup). Se aparecerem muitos timeouts, **aumente** `connect_seconds` e `read_seconds` (ou por alvo `connect_timeout` / `read_timeout`) e considere reexecutar em horário de menor uso.
1. **Evite DoS e “muito rápido demais”:** Use **rate_limit** (ex.: `max_concurrent_scans: 1`, `min_interval_seconds: 5`) e **scan.max_workers: 1** (ou 2) para que o scanner não abra muitas conexões ao mesmo tempo. Isso reduz carga nos alvos e evita amplificar lentidão ou causar DoS.
1. **Janelas de backup ou manutenção:** Se as varreduras rodarem durante backup ou manutenção, aumente os timeouts e mantenha o paralelismo baixo; ou agende varreduras fora dessas janelas.
1. **Sobrescrita por alvo:** Para um banco ou API lento, defina `connect_timeout` / `read_timeout` (ou `timeout`) nesse alvo em vez de aumentar os padrões globais para todos.

### API e segurança (CSP, cabeçalhos)

A API web e o dashboard enviam **cabeçalhos de segurança** em toda resposta (veja [SECURITY.md](../SECURITY.md)): X-Content-Type-Options, X-Frame-Options, **Content-Security-Policy (CSP)**, Referrer-Policy, Permissions-Policy e HSTS quando a requisição é considerada HTTPS.

- **CSP padrão:** Scripts e estilos são permitidos da origem da aplicação (`'self'`). O dashboard carrega o Chart.js do **CDN jsDelivr** (`<https://cdn.jsdelivr.ne>t`), permitido por padrão para o gráfico “Progress over time”. Uma quantidade mínima de script inline é usada para os dados do gráfico; o restante da lógica do dashboard fica em `/static/dashboard.js`.
- **CSP mais restrito:** Para remover `'unsafe-inline'` (ex.: perfil de alta segurança), você pode definir um CSP mais restrito no **proxy reverso** (sobrescrevendo o cabeçalho da aplicação) ou usar um toggle de env/config se a aplicação passar a oferecer um no futuro. Com CSP mais restrito, todo script e estilo deve vir de origens permitidas (`'self'` e o CDN); qualquer script inline restante nos templates precisaria ser refatorado para arquivos externos. Veja [SECURITY.md](../SECURITY.md) e [docs/deploy/DEPLOY.pt_BR.md](deploy/DEPLOY.pt_BR.md) ([EN](deploy/DEPLOY.md)) (Security and hardening) para endurecimento de implantação (Docker, Kubernetes, proxy reverso).

Para detalhes de todos os campos e exemplos completos, consulte `README.md` e `docs/USAGE.md` (inglês), que são as referências canônicas.

**Produção atrás de proxy reverso (nginx, Traefik, Caddy):** A aplicação se comporta corretamente atrás de NAT, load balancer ou proxy reverso. Quando o TLS for terminado no proxy, defina **X-Forwarded-Proto: https** para que os cabeçalhos de segurança (ex.: HSTS) funcionem. Veja [SECURITY.md](../SECURITY.md) para os cabeçalhos HTTP de segurança.

#### Formatos de CNPJ (legado numérico e alfanumérico)

Para o **CNPJ** brasileiro, o detector inclui dois padrões regex embutidos:

- `LGPD_CNPJ` – formato **legado, apenas numérico** (14 dígitos, pontuação opcional `./-/`: `XX.XXX.XXX/XXXX-XX`).
- `LGPD_CNPJ_ALNUM` – formato **alfanumérico** em que as 12 primeiras posições podem conter `A–Z` ou `0–9`, e as duas últimas posições permanecem dígitos (check digits); a pontuação é opcional nos mesmos lugares.

Ambos usam o mesmo `norm_tag` (`LGPD Art. 5`). Nesta etapa a detecção é apenas por **compatibilidade de formato** (sem validação de dígito verificador); veja [SENSITIVITY_DETECTION.pt_BR.md](SENSITIVITY_DETECTION.pt_BR.md#formatos-de-cnpj-brasil-numérico-legado-e-alfanumérico) para detalhes e para saber como estender/substituir padrões via `regex_overrides_file`.

### Notificações ao operador (opcional)

Após o fim da varredura (CLI ou `POST /scan` / `POST /start` em segundo plano), a aplicação pode enviar um **resumo curto em pt-BR** para **Slack**, **Microsoft Teams**, um **webhook JSON genérico** (ex.: ferramentas de automação ou ponte **Signal**) ou **Telegram** (campos opcionais para instalações legadas/de terceiros). O padrão é **desligado** (`notifications.enabled: false`).

- **Política do mantenedor (repositório canônico):** O mantenedor **não** usa **Telegram** para notificações ao operador do Data Boar; prefira **Slack**, **Teams** ou **webhook genérico** para **Signal**. Ver [OPERATOR_NOTIFICATION_CHANNELS.pt_BR.md](ops/OPERATOR_NOTIFICATION_CHANNELS.pt_BR.md).
- **Config (caminho único legado):** `notifications.operator` com `slack_webhook_url`, `teams_webhook_url`, `telegram_bot_token` + `telegram_chat_id` ou `generic_webhook_url` — vale o primeiro tipo configurado (Slack → Teams → Telegram → genérico).
- **Config (vários canais ao operador):** `notifications.operator.channels` como **lista** de objetos; cada item é **um** canal (ex.: um webhook Slack e um webhook genérico). Todos recebem a mesma mensagem (varredura concluída ou script manual).
- **Cópia ao tenant (opcional):** `notifications.tenant.by_tenant` mapeia o nome do tenant em **minúsculas** para um bloco de webhook (ou string URL para POST genérico). `default_slack_webhook_url` / `default_generic_webhook_url` aplicam quando há `tenant_name` na sessão mas não há entrada específica. Exige `tenant_name` não vazio na sessão.
- **Deduplicação:** `notifications.dedupe_scan_complete_per_session` (padrão `true`) evita um segundo POST para o mesmo `session_id` depois de **pelo menos um** envio bem-sucedido (por processo; use `false` só se precisar repetir em todo hook de conclusão).
- **Registro de auditoria (opcional):** `notifications.notify_audit_log` (padrão `true`) grava uma linha por tentativa/canal na tabela SQLite **`notification_send_log`** (sessão, *trigger*, destino `operator`/`tenant`, canal, sucesso, texto de erro redigido, carimbo de tempo). **Não** armazena o corpo da mensagem. Use `false` para desligar escritas.
- **Segredos:** URLs podem usar `${VAR_DE_AMBIENTE}`. Os POSTs repetem algumas vezes em HTTP 5xx ou erro de rede transitório.
- **Manual / CI:** `python scripts/notify_webhook.py "mensagem"` (mesmo `config.yaml`; exige `notifications.enabled: true` e um canal configurado). Por padrão o script abre o SQLite em ``sqlite_path`` e grava auditoria por canal (como no fim de varredura); use ``--no-audit`` quando não houver banco local (ex.: alguns jobs de CI).
- **Detalhes:** [TECH_GUIDE.pt_BR.md](TECH_GUIDE.pt_BR.md) (notificações e webhooks) e [ops/OPERATOR_NOTIFICATION_CHANNELS.pt_BR.md](ops/OPERATOR_NOTIFICATION_CHANNELS.pt_BR.md).

**Documentação relacionada:** Índice completo da documentação (todos os tópicos, ambos os idiomas): [README.md](README.md) · [README.pt_BR.md](README.pt_BR.md). Guia técnico: [TECH_GUIDE.md](TECH_GUIDE.md) · [TECH_GUIDE.pt_BR.md](TECH_GUIDE.pt_BR.md). [SENSITIVITY_DETECTION.pt_BR.md](SENSITIVITY_DETECTION.pt_BR.md) (termos de treino ML/DL; [inglês](SENSITIVITY_DETECTION.md)). Para `recommendation_overrides` cobrindo categorias sensíveis (saúde, religião, política, PEP, raça, sindicato, genético, biométrico, vida sexual), veja o exemplo acima (Notas sobre configuração) e [SENSITIVITY_DETECTION.pt_BR.md](SENSITIVITY_DETECTION.pt_BR.md). Para adicionar um novo conector (banco, API, share), veja [ADDING_CONNECTORS.pt_BR.md](ADDING_CONNECTORS.pt_BR.md) ou [ADDING_CONNECTORS.md](ADDING_CONNECTORS.md) (inglês). Deploy: [deploy/DEPLOY.pt_BR.md](deploy/DEPLOY.pt_BR.md) · [deploy/DEPLOY.md](deploy/DEPLOY.md). Mais: [TESTING.pt_BR.md](TESTING.pt_BR.md) ([EN](TESTING.md)), [TOPOLOGY.pt_BR.md](TOPOLOGY.pt_BR.md) ([EN](TOPOLOGY.md)), [COMMIT_AND_PR.pt_BR.md](ops/COMMIT_AND_PR.pt_BR.md) ([EN](ops/COMMIT_AND_PR.md)), [COMPLIANCE_FRAMEWORKS.pt_BR.md](COMPLIANCE_FRAMEWORKS.pt_BR.md) ([EN](COMPLIANCE_FRAMEWORKS.md)). Em sistemas com `man`: `man data_boar` ou `man lgpd_crawler` (comando e API), e `man 5 data_boar` ou `man 5 lgpd_crawler` (config e formatos).
