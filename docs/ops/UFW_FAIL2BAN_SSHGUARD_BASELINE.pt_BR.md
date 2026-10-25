# Baseline UFW + Fail2ban + sshguard (LAB-OP friendly)

**English:** [UFW_FAIL2BAN_SSHGUARD_BASELINE.md](UFW_FAIL2BAN_SSHGUARD_BASELINE.md)

## Objetivo

Proteger o acesso remoto mantendo a operação segura no LAB-OP.

## O que aprendemos com hosts existentes do LAB-OP

- Um **host secundário de lab** usa `fail2ban` com uma lista explícita de LAN em `ignoreip` (ex.: `192.0.2.0/24` — só documentação; CIDRs reais em notas privadas).
- `sshguard` está habilitado e usa `/etc/sshguard/whitelist`.
- Alguns hosts não são Debian-family; podem usar `nftables` diretamente (sem `ufw`).

## Automação

- UFW baseline: `ops/automation/ansible/roles/lab_node_01_ufw`
- Fail2ban baseline: `ops/automation/ansible/roles/lab_node_01_fail2ban`
- sshguard baseline: `ops/automation/ansible/roles/lab_node_01_sshguard`

## Botões opt-in

- **Fail2ban ignore list**: definir `lab_node_01_fail2ban_ignoreip` no inventory.
- **sshguard whitelist**: definir `lab_node_01_sshguard_whitelist_lines` no inventory.

