# Baseline de swap com zram (LAB-OP friendly)

**English:** [ZRAM_SWAP_BASELINE.md](ZRAM_SWAP_BASELINE.md)

## Objetivo

Melhorar a responsividade em hosts com pouca RAM sem depender de um swap grande em disco.

## Automação (Ansible)

Role: `ops/automation/ansible/roles/lab_node_01_zram`

O padrão é **opt-in** (`lab_node_01_zram_enable=false`).

### Política de sizing

A role calcula `zram-size` com base na RAM do host:

- `lab_node_01_zram_size_percent` da RAM total
- limitado por `lab_node_01_zram_min_mb` e `lab_node_01_zram_max_mb`

## Validação

No host:

```bash
swapon --show
zramctl
```

