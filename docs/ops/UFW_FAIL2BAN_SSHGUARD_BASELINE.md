# UFW + Fail2ban + sshguard baseline (LAB-OP friendly)

**pt-BR:** [UFW_FAIL2BAN_SSHGUARD_BASELINE.pt_BR.md](UFW_FAIL2BAN_SSHGUARD_BASELINE.pt_BR.md)

## Goal

Keep remote access protected while staying operational for LAB-OP.

## What we learned from existing LAB-OP hosts

- A **secondary lab host** uses `fail2ban` with an explicit LAN ignore list (example: `192.0.2.0/24` — documentation only; real CIDRs belong in private notes).
- `sshguard` is enabled and uses `/etc/sshguard/whitelist`.
- Some hosts are not Debian-family; they may use `nftables` directly (not `ufw`).

## Automation

- UFW baseline: `ops/automation/ansible/roles/lab_node_01_ufw`
- Fail2ban baseline: `ops/automation/ansible/roles/lab_node_01_fail2ban`
- sshguard baseline: `ops/automation/ansible/roles/lab_node_01_sshguard`

## Opt-in knobs

- **Fail2ban ignore list**: set `lab_node_01_fail2ban_ignoreip` in inventory.
- **sshguard whitelist**: set `lab_node_01_sshguard_whitelist_lines` in inventory.

