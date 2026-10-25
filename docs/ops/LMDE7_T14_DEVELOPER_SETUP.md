# ThinkPad LAB-NODE-01 + LMDE 7 — developer setup (Data Boar)

**Português (Brasil):** Full step-by-step (install from Ventoy through lab-op readiness) — **[LMDE7_LAB-NODE-01_DEVELOPER_SETUP.pt_BR.md](LMDE7_LAB-NODE-01_DEVELOPER_SETUP.pt_BR.md)**. **Use that file as the primary recipe;** this English page is a structured summary and cross-reference.

---

## Install and firmware context (what the pt-BR doc covers in §0)

- **Ventoy:** Keep the USB updated from the official [Ventoy releases](https://github.com/ventoy/Ventoy/releases) (as of late 2025 / early 2026 the line is **1.1.x**, e.g. **v1.1.10** — re-check the releases page on the day you refresh the stick). On UEFI + **Secure Boot** enabled, follow Ventoy’s **Secure Boot** documentation (enrol the Ventoy certificate into **MOK** when prompted — do **not** turn off Secure Boot “just to boot”).
- **“Device Guard”:** That label is **Windows** (virtualization-based security). On **LMDE/Linux**, the parallel goal is **UEFI Secure Boot** (Debian/LMDE signed shim + kernel) **plus** hardening in §3 of the pt-BR doc (`ufw`, `unattended-upgrades`, `AppArmor`, audits).
- **Concrete flow:** §0 in the Portuguese file walks: firmware defaults → boot Ventoy with Secure Boot → optional **F31 fix** if the ISO’s GRUB path is wrong → LMDE installer → after first boot confirm **`mokutil --sb-state`** is still **enabled**.

---

## After the OS boots (baseline)

LMDE 7 is **Debian 13–based**. Align packages with [TECH_GUIDE.md](../TECH_GUIDE.md): Python **3.13** on the host when available (**≥3.12** still supported), plus `build-essential`, `libpq-dev`, `libssl-dev`, `libffi-dev`, `unixodbc-dev`; install **`uv`**; in the repo run **`uv sync`** and **`uv run pytest`**.

Security baseline (details in pt-BR §3): **`ufw`**, **`unattended-upgrades`**, **`fwupd`** for ThinkPad firmware, optional **Lynis** and **`debsecan` / `needrestart`**.

---

## Performance tuning (summary — full commands in pt-BR §3.6 and §6)

- **I/O schedulers / fstab:** NVMe-oriented notes and `noatime` example in §6.2.
- **Kernel:** Prefer **distribution kernels** so signatures stay aligned with **Secure Boot** (§6.3); avoid third-party kernel builds unless you manage signing/MOK.
- **Memory:** Optional **`zram-tools`** for compressed swap (§6.4); otherwise tune **`vm.swappiness`** conservatively (§3.6).

---

## Containers and lab-op

- **Docker CE** (official repo) **+ Compose plugin** are the **default** for this repo’s LAB-NODE-01 baseline: [playbooks/lab-node-01-baseline.yml](../../ops/automation/ansible/playbooks/lab-node-01-baseline.yml) enables **`lab_node_01_install_docker_ce: true`** and the **`lab_node_01_operator_supplementary_groups`** role adds the operator login to the **`docker`** group (log out and back in, or `newgrp docker`, so **`docker compose`** works without `sudo`). **Podman** remains opt-in in the same playbook (`lab_node_01_install_podman: false` by default). See §7 in the pt-BR guide and [ops/automation/ansible/README.md](../../ops/automation/ansible/README.md).
- When the LAB-NODE-01 is a lab host: SSH hardening, **`docs/private/homelab/lab-op-hosts.manifest.json`** from the example manifest, then **`scripts/lab-op-sync-and-collect.ps1`** from the workstation — §6.5. For **`deploy/lab-smoke-stack`**, see [LAB_SMOKE_MULTI_HOST.md](LAB_SMOKE_MULTI_HOST.md) (two Docker hubs: e.g. **lab-node-02 + LAB-NODE-01**; no compose requirement on LAB-NODE-03 / LAB-NODE-04).

---

## Repeatable automation (Ansible + OpenTofu) (summary)

The Portuguese guide now includes an optional section on **repeatability** using:

- **Ansible** for host bootstrap (packages, files, services),
- **OpenTofu** for declarative infrastructure (when a real provider/API exists).

Key guardrails match the rest of the repo:

- Do **not** commit secrets (PATs, tokens, keys); keep sensitive configs under gitignored `docs/private/` or in a separate private automation repo.
- Treat assistant/tool suggestions as **inputs**: run, validate, then standardize.

See **§7.1** in the pt-BR file for a minimal skeleton (inventory/playbook/tofu layout) and a post-run validation checklist.

**Canonical baseline in this repo:** [ops/automation/ansible/README.md](../../ops/automation/ansible/README.md) and [playbooks/lab-node-01-baseline.yml](../../ops/automation/ansible/playbooks/lab-node-01-baseline.yml) (includes `tmux` and Bitwarden CLI via npm). **End-to-end workflow** (close baseline, sudo warm, `bw`, VeraCrypt pointers): [LAB-NODE-01_BASELINE_COMPLETION.md](LAB-NODE-01_BASELINE_COMPLETION.md). **tmux dotfiles** for lab hosts: [OPERATOR_PACKAGE_MAINTENANCE_AND_BW_CLI.md](OPERATOR_PACKAGE_MAINTENANCE_AND_BW_CLI.md) §5.

Role and baseline changes (for example `apt-listbugs` during unattended apt, D-Bus or `systemctl` behavior under Ansible, Snapper on btrfs, keeping the laptop repo in sync with `main`) are documented in the Ansible README **Troubleshooting** section and in `ops/automation/ansible/` — they are **not** duplicated step-by-step in this guide. The minimal `lab-automation` skeleton in pt-BR §7.1 is illustrative only; **`lab-node-01-baseline.yml`** is the source of truth.

---

## Related plans and links

- Observability stack (optional, after baseline): [PLAN_LAB_OP_OBSERVABILITY_STACK.md](../plans/PLAN_LAB_OP_OBSERVABILITY_STACK.md).
- Package inventory: [HOMELAB_HOST_PACKAGE_INVENTORY.md](HOMELAB_HOST_PACKAGE_INVENTORY.md).
- Workstation updates, **Topgrade**, **`gta`**, **Bitwarden CLI** (`bw`): [OPERATOR_PACKAGE_MAINTENANCE_AND_BW_CLI.md](OPERATOR_PACKAGE_MAINTENANCE_AND_BW_CLI.md).

**Last review:** Matches Debian 13 / LMDE 7 and Data Boar `pyproject.toml` (**≥3.12**, **3.13** recommended on the laptop); confirm packages with `apt-cache policy python3.13` (or `python3.12` as fallback).
