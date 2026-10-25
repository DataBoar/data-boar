# Guia de integração Enterprise (TI / SRE)

**English:** [ENTERPRISE_INTEGRATION_GUIDE.md](ENTERPRISE_INTEGRATION_GUIDE.md)

Esta página é para **DevOps, engenharia de segurança e SRE** que instalam e operam o Data Boar ao lado de pipelines já existentes. **Não** é lista de preços, cotação de franquia de volume nem pitch comercial. Faixas de capacidade: [SUBSCRIPTION_TIERS.pt_BR.md](SUBSCRIPTION_TIERS.pt_BR.md). Porta no código: `FEATURE_TIER_MAP` em `core/licensing/tier_features.py`. Como executar: [USAGE.pt_BR.md](USAGE.pt_BR.md). Topologias de deploy: [deploy/DEPLOY.pt_BR.md](deploy/DEPLOY.pt_BR.md) ([EN](deploy/DEPLOY.md)).

**Audiência:** CLI, Python e CI/CD. Narrativa de conformidade fica em [COMPLIANCE_FRAMEWORKS.pt_BR.md](COMPLIANCE_FRAMEWORKS.pt_BR.md), não aqui.

## O que este guia não inventa

- **Sem preços Data Boar, cotação de SKU ou franquia de volume.** O site público ainda diz que o pricing vem em breve; termos comerciais estão em revisão. Claims JWT de **quantidade** que já embarcam (`dbmax_workers`, `dbmax_deployments`) estão em [SUBSCRIPTION_TIERS.pt_BR.md](SUBSCRIPTION_TIERS.pt_BR.md) e [LICENSING_SPEC.md](LICENSING_SPEC.md) (EN) — isso **não** é fatura.
- **SSO:** a **chave no mapa** entregue é `sso_saml` (Enterprise). **Não** há handshake SAML/OIDC/LDAP implementado neste repositório neste momento. OIDC e LDAP permanecem **intenção** em planos internos — não trate como IdP pronto.
- **Sem links Markdown para `docs/plans/`** nesta página ([ADR 0004](adr/ADR-0004-external-docs-no-markdown-links-to-plans.md)).
- **Enciclopédia de config:** as chaves YAML **não** são copiadas aqui (envelhecem). Canônico: [USAGE.pt_BR.md](USAGE.pt_BR.md) e [deploy/samples/](../deploy/samples/).

## 1. Requisitos de sistema

