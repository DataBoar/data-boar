# USBGuard rules baseline (LAB-OP friendly)

**pt-BR:** [USBGuard_RULES_BASELINE.pt_BR.md](USBGuard_RULES_BASELINE.pt_BR.md)

## Goal

Make USB device control repeatable without retyping allowlists on each host.

## Policy

- Prefer generating the policy **on the host** (`usbguard generate-policy`) and reviewing it.
- Keep tracked automation **generic** (no real device IDs/hashes).
- Store real allowlists as private overlays under `docs/private/homelab/`.

## Automation

The Ansible baseline writes a comment-only starter file:

- Role: `ops/automation/ansible/roles/lab_node_01_usbguard`
- Template: `ops/automation/ansible/roles/lab_node_01_usbguard/templates/rules.conf.j2`

## How to adopt (recommended)

1. On the host, run:
   - `sudo usbguard generate-policy > /etc/usbguard/rules.conf`
2. Review the file (remove transient devices you don't want trusted).
3. Enable the service:
   - `sudo systemctl enable --now usbguard`

