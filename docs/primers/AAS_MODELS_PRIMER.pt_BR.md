# Primer: SaaS, AIaaS e o modelo de entrega do Data Boar

**English:** [AAS_MODELS_PRIMER.md](AAS_MODELS_PRIMER.md)

**Público:** integradores, revisores de segurança e compradores que comparam rótulos “as a service” com o que de fato roda no ambiente deles.

---

## 1. Vocabulário

| Termo | Significado usual | Data Boar neste repositório público |
| ----- | ----------------- | ----------------------------------- |
| **SaaS** | Fornecedor hospeda o app; tenants compartilham serviço operado | **Não** é o modelo central hoje — você implanta o scanner onde os dados estão |
| **AIaaS** | API de modelo/inferência cobrada por token ou chamada | **Não** é o núcleo — a descoberta é lógica **determinística** de padrões/detector, não LLM hospedado que lê seu corpus |
| **On-prem / VPC do cliente** | Você roda containers ou VMs; dados no seu perímetro | **Sim** — narrativa padrão em [LICENSING_OPEN_CORE_AND_COMMERCIAL.pt_BR.md](../LICENSING_OPEN_CORE_AND_COMMERCIAL.pt_BR.md) e [DEPLOY.md](../deploy/DEPLOY.md) |
| **Managed futuro** | Oferta possível depois | **Só tese** — não afirme SaaS multi-tenant público a partir desta árvore |

---

## 2. Evidência na documentação rastreada

- **Deploy:** Ansible + Docker/OpenTofu em `deploy/` ([IAC_AND_DEVSECOPS_PRIMER.pt_BR.md](IAC_AND_DEVSECOPS_PRIMER.pt_BR.md)); licenças Pro descrevem **footprints de produção limitados** (`dbmax_deployments` em [LICENSING_SPEC.pt_BR.md](../LICENSING_SPEC.pt_BR.md)), não assentos SaaS ilimitados.
- **Postura de IA:** [AI_COMPLIANCE_PRIMER.pt_BR.md](AI_COMPLIANCE_PRIMER.pt_BR.md) — camada de **dados**, sem avaliação de modelo. [GLOSSARY.pt_BR.md](../GLOSSARY.pt_BR.md) separa vocabulário de marketing “IA” do comportamento do detector.
- **OTel opcional:** métricas/traces **opt-in** via `DATA_BOAR_OTEL_ENABLED` (`core/otel_setup.py`) — exportação de telemetria, não AIaaS.

---

## 3. O que não afirmamos

- Não há fluxo versionado “envie seus dados para databoar.com para varrer”.
- Não há precificação por token nem model card neste repositório.
- Alvos de conectores podem incluir **exportações de SaaS** — é **inventário de sistemas de terceiros**, não o Data Boar virando o SaaS desses fornecedores.

---

## 4. Onde ir depois

| Necessidade | Doc |
| ----------- | --- |
| Caminhos de instalação | [DEPLOY.md](../deploy/DEPLOY.md) |
| Tiers / deployments | [LICENSING_OPEN_CORE_AND_COMMERCIAL.pt_BR.md](../LICENSING_OPEN_CORE_AND_COMMERCIAL.pt_BR.md) |
| Primer de IA (só camada de dados) | [AI_COMPLIANCE_PRIMER.pt_BR.md](AI_COMPLIANCE_PRIMER.pt_BR.md) |