| Necessidade | Verdade na árvore |
| ----------- | ----------------- |
| **Python** | `requires-python = ">=3.12"` em `pyproject.toml`. |
| **Instalador** | [uv](https://docs.astral.sh/uv/) é o caminho do mantenedor (`uv sync`); pip/pipx servem para wheels publicados. |
| **SO** | CPython em **Linux** e **Windows** (nativo ou WSL2). A distro (família Debian, RHEL, Void, …) é assunto do **host**: clientes NFS/SMB, `tesseract`, `ffprobe` no `PATH`, não no wheel. |
| **PowerShell** | Opcional. Wrappers `scripts/*.ps1` ajudam o **operador**; o entrypoint do produto é `python main.py` ([USAGE.pt_BR.md](USAGE.pt_BR.md)). |
| **`py7zr` / 7z** | Extra opcional **`compressed`**: `py7zr` no `pyproject.toml`. Sem ele, ZIP/tar seguem via biblioteca padrão; membros **`.7z` são ignorados** (falha suave). Instale com `uv sync --extra compressed` ou `pip install 'data-boar[compressed]'`. Pacotes da distro são opcionais; não trate um único gerenciador de pacotes como o único caminho suportado. |
| **NFS / SMB** | Extra do produto: `.[shares]`. O cliente NFS ou Samba do **kernel/userland** é pacote do SO (`nfs-utils`, `cifs-utils`, etc. — nomes variam). O mount costuma ser da TI; o Data Boar precisa de **leitura + listagem** no caminho montado ([ops/OPERATOR_IT_REQUIREMENTS.pt_BR.md](ops/OPERATOR_IT_REQUIREMENTS.pt_BR.md)). |
| **`boar_fast_filter` (Rust / PyO3)** | **Acelerador opcional.** O wheel PyPI `data-boar` é `py3-none-any` **sem** extensão compilada — o matching cai para **Python puro**. Em faixas pagas, `--validate-config` emite **WARN** se o wheel faltar. O wheelhouse é o canal **documentado** do estágio Rust ([TROUBLESHOOTING.pt_BR.md](TROUBLESHOOTING.pt_BR.md)). **Não** é obrigatório para gerar achados. |

## 2. Padrões de implantação

Docker/Compose/Swarm/Kubernetes canônicos: [deploy/DEPLOY.pt_BR.md](deploy/DEPLOY.pt_BR.md). Imagem vs override CLI está lá (padrão **web** na **8088**; CLI one-shot **não** passa `--web`).

| Padrão | Ponteiro |
| ------ | -------- |
| **CLI standalone** | `python main.py --config /path/config.yaml` (opcional `--tenant` / `--technician`). Persista `sqlite_path` e `report.output_dir` em volume. |
| **Passo de CI/CD** | Pre-flight `--validate-config` ([#532](https://github.com/DataBoar/data-boar/issues/532)); scan; opcional `--diff` + `--fail-on-new-high` ([#565](https://github.com/DataBoar/data-boar/issues/565)). Segredos no cofre da CI, não no YAML. |
| **Scan agendado** | **cron** / **timer systemd** / CronJob do orquestrador chamando o mesmo CLI. A chave `scheduled_scans` é **Pro**; `scan_scheduler_ui_enterprise` é chave de **mapa Enterprise** (UI), não substitui um timer que funciona. |
| **Air-gapped / sem internet** | Espelhe o wheel da aplicação (e extras / wheelhouse de `boar_fast_filter`) num índice interno; `pip install --no-index --find-links …` como em [TROUBLESHOOTING.pt_BR.md](TROUBLESHOOTING.pt_BR.md). Carregue imagens Docker de um **registry interno**. Não existe SKU separado de air-gap. |

## 3. Configuração

1. Copie um **sample rastreado**; não monte YAML de memória: [deploy/samples/config.starter-lgpd-eval.yaml](../deploy/samples/config.starter-lgpd-eval.yaml) e [docs/samples/README.pt_BR.md](samples/README.pt_BR.md).
1. Credenciais no **ambiente** (`*_from_env`). `--validate-config` emite **WARN** se a variável estiver vazia, sem varrer.
1. **Conectores:** tipos e chaves obrigatórias são validados no `--validate-config`. Quais existem e em qual **faixa**: [SUBSCRIPTION_TIERS.pt_BR.md](SUBSCRIPTION_TIERS.pt_BR.md) + `FEATURE_TIER_MAP` (exemplo: REST genérico / SQL-NoSQL auto-hospedado = Community; Power BI, SharePoint, Snowflake, SAP, object storage, SMB/NFS/WebDAV, MSSQL, Oracle = **Pro**, salvo o mapa dizer o contrário). Novo conector: [ADDING_CONNECTORS.pt_BR.md](ADDING_CONNECTORS.pt_BR.md). Plugins de padrão: [PLUGIN_AUTHOR_GUIDE.pt_BR.md](PLUGIN_AUTHOR_GUIDE.pt_BR.md).
1. Timeouts: `timeouts:` global e `connect_timeout` / `read_timeout` por alvo em [USAGE.pt_BR.md](USAGE.pt_BR.md); falhas de rede: [TROUBLESHOOTING_CONNECTIVITY.pt_BR.md](TROUBLESHOOTING_CONNECTIVITY.pt_BR.md).

```bash
python main.py --config /path/config.yaml --validate-config
# exit 0 → [OK]; exit 1 → [INVALID] (conector desconhecido, chaves faltando, …)
```

## 4. Recursos de CI/CD (CLI entregue)

| Flag | Papel | Origem |
| ---- | ----- | ------ |
| `--validate-config` | Parse + checagem de conector/driver/chaves; sem scan em `[INVALID]` | [#532](https://github.com/DataBoar/data-boar/issues/532) |
| `--diff SESSION_A SESSION_B` | Achados novos / resolvidos / mudança de severidade | [#565](https://github.com/DataBoar/data-boar/issues/565) |
| `--fail-on-new-high` | Com `--diff`: exit **1** se `SESSION_B` tiver **HIGH** novos | mesma |
| `--export-dsar SESSION_ID` | JSON orientado a DSAR (metadados primeiro); `--dsar-output PATH` | [#522](https://github.com/DataBoar/data-boar/issues/522) |
| `--export-audit-trail [PATH]` | Trilha JSON a partir do SQLite | [USAGE.pt_BR.md](USAGE.pt_BR.md) |

UUID desconhecido em `--diff` → exit **2**. **Não** combine `--web` com esses flags de export/diff.

## 5. Stack existente (SIEM, GRC, notificações, API)

| Integração | O que existe |
| ---------- | ------------ |
| **SIEM / auditoria** | Ingerir JSON de `--export-audit-trail` (campos em [USAGE.pt_BR.md](USAGE.pt_BR.md)). **Push SARIF / SIEM** é capacidade de faixa **Pro+** em [SUBSCRIPTION_TIERS.pt_BR.md](SUBSCRIPTION_TIERS.pt_BR.md) — não é webhook open-core para Splunk. |
| **GRC / CSV-JSONL** | Relatórios Excel, JSON DSAR, JSON de auditoria, schema GRC: [REPORTS_AND_COMPLIANCE_OUTPUTS.pt_BR.md](REPORTS_AND_COMPLIANCE_OUTPUTS.pt_BR.md), [GRC_EXECUTIVE_REPORT_SCHEMA.pt_BR.md](GRC_EXECUTIVE_REPORT_SCHEMA.pt_BR.md). |
| **Slack / Teams / webhook genérico** | `notifications.enabled` (**desligado** por padrão). Webhook Slack do operador + kill-switch: [ops/OPERATOR_NOTIFICATION_CHANNELS.pt_BR.md](ops/OPERATOR_NOTIFICATION_CHANNELS.pt_BR.md). Manual: `python scripts/notify_webhook.py`. |
| **API HTTP** | Porta padrão **8088**. Endpoints: [USAGE.pt_BR.md](USAGE.pt_BR.md) / [TECH_GUIDE.pt_BR.md](TECH_GUIDE.pt_BR.md). **Auth:** API key opcional (`X-API-Key` ou `Authorization: Bearer`). WebAuthn JSON opcional quando ligado. **`GET /health` permanece sem autenticação** de propósito. |

## 6. Troubleshooting

| Sintoma | O que fazer |
| ------- | ----------- |
| **`boar_fast_filter` ausente / não compila** | Esperado em instalação só-PyPI. Achados seguem em Python. Ver [TROUBLESHOOTING.pt_BR.md](TROUBLESHOOTING.pt_BR.md). Opcional: injetar a partir de um wheelhouse compatível. `--prefilter-status` imprime JSON de prontidão. |
| **Timeout de conector** | Aumente `timeouts.connect_seconds` / `read_seconds` ou overrides por alvo; reduza `scan.max_workers`; [TROUBLESHOOTING_CONNECTIVITY.pt_BR.md](TROUBLESHOOTING_CONNECTIVITY.pt_BR.md). |
| **`$HOME` é root / vazio sob systemd ou `sudo`** | **Não** grave corpus ou relatórios num home implícito. Defina caminhos **absolutos** em `sqlite_path`, `report.output_dir` e variáveis de credencial no **usuário de serviço**. Scripts privilegiados deste repo resolvem o invocador via `SUDO_USER` / `getent` quando precisam — unidades de produção ainda devem usar caminhos explícitos. |
| **`.7z` não varrido** | Instale o extra **`compressed`** (`py7zr`). Sem ele, o skip é esperado. |

Auth e credenciais: [TROUBLESHOOTING_CREDENTIALS_AND_AUTH.pt_BR.md](TROUBLESHOOTING_CREDENTIALS_AND_AUTH.pt_BR.md).

## 7. Segurança da implantação

### Padrão da API key é aberto ([#549](https://github.com/DataBoar/data-boar/issues/549))

Os samples rastreados mantêm **`api.require_api_key` false** para o lab no laptop subir. Isso **não** é postura de produção.

**Contorno (obrigatório em bind fora de loopback):**

1. Defina `api.require_api_key: true`.
1. Chave forte via `api.api_key_from_env` (preferível) ou `api.api_key` (não faça commit).
1. Prefira loopback + proxy reverso com TLS. `main.py --web` **avisa** em stderr se o bind não for loopback e não houver chave efetiva; **sai com código 2** se a chave for exigida e estiver faltando.
1. Comportamento completo: [SECURITY.md](../SECURITY.md) na raiz, [docs/SECURITY.pt_BR.md](SECURITY.pt_BR.md), [ops/SECURE_DASHBOARD_AUTH_AND_HTTPS_HOWTO.pt_BR.md](ops/SECURE_DASHBOARD_AUTH_AND_HTTPS_HOWTO.pt_BR.md).

### Permissões de filesystem

Menor privilégio nos **alvos de scan**: [ops/OPERATOR_IT_REQUIREMENTS.pt_BR.md](ops/OPERATOR_IT_REQUIREMENTS.pt_BR.md). O **processo** precisa de escrita só onde **ele** persiste SQLite e relatórios — não nos repositórios de dados do cliente.

### Chaves de assinatura (não misture dois mundos)

- **JWT de licença do produto:** [LICENSING_SPEC.md](LICENSING_SPEC.md) — rode o material do **emissor** conforme o acordo; este guia não publica procedimentos que pertencem a pacotes comerciais privados.
- **[ADR 0056](adr/ADR-0056-cryptographic-adr-inventory-inv-adr-ssh-attestation.md)** (`inv-adr.ps1`, `docs/adr/INVENTORY.txt`, SSH ed25519): isso é **atestação G0-S do repositório** para Architecture Decision Records. **Não** é a chave SSO do dashboard e **não** é runbook de “rodar certificado SAML” do cliente. Mantenedores de fork seguem o ADR; TI que só implanta o scanner **não** precisa desse ritual para varrer.

## Docs de produto relacionados

| Doc | Por quê |
| --- | ------- |
| [SUBSCRIPTION_TIERS.pt_BR.md](SUBSCRIPTION_TIERS.pt_BR.md) | Seis faixas públicas; não existe `docs/PRICING.md` |
| [USAGE.pt_BR.md](USAGE.pt_BR.md) | CLI/API/config |
| [TECH_GUIDE.pt_BR.md](TECH_GUIDE.pt_BR.md) | Instalação, conectores, notificações |
| [PLUGIN_SDK.pt_BR.md](PLUGIN_SDK.pt_BR.md) | Host de plugin de remediação Enterprise (L1) |
| [AUDIENCE_GUIDE.pt_BR.md](AUDIENCE_GUIDE.pt_BR.md) | Quem lê o quê |
| [hubs/INDEX.pt_BR.md](hubs/INDEX.pt_BR.md) | Mapa dos mapas |
