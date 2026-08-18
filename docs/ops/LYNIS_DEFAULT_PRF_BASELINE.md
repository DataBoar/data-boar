# Lynis `default.prf` baseline (LAB-OP friendly)

**pt-BR:** [LYNIS_DEFAULT_PRF_BASELINE.pt_BR.md](LYNIS_DEFAULT_PRF_BASELINE.pt_BR.md)

## Goal

Keep Lynis runs **actionable**: reduce repeated noise **without** hiding real findings.

## Policy

- Prefer fixing the root cause (package/service/config) instead of skipping tests.
- When you must skip, keep skips as **opt-in** and documented (why + scope).
- Tracked docs stay generic (no hostnames, IPs, secrets). Host-specific exceptions belong in `docs/private/homelab/`.

## Automation

The Ansible baseline writes a reviewable `/etc/lynis/default.prf` with **comment-only** suggestions:

- Role: `ops/automation/ansible/roles/lab_node_01_lynis`
- Template: `ops/automation/ansible/roles/lab_node_01_lynis/templates/default.prf.j2`

## How to use

1. Run Lynis normally (`sudo lynis audit system`).
2. If a finding is a false positive or “not applicable”, add a **comment** first.
3. Only after you confirm it is safe and appropriate, **uncomment** the relevant `skip-test=...` line.

