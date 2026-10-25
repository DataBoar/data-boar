# Avaliacao de conectividade externa (APIs publicas, datasets, BD somente leitura)

**English:** [LAB_EXTERNAL_CONNECTIVITY_EVAL.md](LAB_EXTERNAL_CONNECTIVITY_EVAL.md)

**Objetivo:** Checklist **reproduzivel** para validar que os **conectores** do Data Boar se comportam bem contra APIs HTTP de terceiros e (onde permitido) endpoints SQL/NoSQL **somente leitura**. **Complementa** [LAB_SMOKE_MULTI_HOST.md](LAB_SMOKE_MULTI_HOST.md) (pilhas na LAN) e o **CI** — **nao** substitui.

**Ambito:** Este arquivo rastreado permanece **sem** hostnames reais, **sem** IPs de LAN, **sem** palavras-passe e **sem** estrategia de operador. Copie modelos de **`docs/private.example/homelab/`** para **`docs/private/`** e preencha segredos la. **Nunca** commite credenciais nem palavras-passe de leitura publica (ex. RNAcentral) no Git.

---

## 1. O que o Data Boar pode exercitar aqui

| Area do conector | `type` / `driver` em config | Uso tipico nesta avaliacao |
| ---------------- | --------------------------- | -------------------------- |
| REST/HTTP JSON | `api` ou `rest`, `base_url` + `paths` | APIs de demonstracao publicas (GET JSON). |
| PostgreSQL / MariaDB / MySQL | `database` + driver SQLAlchemy | BDs publicos **so** onde os ToS permitirem; prefira **Docker local** ou [postgres-sample-dbs](https://github.com/neondatabase/postgres-sample-dbs) no **seu** host. |
| MongoDB | `database`, `driver: mongodb` | **`deploy/lab-smoke-stack/docker-compose.mongo.yml`** (recomendado) ou instancia sua. |
| Arquivos (filesystem) | `filesystem` | **`tests/data/compressed`**, **`tests/data/homelab_synthetic`**, amostras protegidas por senha conforme [GLOSSARY.pt_BR.md](../GLOSSARY.pt_BR.md) (*password-protected archive or document*). |

**Fora do ambito "internet publica":** abusar de rate limits, scraping sem contrato de API, ou armazenar payloads de terceiros em relatorios alem da politica de metadados/findings.

---

## 2. Taxonomia (atalhos)

| Etiqueta | Significado |
| -------- | ----------- |
| **E2E-OK** | Alcancavel; conector conclui; findings ou negativo limpo como esperado. |
| **E2E-FAIL-EXPECTED** | Host/porta/credenciais **intencionalmente** errados — valida **`scan_failures`**, timeouts e mensagens ao tecnico. |
| **E2E-SKIP** | Bloqueado por firewall, ToS ou terceiro offline — **nao** e defeito do produto. |

Corra **pelo menos duas** categorias por sessao (ex. um **OK** + um **FAIL-EXPECTED**) para nao confundir com indisponibilidade passageira.

---

## 3. Recursos de referencia (so links; sem segredos)

| Tipo | Exemplo (verificar ToS antes) |
| ---- | ----------------------------- |
| API REST demo | [restful-api.dev](https://restful-api.dev/) — endpoints `GET` publicos (limites de taxa). |
| Amostras Postgres (clonar/carregar local) | [neondatabase/postgres-sample-dbs](https://github.com/neondatabase/postgres-sample-dbs). |
| Listas / rankings | [db-engines.com ranking](https://db-engines.com/en/ranking); artigos (ex. [DataCosmos — BD gratis para teste](https://www.datacosmos.com.br/en/post/5-free-database-to-test-and-develop)) — **nao** sao endossos. |
| Postgres somente leitura (ciencia) | [RNAcentral public Postgres](https://rnacentral.org/help/public-database) — **credenciais na pagina do fornecedor**; nao colar no Git; respeitar politica de uso. |
| Datasets Kaggle | [kaggle.com/datasets](https://www.kaggle.com/datasets) — descarregar pelas regras deles; usar como **filesystem** apos extrair. |
| Listas SQL sample | Blogs terceiros (Red9, Software Testing Magazine, etc.) — **ponteiros**, nao garantias. |
| Ferramentas NoSQL (nao substituem o Data Boar) | [NoSQLBench](https://docs.nosqlbench.io/introduction/), [NoSQLUnit](https://www.methodsandtools.com/tools/nosqlunit.php) — geracao/carga **em volta** dos scans. |
| Amostras MongoDB | [MongoDB sample datasets (Atlas)](https://www.mongodb.com/resources/basics/databases/sample-database) — termos de nuvem; Docker local prefivel para lab fixo. |

---

## 4. Falhas intencionais (uteis ao runbook do tecnico)

Configure alvos que **devem** falhar: IP de documentacao (ex. `192.0.2.1`) em porta fechada; credenciais erradas contra **o seu** contentor de lab; `read_timeout_seconds` baixo contra URL lenta. Documente em **`scan_failures`** / logs de sessao.

---

## 5. Office / PDF / arquivos protegidos por senha

Sem senha fornecida, conteudo encriptado **nao** e legivel — espere **falsos negativos**; ver **GLOSSARY** e limitacoes em **USAGE**. Para testar desbloqueio, use **`file_passwords`** (ou env) conforme **TECH_GUIDE**; listas de senhas **privadas** ou gitignored.

---

## 6. Firewall (passos genericos; sem IPs reais)

Num **hub Linux** que aceita clientes BD na LAN: **UFW** — permitir **so** a sub-rede de lab para as portas publicadas (ex. `55432`, `33306`); **nftables** — regra `accept` equivalente e **drop** de WAN. **Windows:** regras avancadas do firewall para portas publicadas pelo Docker quando clientes LAN se ligam. Comandos com **a sua** CIDR ficam em **`docs/private/homelab/`**.

---

## 7. Automacao neste repositorio

| Artefato | Funcao |
| -------- | ------ |
| **`scripts/lab-external-smoke.ps1`** | Chegada rapida (HTTP GET, TCP opcional) no PC do operador — **nao** e scan completo do Data Boar. |
| **`deploy/lab-smoke-stack/docker-compose.mongo.yml`** | MongoDB local opcional para `driver: mongodb`. |
| **`docs/private.example/homelab/config.external-eval.example.yaml`** | Modelo — copiar para privado e preencher. |
| **`.cursor/skills/lab-external-connectivity-eval/SKILL.md`** | Reproducao token-aware para assistentes. |

Token de chat: **`external-eval`** (ver **`.cursor/rules/session-mode-keywords.mdc`**).

---

## 8. Sinal de prontidao para PRD?

**Parcial.** Passar nesta avaliacao mostra conectores e mensagens sob variancia de rede e falhas **controladas**. **Prontidao de producao** continua a exigir [HOMELAB_VALIDATION.md](HOMELAB_VALIDATION.md), [SECURITY.md](../SECURITY.md), notas de release e configuracao por cliente.

---

## 9. Documentos relacionados

- [LAB_SMOKE_MULTI_HOST.md](LAB_SMOKE_MULTI_HOST.md)
- [TROUBLESHOOTING_MATRIX.md](../TROUBLESHOOTING_MATRIX.md)
- [USAGE.md](../USAGE.md)
- ADR [0028](../adr/ADR-0028-lab-external-connectivity-eval-playbook.md)
