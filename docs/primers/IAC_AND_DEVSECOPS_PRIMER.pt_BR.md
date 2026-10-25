# Primer: Infrastructure as Code e DevSecOps (contexto de deploy do Boar)

**English:** [IAC_AND_DEVSECOPS_PRIMER.md](IAC_AND_DEVSECOPS_PRIMER.md)

Este primer é para **integradores e novos mantenedores** que precisam de vocabulário comum sobre
**Infrastructure as Code (IaC)** e sobre como as **verificações de segurança** aparecem neste
repositório. É onboarding conceitual — não é runbook. Comandos passo a passo ficam nos READMEs de
deploy listados no final.

**Relacionado:** [docs/hubs/INDEX.md](../hubs/INDEX.md) · [GLOSSARY.pt_BR.md](../GLOSSARY.pt_BR.md) · [índice local de primers](INDEX.pt_BR.md)

---

## 1. IaC em resumo

**Infrastructure as Code** significa descrever hosts, redes, containers e recursos correlatos em
**arquivos versionados**, em vez de depender só de comandos digitados uma vez no servidor.

Duas ideias costumam se misturar:

| Ideia | Classe de ferramenta típica | O que otimiza |
| ----- | --------------------------- | ------------- |
| **Provisionamento** | OpenTofu, Terraform, APIs de nuvem | *Criar ou alterar* recursos (VMs, DNS, containers, firewall) com **plan → apply** e **estado** registrado |
| **Gerenciamento de configuração** | Ansible, Salt, Chef | *Convergir* uma máquina já existente para um formato declarado (pacotes, serviços, arquivos) com execuções **idempotentes** |

**Idempotência:** rodar a mesma automação de novo deve deixar o sistema no estado desejado, sem
efeitos colaterais duplicados.

**Drift:** o ambiente real deixa de corresponder ao que o código declara. Drift é detectado
comparando a realidade à intenção declarada (e, no OpenTofu/Terraform, ao **state**).

**Plan / apply:** OpenTofu (e ferramentas compatíveis com Terraform) mostram um **plan** de mudanças
pendentes; o operador aceita antes do **apply**. Ansible usa **`--check`** (dry-run) nos playbooks
para um passe “o que mudaria?” antes de aplicar.

Este repositório **não** inclui bloco **backend** remoto do OpenTofu: o estado de
`deploy/opentofu/` fica **local** na máquina onde você roda `tofu apply` (veja
`deploy/opentofu/versions.tf` — providers fixados, sem `backend { … }`).

---

## 2. Os caminhos de deploy do Boar (o que está na árvore)

A automação de deploy do produto em **`deploy/`** separa **provisionamento de infraestrutura** e
**deploy da aplicação**, conforme
[ADR-0016](../adr/ADR-0016-opentofu-corporate-iac-path-alongside-ansible.md). O **gerenciamento de
configuração** para instalações é **Ansible-first** para estado de host reproduzível, alinhado ao
[ADR-0009](../adr/ADR-0009-ansible-idempotent-roles-as-single-automation-source.md) (roles
idempotentes como fonte de automação — no repositório isso vale para baselines de lab em
`ops/automation/ansible/` e para roles de produto em `deploy/ansible/`).

### 2.1 Ansible — `deploy/ansible/`

| Artefato | Papel |
| -------- | ----- |
| [`site.yml`](../../deploy/ansible/site.yml) | **Caminho A:** Data Boar standalone via Docker Compose (`swarm_enabled: false`), role `data_boar` |
| [`site-full.yml`](../../deploy/ansible/site-full.yml) | **Caminho B:** Docker CE + init Swarm, depois serviço Swarm — roles `docker`, depois `data_boar` |
| [`site-poc-db.yml`](../../deploy/ansible/site-poc-db.yml) | Stack de banco POC — role `poc_database` (dados sintéticos de lab; ver vars do playbook) |
| [`roles/data_boar/`](../../deploy/ansible/roles/data_boar/) | Pull de imagem, deploy compose/stack, portas, caminhos no host |
| [`roles/docker/`](../../deploy/ansible/roles/docker/) | Instalação Docker CE e Swarm no Caminho B |
| [`roles/poc_database/`](../../deploy/ansible/roles/poc_database/) | Container de banco POC opcional + caminho de seed |
| [`group_vars/all.yml`](../../deploy/ansible/group_vars/all.yml) | Defaults compartilhados (imagem, porta `8088`, diretório de instalação, env apt-listbugs) |
| [`inventory/hosts.ini.example`](../../deploy/ansible/inventory/hosts.ini.example) | Inventário de exemplo — copiar para `hosts.ini` localmente |
| [`ansible.cfg`](../../deploy/ansible/ansible.cfg) | Comportamento Ansible desta árvore |
| [`README.md`](../../deploy/ansible/README.md) (+ [pt-BR](../../deploy/ansible/README.pt_BR.md)) | Entrada do operador: pré-requisitos, Caminhos A/B, POC DB |

Os playbooks definem `environment: "{{ labop_debian_unattended_apt_environment }}"` para que
`apt-listbugs` não aborte installs não assistidos no Debian/Ubuntu — CI em
`tests/test_ansible_playbooks_unattended_apt.py` (ver README de deploy).

**Fluxo corporativo em dois passos** (documentado nos READMEs de deploy): OpenTofu pode gerar
`generated_inventory.ini`; Ansible roda `site.yml` contra esse inventário.

### 2.2 OpenTofu — `deploy/opentofu/`

