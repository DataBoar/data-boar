# Homelab host report (extended) — hardening + inventory signals

**pt-BR:** [HOMELAB_HOST_REPORT_EXTENDED.pt_BR.md](HOMELAB_HOST_REPORT_EXTENDED.pt_BR.md)

## Goal

Capture a **high-signal** snapshot of each LAB-OP host (packages + security posture) in a way that is:

- repeatable,
- reviewable,
- safe to share in **redacted** form,
- and works across different Linux distros (Debian-family + Void + others).

This complements the package-focused page: [HOMELAB_HOST_PACKAGE_INVENTORY.md](HOMELAB_HOST_PACKAGE_INVENTORY.md).

## What is captured (high level)

The script `scripts/homelab-host-report.sh` runs **on the host** and attempts:

- OS/kernel + CPU/memory
- Python/uv/pip (runtime prerequisites)
- Docker presence + basic info (if installed)
- Banners: `/etc/issue`, `/etc/issue.net`, `/etc/banner.net`
- OpenSSH effective config subset (`sshd -T` when available)
- Firewall posture:
  - `ufw status` when UFW exists (Debian/Ubuntu/LMDE)
  - `nft list ruleset` head when `nft` exists (e.g. Void Linux)
- fail2ban, sshguard (status + minimal config signals)
- usbguard (rules/devices when available)
- auditd rules and AIDE config head (when available)
- Kernel + tuning signals (to validate performance/safety posture without surprises):
  - `/proc/cmdline` (boot params)
  - selected `sysctl` values (when `sysctl` exists)
  - `sysctl` config files head (`/etc/sysctl.conf`, `/etc/sysctl.d/*.conf`)
  - `ulimit -a` + `/etc/security/limits*`
  - block device queue hints (`scheduler`, `rotational`, `nr_requests`, etc.)
  - `/etc/udev/rules.d/*.rules` head

The script uses **best-effort** collection and will skip sections that are not installed.

## Recommended profiles by machine class (operator-driven; variable-controlled)

The intent is to keep automation **decidable by variables** so a new host does not get surprise tunings.

These are **recommendations** based on recent LAB-OP reports, common Linux best practices, and the host’s likely hardware profile.

### Class: Raspberry Pi 3B (low RAM, SD/eMMC, Debian)

- **I/O scheduler**: prefer `mq-deadline` for `mmcblk*` (stable latency); avoid forcing BFQ on SD unless you’ve tested it.
- **Deep scans**: avoid `--deep` (Lynis quick audit can be too heavy); keep `--privileged` OK.
- **Memory**: prefer **zram swap** (small); swappiness may be higher than desktops (workload-dependent).
- **Note**: if `sysctl` is not present, install `procps` so tuning can be audited consistently.

### Class: <lab-host-2> (Void, x86_64, SATA SSD, “utility box”)

- **I/O scheduler**: BFQ can be OK for SATA SSD when interactive latency matters; don’t apply BFQ to NVMe.
- **Queueing**: consider modern defaults (`net.core.default_qdisc=fq`) if the distro still defaults to `pfifo_fast`.
- **Hardening sysctls** (safe defaults): ensure `fs.protected_fifos=1` and `fs.protected_regular=2` (if kernel supports).

### Class: Primary lab x86_64 (Ubuntu-family desktop/server, SATA SSD, Docker Swarm manager)

- **I/O scheduler**: `mq-deadline` is a safe default for SATA SSD.
- **Networking**: `fq_codel` as default qdisc is a good baseline; avoid aggressive TCP changes unless you measure.
- **Docker host**: avoid “too low” `nofile` limits for services; prefer systemd unit overrides rather than global `limits.conf`.

### Class: Developer workstation (LMDE, NVMe, encrypted BTRFS)

- **I/O scheduler**: prefer `none` for NVMe (kernel default).
- **Memory**: zram is optional (you have 16 GiB); enable only if you have a reason (hibernate isn’t covered by zram).
- **Security vs usability**: keep any tuning minimal unless you have a clear benchmark reason.
- **Note**: if `sysctl` is not present, install `procps` so tuning can be audited consistently.

### Suggested “variable sets” (example)

These are illustrative (not enforced automatically). Use host/group vars to opt in:

```yaml
# ops/automation/ansible/inventory.ini (or group_vars/ / host_vars/)
#
# lab-sbc (example ARM host):
#   lab_node_01_zram_enable: true
#   lab_node_01_zram_max_mb: 512
#
# <lab-host-2>:
#   lab_node_01_zram_enable: true
#   lab_node_01_zram_size_percent: 25
#
# lab-op (primary x86 lab):
#   lab_node_01_install_docker_ce: true
#   lab_node_01_docker_swarm_init: true
#
# lab-workstation (example dev laptop):
#   lab_node_01_zram_enable: false
```

## How to run (on each host)

From the repo root (on the host):

```bash
bash scripts/homelab-host-report.sh
```

To enable best-effort privileged probes using `sudo -n` (non-interactive), pass:

```bash
bash scripts/homelab-host-report.sh --privileged
```

Save output to a file, then redact before sharing:

```bash
bash scripts/homelab-host-report.sh | tee "homelab_host_report_$(date +%F).log"
```

## Privileged block (optional)

Some sections require root for full fidelity (e.g. `sshd -T`, `/etc/audit/rules.d/*.rules`).

The script tries `sudo -n` (non-interactive). If your host requires a password, you can run once:

```bash
sudo -v
bash scripts/homelab-host-report.sh --privileged | tee "homelab_host_report_$(date +%F).log"
```

For a safe-by-default sudoers pattern (restricted to the report command), see:

- [LAB_OP_PRIVILEGED_COLLECTION.md](LAB_OP_PRIVILEGED_COLLECTION.md)

## What to redact

Before sharing logs outside `docs/private/`:

- hostnames / domains
- LAN IPs
- user home paths if they are personally identifying
- any secrets in config files (API keys, tokens)

