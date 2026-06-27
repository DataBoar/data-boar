# Data Boar — Ansible Deployment

Two automation paths for deploying Data Boar on any Debian/Ubuntu host.
Pick the path that matches your infrastructure.

All plays set **`environment: "{{ labop_debian_unattended_apt_environment }}"`** (from **`group_vars/all.yml`**) so **`apt-listbugs`** does not abort unattended `apt` installs on Debian/Ubuntu. New playbooks must keep this pattern; CI enforces it — see **`tests/test_ansible_playbooks_unattended_apt.py`** and **[ops/automation/ansible/README.md](../../ops/automation/ansible/README.md)**.

---

## Prerequisites (both paths)

```bash
# Install Ansible (on your control machine, not the target)
sudo apt install ansible          # Debian/Ubuntu
# or: pip install ansible

# Install community.docker collection
ansible-galaxy collection install community.docker

# Clone the Data Boar repository
git clone https://github.com/FabioLeitao/data-boar.git
cd data-boar/deploy/ansible

# Create your inventory
cp inventory/hosts.ini.example inventory/hosts.ini
# Edit hosts.ini: add your server IP and SSH user

```

---

## Path A — Simple: pull image + Docker Compose (no Swarm)

Best for: single server, quick evaluation, existing Docker installs.

```bash
# Dry-run (show what would change, nothing applied)
ansible-playbook site.yml --check

# Apply
ansible-playbook site.yml

```

Data Boar will be reachable at `http://<your-server>:8088` after the playbook completes.

---

## Path B — Full stack: Docker CE + Swarm + ctop + Data Boar service

Best for: fresh servers, reproducible lab environments, multi-node Swarm (extend the
inventory with additional hosts in the [data_boar] group).

```bash
# Dry-run
ansible-playbook site-full.yml --check

# Apply
ansible-playbook site-full.yml

```

This playbook:
1. Installs Docker CE (from the official Docker repository)
2. Initialises a single-node Docker Swarm (`docker swarm init`)
3. Installs `ctop` for real-time container monitoring
4. Pulls the Data Boar image and deploys it as a Swarm service

After apply:

```bash
# Monitor containers on the target
ssh user@your-server ctop

# Check Swarm service status
ssh user@your-server docker service ps data_boar

```

---

## Variables

Override any default in `group_vars/all.yml` or pass via `-e`:

| Variable | Default | Description |
|---|---|---|
| `data_boar_image` | `fabioleitao/data_boar:latest` | Docker image to pull |
| `data_boar_port` | `8088` | Host port for the API |
| `data_boar_dir` | `/opt/data_boar` | Working directory on target |
| `swarm_enabled` | `false` | Set `true` for Path B / Swarm |

Example override:

```bash
ansible-playbook site.yml -e "data_boar_port=9000"

```

---

## Verification

```bash
# Health check (from your control machine)
curl http://<server>:8088/health

# View logs on the target
ssh user@your-server docker logs -f data_boar

```

---

## Related documentation

- `deploy/docker-compose.yml` — base compose definition
- `docs/USAGE.md` — CLI and configuration reference
- `docs/TECH_GUIDE.md` — architecture overview
- `docs/deploy/DEPLOY.md` — Docker and manual deployment alternatives