| Arquivo | Papel |
| ------- | ----- |
| [`main.tf`](../../deploy/opentofu/main.tf) | Pull de imagem Docker, `docker_container` do Data Boar, Postgres POC opcional, healthcheck |
| [`variables.tf`](../../deploy/opentofu/variables.tf) | Entradas (imagem, porta, caminhos no host, `db_enabled`, `db_password` com `sensitive`) |
| [`outputs.tf`](../../deploy/opentofu/outputs.tf) | Endpoints e caminho do inventário Ansible gerado |
| [`versions.tf`](../../deploy/opentofu/versions.tf) | `required_version >= 1.6.0`; fixa providers `kreuzwerker/docker` e `hashicorp/local` |
| [`README.md`](../../deploy/opentofu/README.md) (+ [pt-BR](../../deploy/opentofu/README.pt_BR.md)) | `tofu init` / `plan` / `apply` e repasse ao Ansible |

O OpenTofu aqui usa o **provider Docker** em um host que já executa Docker; não substitui o
Ansible para instalação de pacotes ou YAML de aplicação no host.

---

## 3. Sinais de DevSecOps *neste* repositório

O que existe **nos arquivos versionados hoje**, com ponteiros verificáveis. O que **não** está
listado **não** é afirmado.

| Prática | Onde aparece no repositório |
| ------- | --------------------------- |
| **SAST Python (Bandit)** | `[tool.bandit]` em `pyproject.toml`; job **Bandit (strict)** em `.github/workflows/ci.yml`; tier padrão em `scripts/check-all-security-scans.sh` |
| **Semgrep** | Workflow `.github/workflows/semgrep.yml`; **`check-all.sh --enforced`** opcional (`scripts/check-all-security-scans.sh`) |
| **CodeQL** | Workflow `.github/workflows/codeql.yml` |
| **Varredura de segredos (Gitleaks)** | `security/gitleaks.toml`, workflow `.github/workflows/gitleaks.yml`, `scripts/run-gitleaks-strict.sh`; pre-commit / `check-all`; CI com binário **fixado** (SHA256 em `ci.yml`) |
| **Análise estática de workflows (Zizmor)** | Workflow `.github/workflows/zizmor.yml`; `scripts/check-all-security-scans.sh` com `uvx zizmor` em `.github/workflows/` |
| **Geração de SBOM** | Workflow `.github/workflows/sbom.yml`; roteiro em [ADR-0003](../adr/ADR-0003-sbom-roadmap-cyclonedx-then-syft.md) |
| **Scan de dependências / OSV** | `scripts/run-osv-scanner.sh`; tier **`check-all --enforced`** |
| **Lint de shell** | `shellcheck --severity=error` em `scripts/check-all.sh` / `check-all.ps1` e passo **Shellcheck (severity=error)** em `ci.yml` |
| **Tripwire de gates (PII / arquivos de gate)** | `scripts/gate_change_tripwire.py` no início de `check-all.sh`; conjunto protegido no script e em `.github/CODEOWNERS` |
| **Commits assinados / atestação** | Política em `CONTRIBUTING.md` e inventário ADR ([ADR-0056](../adr/ADR-0056-cryptographic-adr-inventory-inv-adr-ssh-attestation.md)); workflow `.github/workflows/operator-gated-pr-guard.yml` |

**Não está neste repositório (dizer com clareza):**

- Nenhum workflow de **scanner de IaC dedicado** (ex.: Checkov, tfsec) na automação versionada.
- Nenhum **backend remoto** OpenTofu/Terraform em `deploy/opentofu/`.
- **Bats** para helpers shell é passo **opcional local** em `check-all.sh`, não job de CI (bloco `#1926` em `scripts/check-all.sh`).

---

## 4. Segurança da própria automação

O que as árvores **deploy** mostram:

- **Segredos no Ansible:** defaults em `group_vars/all.yml` e `defaults/` das roles usam nomes de
  imagem e caminhos públicos — sem senhas de vault commitadas. Inventário real e overrides ficam em
  `inventory/hosts.ini` (a partir do exemplo) ou `-e`, fora do git.
- **Segredos no OpenTofu:** `db_password` é variável `sensitive`; exemplos do README usam `-var` na
  CLI para senhas POC — não commitar tfvars com segredos de produção.
- **Fixação de providers:** `deploy/opentofu/versions.tf` fixa versões; Ansible exige
  `community.docker` conforme README de deploy.
- **Responsabilidade do operador:** exposição da porta `8088`, acesso ao socket Docker, TLS na
  frente da app e classificação dos arquivos de config montados nos containers ficam **fora** do
  que estes módulos impõem — ver [DEPLOY.md](../deploy/DEPLOY.md) e docs de hardening do dashboard.

---

## 5. Onde ir depois

| Necessidade | Comece aqui |
| ----------- | ----------- |
| Caminhos Ansible A/B e POC DB | [`deploy/ansible/README.md`](../../deploy/ansible/README.md) |
| Módulo OpenTofu e fluxo em dois passos | [`deploy/opentofu/README.md`](../../deploy/opentofu/README.md) |
| Por que Ansible é fonte de CM | [ADR-0009](../adr/ADR-0009-ansible-idempotent-roles-as-single-automation-source.md) |
| Por que OpenTofu fica ao lado do Ansible | [ADR-0016](../adr/ADR-0016-opentofu-corporate-iac-path-alongside-ansible.md) |
| Taxonomia e registro de primers | [ADR-0070](../adr/ADR-0070-primer-taxonomy-and-home.md), [ADR-0058](../adr/ADR-0058-primer-hub-registration-ritual.md) |
| Índice completo de ADRs | [`docs/adr/README.md`](../adr/README.md) |
| Mapa de hubs de documentação | [`docs/hubs/INDEX.md`](../hubs/INDEX.md) |

---

*Governança:* primers técnicos ficam em `docs/primers/` conforme [ADR-0070](../adr/ADR-0070-primer-taxonomy-and-home.md).
