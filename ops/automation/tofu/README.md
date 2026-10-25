# OpenTofu (optional) — LAB-OP automation scaffolding

This folder is intentionally minimal. OpenTofu is useful when you have a **provider-backed API** to manage (DNS, IPAM, cloud, secrets managers, etc.).

For a single workstation host, most hardening is better expressed via **Ansible**.

## Policy

- Never commit state files (`*.tfstate`) — see `.gitignore`.
- Keep secrets out of tracked `.tf` files. Use environment variables, CI secrets, or gitignored local files.

## When to use

- You want declarative, drift-detectable management for infrastructure *around* the lab (not the OS config itself).
- Example: a DNS provider, or future self-hosted services with an API.

## When not to use

- To install packages or manage `/etc/*` on the LAB-NODE-01 — use Ansible.

