# Data Boar — implantação com Ansible

**English:** [README.md](README.md)

Dois caminhos de automação para implantar o Data Boar em qualquer host Debian/Ubuntu.
Escolha o caminho que combina com a sua infraestrutura.

Todos os plays definem **`environment: "{{ labop_debian_unattended_apt_environment }}"`** (em **`group_vars/all.yml`**) para o **`apt-listbugs`** não abortar instalações `apt` não assistidas em Debian/Ubuntu. Novos playbooks devem manter esse padrão; o CI reforça — veja **`tests/test_ansible_playbooks_unattended_apt.py`** e **[ops/automation/ansible/README.md](../../ops/automation/ansible/README.md)**.

---

## Pré-requisitos (ambos os caminhos)

```bash
# Instale o Ansible (na máquina de controle, não no alvo)
sudo apt install ansible          # Debian/Ubuntu
# ou: pip install ansible

# Instale a collection community.docker
ansible-galaxy collection install community.docker

# Clone o repositório Data Boar
git clone https://github.com/FabioLeitao/data-boar.git
cd data-boar/deploy/ansible

# Crie o inventário
cp inventory/hosts.ini.example inventory/hosts.ini
# Edite hosts.ini: adicione o IP do servidor e o usuário SSH

```

---

## Caminho A — Simples: pull da imagem + Docker Compose (sem Swarm)

Melhor para: servidor único, avaliação rápida, instalações Docker já existentes.

```bash
# Dry-run (mostra o que mudaria, nada é aplicado)
ansible-playbook site.yml --check

# Aplicar
ansible-playbook site.yml

```

O Data Boar ficará acessível em `http://<seu-servidor>:8088` após o playbook concluir.

---

## Caminho B — Stack completa: Docker CE + Swarm + ctop + serviço Data Boar

Melhor para: servidores novos, ambientes de laboratório reproduzíveis, Swarm multi-nó (estenda o
inventário com hosts adicionais no grupo `[data_boar]`).

```bash
# Dry-run
ansible-playbook site-full.yml --check

# Aplicar
ansible-playbook site-full.yml

```

Este playbook:

1. Instala o Docker CE (do repositório oficial do Docker)
2. Inicializa um Docker Swarm de nó único (`docker swarm init`)
3. Instala `ctop` para monitoramento de contêineres em tempo real
4. Faz pull da imagem Data Boar e implanta como serviço Swarm

Após aplicar:

```bash
# Monitore contêineres no alvo
ssh user@your-server ctop

# Verifique o status do serviço Swarm
ssh user@your-server docker service ps data_boar

```

---

## Variáveis

Substitua qualquer padrão em `group_vars/all.yml` ou passe via `-e`:

| Variável | Padrão | Descrição |
|---|---|---|
| `data_boar_image` | `fabioleitao/data_boar:latest` | Imagem Docker para pull |
| `data_boar_port` | `8088` | Porta no host para a API |
| `data_boar_dir` | `/opt/data_boar` | Diretório de trabalho no alvo |
| `swarm_enabled` | `false` | Defina `true` para o Caminho B / Swarm |

Exemplo de substituição:

```bash
ansible-playbook site.yml -e "data_boar_port=9000"

```

---

## Verificação

```bash
# Health check (da máquina de controle)
curl http://<server>:8088/health

# Ver logs no alvo
ssh user@your-server docker logs -f data_boar

```

---

## Documentação relacionada

- `deploy/docker-compose.yml` — definição base do compose
- `docs/USAGE.md` — referência de CLI e configuração
- `docs/TECH_GUIDE.md` — visão geral da arquitetura
- `docs/deploy/DEPLOY.md` — alternativas de implantação Docker e manual
