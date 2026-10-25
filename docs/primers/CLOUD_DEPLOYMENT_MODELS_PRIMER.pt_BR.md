# Primer: Modelos de deploy em nuvem (e como o Data Boar entrega hoje)

**English:** [CLOUD_DEPLOYMENT_MODELS_PRIMER.md](CLOUD_DEPLOYMENT_MODELS_PRIMER.md)

Primer conceitual para integradores que comparam **onde** o software roda (metal próprio, VM, containers ou APIs de nuvem). Mapeia vocabulário para **o que este repositório versiona** em `deploy/` — não é guia comercial de hyperscaler.

**Relacionado:** [IAC_AND_DEVSECOPS_PRIMER.pt_BR.md](IAC_AND_DEVSECOPS_PRIMER.pt_BR.md) · [docs/deploy/DEPLOY.md](../deploy/DEPLOY.md) · [índice local](INDEX.pt_BR.md)

---

## 1. Modelos em uma tabela

| Modelo | Ideia | Artefatos típicos |
| ------ | ----- | ----------------- |
| **Bare metal / VM** | SO sob seu controle; pacotes no host | Playbooks Ansible, systemd, firewall no host |
| **Container no host** | App em imagem; host com engine de containers | `docker pull`, `docker compose`, serviço Swarm |
| **Provisionamento IaC** | Infra declarada; plan/apply com estado | Módulos OpenTofu/Terraform (aqui: provider Docker em engine existente) |
| **Multicloud** | Mesmos padrões repetidos por provedor/conta | Não há um módulo único multicloud versionado — o operador compõe por site |

**Multicloud** na prática significa contas, regiões e limites de compliance distintos. A postura **de produto** do Data Boar é **deploy sob controle do cliente** (on-prem, VPC ou laptop de consultoria), conforme [LICENSING_OPEN_CORE_AND_COMMERCIAL.pt_BR.md](../LICENSING_OPEN_CORE_AND_COMMERCIAL.pt_BR.md) — não um control plane SaaS multi-tenant nesta árvore.

---

## 2. O que o Data Boar versiona em `deploy/`

| Caminho | Papel |
| ------- | ----- |
| [`deploy/ansible/`](../deploy/ansible/README.pt_BR.md) | **Caminho A:** Compose no host (`site.yml`). **Caminho B:** Docker CE + Swarm e stack (`site-full.yml`). POC DB opcional (`site-poc-db.yml`). |
| [`deploy/opentofu/`](../deploy/opentofu/README.pt_BR.md) | Pull de imagem, `docker_container`, Postgres POC opcional; pode gerar `generated_inventory.ini` para Ansible |
| [`deploy/docker-compose.yml`](../../deploy/docker-compose.yml) | Compose de referência para execução local/lab (ver [DEPLOY.md](../deploy/DEPLOY.md)) |
| [`Dockerfile`](../../Dockerfile) | Build de imagem para releases `data_boar` |

**Não** há módulo Terraform versionado aqui para rede AWS/GCP/Azure. Instalações “em nuvem” em geral significam **você** fornece a VM ou o host Docker/Kubernetes e roda os caminhos Ansible ou OpenTofu acima.

---

## 3. Limites honestos

- **Não** há endpoint gerenciado “Data Boar Cloud” definido na documentação de deploy rastreada.
- **Não** há backend remoto OpenTofu — o estado fica local salvo se você não adicionar um fora do repo ([`deploy/opentofu/versions.tf`](../../deploy/opentofu/versions.tf)).
- Conectores podem apontar para exportações **cloud-adjacent** — isso é **configuração de scan**, não scanner SaaS hospedado.

---

## 4. Onde ir depois

| Necessidade | Comece aqui |
| ----------- | ----------- |
| Caminhos Ansible A/B | [`deploy/ansible/README.pt_BR.md`](../../deploy/ansible/README.pt_BR.md) |
| Fluxo em dois passos OpenTofu | [`deploy/opentofu/README.pt_BR.md`](../../deploy/opentofu/README.pt_BR.md) |
| Vocabulário IaC + DevSecOps | [IAC_AND_DEVSECOPS_PRIMER.pt_BR.md](IAC_AND_DEVSECOPS_PRIMER.pt_BR.md) |
| Licenciamento / contagem de deploy | [LICENSING_SPEC.pt_BR.md](../LICENSING_SPEC.pt_BR.md) (`dbmax_deployments`) |
