# Baseline do `default.prf` do Lynis (LAB-OP friendly)

**English:** [LYNIS_DEFAULT_PRF_BASELINE.md](LYNIS_DEFAULT_PRF_BASELINE.md)

## Objetivo

Manter as execuções do Lynis **acionáveis**: reduzir ruído recorrente **sem** mascarar achados reais.

## Política

- Prefira corrigir a causa raiz (pacote/serviço/config) em vez de pular testes.
- Quando for realmente necessário pular, mantenha “skips” como **opt-in** e documentados (por quê + escopo).
- Docs versionadas ficam genéricas (sem hostnames, IPs, segredos). Exceções por host ficam em `docs/private/homelab/`.

## Automação

O baseline Ansible escreve um `/etc/lynis/default.prf` revisável com sugestões **apenas em comentário**:

- Role: `ops/automation/ansible/roles/lab_node_01_lynis`
- Template: `ops/automation/ansible/roles/lab_node_01_lynis/templates/default.prf.j2`

## Como usar

1. Rode o Lynis normalmente (`sudo lynis audit system`).
2. Se um achado for falso positivo ou “não se aplica”, **comente** antes.
3. Só depois de confirmar que é seguro e apropriado, **descomente** a linha `skip-test=...` relevante.

