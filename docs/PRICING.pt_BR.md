# Mapa de recursos por faixa de assinatura

**English:** [PRICING.md](PRICING.md)

Esta página responde **o que está em cada faixa**. **Não** é lista de preços. Valores, descontos e taxas de canal ficam fora da árvore pública.

**Fonte da verdade:** `FEATURE_TIER_MAP` em `core/licensing/tier_features.py` (faixa mínima por chave). As faixas são **aditivas** em modo enforced: Pro inclui as chaves Community; Enterprise inclui as de Pro.

Faixas de GTM, claims de **quantidade** (workers) e pacotes narrativos: [SUBSCRIPTION_TIERS.pt_BR.md](SUBSCRIPTION_TIERS.pt_BR.md). Rascunho de política: [LICENSING_OPEN_CORE_AND_COMMERCIAL.pt_BR.md](LICENSING_OPEN_CORE_AND_COMMERCIAL.pt_BR.md). Forma do token: [LICENSING_SPEC.pt_BR.md](LICENSING_SPEC.pt_BR.md). Como operar: [USAGE.pt_BR.md](USAGE.pt_BR.md).

O padrão em desenvolvimento/CI é `licensing.mode: open` (todas as chaves disponíveis). Os gates valem com enforcement ligado.

## Community / Pro / Enterprise (colunas do issue #610)

Agrupado a partir do registro. A célula é **incluída** quando a faixa da coluna é **pelo menos** o mínimo da chave.

| Grupo de capacidade | Community | Pro | Enterprise |
| ------------------- | :-------: | :-: | :--------: |
| Scan de filesystem; SQL/NoSQL self-hosted (`sqlite` / Postgres / MySQL / MariaDB / Mongo / Redis); conectores REST/API genéricos | Sim | Sim | Sim |
| Detectores centrais (CPF, RG, e-mail, telefone, heurística de nome, CNPJ, endereço); arquivos compactados; checagem de content-type; teste com dados sintéticos | Sim | Sim | Sim |
| Relatórios XLSX e HTML; API REST; dashBOARd; chaves de deploy Docker e Ansible | Sim | Sim | Sim |
| OCR; relatório PDF; relatório com nota de conformidade; scans agendados; RBAC do dashboard (fixo); UI de API key; POC de autoavaliação de maturidade; notificações e-mail/Slack; export de SBOM; verificação de integridade de build; sink SQL de achados; governance lens (chave Pro) | — | Sim | Sim |
| Conectores gerenciados / corporativos (Power BI, HubSpot, SharePoint, Dataverse, WebDAV, SMB/CIFS, NFS, MSSQL, Oracle, Snowflake, SAP, S3, Azure Blob, GCS) | — | Sim | Sim |
| Branding customizado de PDF; UI de scheduler Enterprise; governance lens Enterprise; multi-tenant; **SSO SAML**; assinatura digital de PDF; e-mail de PDF agendado; comparação histórica; export de audit log; detectores customizados; conector VCS; interface de plugin/parceiro; driver de provedor parceiro; plugin e export de manifesto de remediação | — | — | Sim |

**Ajustes em relação a um sketch de três bullets:** a **assinatura digital** de PDF é chave **Enterprise** (`pdf_digital_signature`), não Pro. **Não** existe chave `report_jsonl` — no mapa, relatório Community é **XLSX/HTML**. **SSO** no mapa é `sso_saml`; OIDC/LDAP aparecem em [SUBSCRIPTION_TIERS.pt_BR.md](SUBSCRIPTION_TIERS.pt_BR.md) como **intenção** de produto, não como chaves do `FEATURE_TIER_MAP`. SLA de suporte dedicado é **termo comercial**, não chave de feature.

## Outras faixas no registro (não omitir)

O mesmo arquivo define **Std** (`std`), **Pro+** (`pro_plus`), **Partner** e **Open** (`open` = enforcement desligado). Não são colunas extras de preço aqui.

| Faixa | O que o código diz |
| ----- | ------------------ |
| **Std** | Faixa de entrada comercial (Boar-Std). **Sem chaves exclusivas** no `FEATURE_TIER_MAP` — direito de uso/suporte vive em licença/claims, não neste mapa. |
| **Pro+** | `pro_prefilter_accel` (caminho CLI→ProScanner) e `rust_regex_stage` (estágio regex em Rust). |
| **Partner** | Enumerado para acordo de canal; capacidade **pelo menos Pro+** no comentário do módulo — sem chaves além da lista Enterprise/Pro+ acima. |
| **Open** | Bypass: todos os recursos no lab/dev. |

## Contato (sem valores)

Para avaliação Pro, Pro+, Partner ou Enterprise: **contact@databoar.com.br** ou abra uma issue neste repositório. Esta página não é orçamento.

## Drift

Quando adicionar uma chave em `FEATURE_TIER_MAP`, atualize esta página no mesmo PR.
