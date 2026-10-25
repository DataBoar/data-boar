## `snmpd` v3-only (baseline opt-in)

**Objetivo:** permitir observabilidade por SNMP **sem** v1/v2c. Este baseline é **opt-in** porque `snmpd` é serviço de rede.

### Política (tracked vs private)

- Não armazenar senhas/credenciais SNMP em arquivos trackeados.
- Coloque usuários v3 e secrets em inventário **privado** (gitignored) ou em Vault local.

### Ansible (LAB-NODE-01)

O role `lab_node_01_snmpd_v3_only` é **desligado por padrão**:

- `lab_node_01_snmpd_install=false`
- `lab_node_01_snmpd_enable=false`

Para instalar + habilitar (exemplo):

```bash
cd ops/automation/ansible
ANSIBLE_ROLES_PATH=./roles ansible-playbook -i inventory.local.ini playbooks/lab-node-01-baseline.yml --diff \
  -e lab_node_01_snmpd_install=true \
  -e lab_node_01_snmpd_enable=true \
  -e lab_node_01_snmpd_agent_address="udp:127.0.0.1:161"
```

> Nota: manter `agentAddress` em loopback é um bom primeiro passo (para testes locais). Para expor na LAN, defina um IP/interface específicos e valide firewall/VLAN.

### Validação (no host)

```bash
sudo systemctl status snmpd --no-pager
ss -lunp | grep ':161' || true
```

