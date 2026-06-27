# Data Boar — módulo OpenTofu

**English:** [README.md](README.md)

Implante a infraestrutura do Data Boar com [OpenTofu](https://opentofu.org/) (fork open source do Terraform).

Este módulo provisiona a **camada de infraestrutura** (runtime de contêiner, portas, volumes). Para
**configuração da aplicação** (alvos de varredura, credenciais de banco, agendamento), use os playbooks
Ansible em `deploy/ansible/` como segundo passo.

---

## Quem deve usar

Use este módulo quando a equipe já gerencia infraestrutura via OpenTofu ou Terraform 1.5.x.
Se você quer uma implantação mais simples em um comando, sem fluxo IaC existente, veja
`deploy/ansible/README.md` ([pt-BR](../ansible/README.pt_BR.md)) (Caminhos A e B).

---

## Pré-requisitos

- **OpenTofu >= 1.6** ou **Terraform >= 1.5** instalado.
- **Docker** em execução no host alvo.
- Um `config.yaml` do Data Boar já no disco no caminho que você passará via `data_boar_config_path`.
- Um diretório de saída de relatórios criado no host.

Instale o OpenTofu: <https://opentofu.org/docs/intro/install/>

---

## Início rápido

```bash
# 1. Entre neste diretório
cd deploy/opentofu

# 2. Inicialize os providers
tofu init

# 3. Pré-visualize o que será criado
tofu plan

# 4. Aplique (implanta o contêiner no daemon Docker local)
tofu apply

# 5. Abra o Data Boar
open http://localhost:8088
```

---

## Fluxo corporativo em dois passos (OpenTofu + Ansible)

O OpenTofu provisiona a infraestrutura; o Ansible configura a aplicação.

```bash
# Passo 1: provisionar infra
cd deploy/opentofu
tofu apply

# Passo 2: configurar e implantar o app
#   O OpenTofu gerou um generated_inventory.ini para você:
cd ../..
ansible-playbook -i deploy/opentofu/generated_inventory.ini deploy/ansible/site.yml
```

---

## Com banco POC (PostgreSQL)

Para subir um contêiner PostgreSQL local junto ao Data Boar para testes POC:

```bash
tofu apply -var="db_enabled=true" -var="db_password=poc-test-123"
```

Depois popule o banco com PII sintética:

```bash
uv run python scripts/populate_poc_database.py \
  --db-type postgres \
  --host localhost \
  --port 5432 \
  --write-config
```

---

## Variáveis

| Nome | Padrão | Descrição |
|---|---|---|
| `data_boar_image` | `fabioleitao/data-boar:latest` | Imagem Docker para pull |
| `data_boar_port` | `8088` | Porta no host para a interface web |
| `data_boar_config_path` | `/etc/data-boar/config.yaml` | Caminho do config.yaml no host |
| `data_boar_output_dir` | `/var/data-boar/reports` | Diretório de saída de relatórios no host |
| `container_name` | `data-boar` | Nome do contêiner Docker |
| `restart_policy` | `unless-stopped` | Política de reinício do Docker |
| `db_enabled` | `false` | Subir banco PostgreSQL POC local |
| `db_password` | `""` (sensível) | Senha do banco PostgreSQL POC |

---

## Outputs

| Output | Descrição |
|---|---|
| `data_boar_url` | URL da interface web do Data Boar |
| `data_boar_port` | Porta no host à qual o contêiner está vinculado |
| `container_name` | Nome do contêiner em execução |
| `ansible_inventory_path` | Caminho do inventário Ansible gerado |
| `poc_db_host` | Host PostgreSQL (quando `db_enabled = true`) |
| `poc_db_port` | Porta PostgreSQL (quando `db_enabled = true`) |

---

## Provedores cloud / remotos

O módulo padrão usa o provider Docker (daemon local). Para apontar a um host remoto ou a um provedor
cloud, substitua a configuração do provider em um arquivo `provider_override.tf` no seu diretório
de trabalho. Exemplos:

**AWS ECS:**

```hcl
# Substitua docker_container por aws_ecs_service / aws_ecs_task_definition
# e use o provider aws da hashicorp/aws
```

**Docker remoto via SSH:**

```hcl
provider "docker" {
  host     = "ssh://<ssh-user>@myserver.example.com"
  ssh_opts = ["-i", "~/.ssh/id_ed25519"]
}
```

---

## Backend de state (recomendado para uso corporativo)

Armazene o state remotamente para a equipe compartilhar a mesma visão de infraestrutura:

```hcl
# backend.tf (crie em deploy/opentofu/ antes de tofu init)
terraform {
  backend "s3" {
    bucket = "my-company-tf-state"
    key    = "data-boar/terraform.tfstate"
    region = "us-east-1"
  }
}
```

Backends compatíveis: S3, GCS, Azure Blob, MinIO (S3-compatível self-hosted).

---

## Compatibilidade

Este módulo usa apenas recursos HCL compatíveis com **OpenTofu >= 1.6** e **Terraform >= 1.5**.
Se a equipe já migrou para OpenTofu, use `tofu`; se ainda estiver no Terraform BSL, os comandos
`terraform` funcionam de forma idêntica.

---

## Relacionados

- `deploy/ansible/README.md` ([pt-BR](../ansible/README.pt_BR.md)) — playbooks Ansible Caminho A (Docker Compose) e Caminho B (stack completa)
- `deploy/kubernetes/` — manifestos Kubernetes
- `docs/adr/ADR-0016-opentofu-corporate-iac-path-alongside-ansible.md` — racional de design
- `docs/USAGE.md` — documentação completa de implantação
