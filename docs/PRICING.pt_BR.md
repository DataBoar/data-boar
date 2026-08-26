# Mapa de recursos e quantidade por faixa comercial

**English:** [PRICING.md](PRICING.md)

Esta página **não** é lista de preços. Valores, descontos, comissões de canal e cotações de franquia ficam fora da árvore pública (`docs/private/`). Contato: **contact@databoar.com.br**.

O issue no GitHub que pedia **só** Community / Pro / Enterprise está **desatualizado**. A escada viva é Community → Std → Pro → Pro+ → Enterprise → Partner / white-label (SKU), mais Open de lab (enforcement desligado). Strings de **Trial** no JWT hoje mapeiam para **Pro** no código.

## Dois eixos (não colapsar)

| Eixo | Pergunta | Fontes públicas |
| ---- | -------- | --------------- |
| **Capacidade (tier)** | O que este deployment pode fazer? | `Tier` + `FEATURE_TIER_MAP` em `core/licensing/tier_features.py`; JWT `dbtier` em `core/licensing/runtime_feature_tier.py` |
| **Quantidade (franquia)** | Quanta concorrência, quantos sites, quão grande o estate governado? | Implementado: `dbmax_workers`, `dbmax_deployments` ([LICENSING_SPEC.pt_BR.md](LICENSING_SPEC.pt_BR.md), [SUBSCRIPTION_TIERS.pt_BR.md](SUBSCRIPTION_TIERS.pt_BR.md)). **Franquias de tamanho de estate** (escopo lógico ativo, não bytes lidos por scan) estão **em avaliação comercial** e **não** são chaves do `FEATURE_TIER_MAP`. Aumentar volume **não** deve promover sozinho Pro → Pro+ / Enterprise. |

Narrativa GTM (RBAC, pacotes SIEM/RoPA, tabela de workers): [SUBSCRIPTION_TIERS.pt_BR.md](SUBSCRIPTION_TIERS.pt_BR.md). Rascunho de política: [LICENSING_OPEN_CORE_AND_COMMERCIAL.pt_BR.md](LICENSING_OPEN_CORE_AND_COMMERCIAL.pt_BR.md). Como operar: [USAGE.pt_BR.md](USAGE.pt_BR.md).

O padrão em CI/dev é `licensing.mode: open`. Os gates valem em `enforced`. A comparação aditiva usa `_TIER_ORDER` em `tier_features.py`.

## Aliases JWT / lab (código)

| Faixa | Strings típicas de `dbtier` / `effective_tier` |
| ----- | ---------------------------------------------- |
| Community | `community`, `oss`, `open_core` |
| Std (Boar-Std — não é Standard Edition de banco Oracle) | `std`, `standard`, `boar_std`, `boar-std` |
| Pro | `pro`, `professional`, `consultant`; **`trial` mapeia aqui** |
| Pro+ | `pro_plus`, `pro+`, `proplus` |
| Enterprise | `enterprise`, `ent` |
| Partner / SKU white-label | `partner`, `partner_custom`, `whitelabel`, `white_label` → enum **`partner`** |
| Open (lab) | vazio / modo open — não é SKU pago |

Strings desconhecidas fecham em **Community** no mapeamento.

## Grupos de capacidade

A célula é **Sim** quando o enum da faixa é **≥** o mínimo da chave em `_TIER_ORDER`. **Std** **não** tem chaves extras (mesmo conjunto Community; direito comercial é licença/claims). **Partner** está **acima de Enterprise** nessa ordem, então um token Partner hoje recebe **todas** as chaves mapeadas (incluindo Enterprise). White-label é **alias de Partner**, não um sétimo enum.

| Grupo de capacidade | Community | Std | Pro | Pro+ | Ent | Partner / WL |
| ------------------- | :-------: | :-: | :-: | :--: | :-: | :----------: |
| Filesystem; SQL/NoSQL self-hosted; REST/API genérico; detectores centrais; compactados; content-type; teste sintético; XLSX/HTML; API REST; dashBOARd; Docker/Ansible | Sim | Sim | Sim | Sim | Sim | Sim |
| OCR; PDF; nota de conformidade; scans agendados; RBAC do dashboard; UI de API key; POC de maturidade; notificações; SBOM; integridade de build; sink SQL; governance lens Pro; conectores gerenciados/corporativos | — | — | Sim | Sim | Sim | Sim |
| `pro_prefilter_accel`; `rust_regex_stage` | — | — | — | Sim | Sim | Sim |
| Branding de PDF; UI de scheduler Ent; governance lens Ent; multi-tenant; **SSO SAML**; assinatura digital de PDF; PDF por e-mail agendado; comparação histórica; export de audit log; detectores customizados; VCS; interface plugin/parceiro; driver de provedor; plugin/manifesto de remediação | — | — | — | — | Sim | Sim |

**Fora do `FEATURE_TIER_MAP`:** chave de relatório JSONL; SSO OIDC/LDAP (intenção em SUBSCRIPTION_TIERS); SLA de suporte dedicado.

## Franquias de quantidade (avaliação vs o que já embarcou)

Claims de quantidade já embarcados (não são preço): workers Community **2** · Pro **4** · Pro+ **8** (claim) · Enterprise **ilimitado** no entitlement; Pro padrão **2** sites de produção licenciados — ver [SUBSCRIPTION_TIERS.pt_BR.md](SUBSCRIPTION_TIERS.pt_BR.md). `dbmax_targets` continua claim planejado.

**Franquias de volume / data estate** (cota-base + packs, true-up em vez de kill switch) estão sendo **precificadas em privado**. Docs públicos não listam valores nem SKUs de pack até produto+jurídico congelarem. Inventariar o **tamanho** do estate pode ser feature de produto sem ser fatura.

## Catalyst / Supporter (avaliação)

**Catalyst** e **Supporter** são **nomes de programa comercial em avaliação**. **Não** são valores em `map_dbtier_string_to_tier` hoje. Não trate como faixas extras do `FEATURE_TIER_MAP` até emissão e docs mudarem juntos.

## Contato

**contact@databoar.com.br** ou uma issue no GitHub. Esta página não é orçamento.

## Drift

Quando `FEATURE_TIER_MAP`, `_TIER_ORDER` ou `map_dbtier_string_to_tier` mudarem, atualize esta página no mesmo PR.
