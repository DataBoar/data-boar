# Baseline de regras do USBGuard (LAB-OP friendly)

**English:** [USBGuard_RULES_BASELINE.md](USBGuard_RULES_BASELINE.md)

## Objetivo

Tornar o controle de dispositivos USB repetível sem recriar allowlists em cada host.

## Política

- Prefira gerar a política **no próprio host** (`usbguard generate-policy`) e revisar.
- Automação versionada fica **genérica** (sem IDs/hashes reais de dispositivos).
- Allowlists reais ficam como overlays privados em `docs/private/homelab/`.

## Automação

O baseline Ansible escreve um arquivo inicial só com comentários:

- Role: `ops/automation/ansible/roles/lab_node_01_usbguard`
- Template: `ops/automation/ansible/roles/lab_node_01_usbguard/templates/rules.conf.j2`

## Como adotar (recomendado)

1. No host, rode:
   - `sudo usbguard generate-policy > /etc/usbguard/rules.conf`
2. Revise o arquivo (remova dispositivos transitórios que você não quer “confiar”).
3. Habilite o serviço:
   - `sudo systemctl enable --now usbguard`

