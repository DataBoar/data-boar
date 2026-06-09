# LAB-OP privileged collection (safe-by-default)

**pt-BR:** [LAB_OP_PRIVILEGED_COLLECTION.pt_BR.md](LAB_OP_PRIVILEGED_COLLECTION.pt_BR.md)

## Goal

Enable **operator-controlled**, **guardrailed** privileged collection for LAB-OP inventory and hardening readiness — without normalizing broad `NOPASSWD` sudo.

## How it works

The host report script supports opt-in flags:

- `bash scripts/homelab-host-report.sh` (default, no sudo)
- `bash scripts/homelab-host-report.sh --privileged` (best-effort `sudo -n`)
- `bash scripts/homelab-host-report.sh --privileged --deep` (heavier checks, still best-effort)

On Windows (operator PC), you can run all hosts from a manifest:

- `.\scripts\run-homelab-host-report-all.ps1`
- `.\scripts\run-homelab-host-report-all.ps1 -Privileged`
- `.\scripts\run-homelab-host-report-all.ps1 -Privileged -Deep`
- Shorthand wrapper (taxonomy): `.\scripts\lab-op.ps1 -Action report-all -Privileged -Deep`

If you want **zero prompts** (true non-interactive runs), prefer the **repo-path** runner:

- `.\scripts\lab-op-sync-and-collect.ps1 -SkipGitPull -Privileged -Deep`

This runs the report as `bash scripts/homelab-host-report.sh ...` **inside the repo path** listed for each host in the manifest (stable path for sudoers allowlists).

## Recommended sudoers pattern (restricted)

If you want passwordless collection, do it **surgically**:

- allow a single command (the report script) with fixed arguments
- do not allow editing tools, shells, or globbing commands

### Example (template — replace placeholders)

1) On the host, create a sudoers include:

```bash
sudo visudo -f /etc/sudoers.d/labop-host-report
```

2) Paste (replace `LEITAO_USER` and `REPO_PATH`):

```text
# Allow only the LAB-OP host report to run without a password.
# Replace:
# - LEITAO_USER: your Linux username (e.g. leitao)
# - REPO_PATH: absolute path to the repo clone on that host (no spaces preferred)

Cmnd_Alias LABOP_HOST_REPORT = /bin/bash REPO_PATH/scripts/homelab-host-report.sh --privileged, \
                               /usr/bin/bash REPO_PATH/scripts/homelab-host-report.sh --privileged, \
                               /bin/bash REPO_PATH/scripts/homelab-host-report.sh --privileged --deep, \
                               /usr/bin/bash REPO_PATH/scripts/homelab-host-report.sh --privileged --deep

LEITAO_USER ALL=(root) NOPASSWD: LABOP_HOST_REPORT
```

3) Validate:

```bash
sudo -l
sudo -n /bin/bash REPO_PATH/scripts/homelab-host-report.sh --privileged | head -20
```

### Shell path in sudoers (`/bin/bash` vs `/usr/bin/bash`)

`sudo` matches the **invoked executable path literally**. On some hosts `command -v bash` is **`/usr/bin/bash`** (e.g. Void) while your muscle memory uses **`/bin/bash`**. If NOPASSWD lists only one of them, the other form will ask for a password. **List both** in `Cmnd_Alias` (as in the template above and in role **`lab-node-01_labop_sudoers`**).

### One-time setup checklist (per host)

1) Ensure the repo exists at a stable path on that host (example):

```bash
ls -la "$HOME/Projects/dev/data-boar/scripts/homelab-host-report.sh"
```

2) Create the sudoers include (restricted) and validate:

```bash
sudo visudo -f /etc/sudoers.d/labop-host-report
sudo -l
sudo -n /bin/bash "$HOME/Projects/dev/data-boar/scripts/homelab-host-report.sh" --privileged --deep | head -40
```

3) From the Windows operator PC, run an all-host privileged collection **without prompts**:

```powershell
.\scripts\lab-op-sync-and-collect.ps1 -SkipGitPull -Privileged -Deep
```

## Ansible Podman apply (same narrow NOPASSWD discipline)

To avoid **BECOME** password prompts when installing **only** Podman via
`playbooks/lab-node-01-podman.yml`, extend the sudoers include with **fixed** commands for
`scripts/lab-node-01-ansible-labop-podman-apply.sh` (same spirit as `homelab-host-report.sh`).
The Ansible role **`lab-node-01_labop_sudoers`** writes **`LABOP_HOST_REPORT`** and
**`LABOP_ANSIBLE_PODMAN`** together when **`lab-node-01_labop_sudoers_enable: true`**.

Example merge (replace `LEITAO_USER` / `REPO_PATH`):

```text
Cmnd_Alias LABOP_ANSIBLE_PODMAN = /bin/bash REPO_PATH/scripts/lab-node-01-ansible-labop-podman-apply.sh --apply, \
                                  /usr/bin/bash REPO_PATH/scripts/lab-node-01-ansible-labop-podman-apply.sh --apply, \
                                  /bin/bash REPO_PATH/scripts/lab-node-01-ansible-labop-podman-apply.sh --check, \
                                  /usr/bin/bash REPO_PATH/scripts/lab-node-01-ansible-labop-podman-apply.sh --check

LEITAO_USER ALL=(root) NOPASSWD: LABOP_HOST_REPORT, LABOP_ANSIBLE_PODMAN
```

On the host (after `visudo -cf`):

```bash
sudo -n /bin/bash "$HOME/Projects/dev/data-boar/scripts/lab-node-01-ansible-labop-podman-apply.sh" --check
sudo -n /bin/bash "$HOME/Projects/dev/data-boar/scripts/lab-node-01-ansible-labop-podman-apply.sh" --apply
```

From Windows (**non-interactive** SSH; no Ansible `-K` prompt):

```powershell
.\scripts\lab-node-01-ansible-baseline.ps1 -SshHost lab-node-01 -Apply -SkipCheck -PodmanOnly -NoAskBecomePass
```

Requires **`ansible-playbook`** on the target and the sudoers lines above. When the wrapper runs under **`sudo`**, **`secure_path`** may hide the operator’s **`~/.local/bin`**; **`scripts/lab-node-01-ansible-labop-podman-apply.sh`** prepends **`~/.local/bin`** / **`~/.cargo/bin`** from **`getent passwd`** for **`SUDO_USER`** when possible. If **`ansible-playbook`** is still missing, install the **`ansible`** package on the host (e.g. Debian: **`apt install ansible`**) so **`ansible-playbook`** is on a system path.

### Sudoers.d order vs `%wheel` (Void Linux)

Drop-ins under **`/etc/sudoers.d/`** are read in **filename sort order** (C locale). If **`wheel`** (or similar) contains **`%wheel ALL=(ALL:ALL) ALL`** and your user is in **`wheel`**, that **broad** rule may be parsed **after** a file named e.g. **`labop-host-report`**, so **`sudo -n`** still returns **`a password is required`** even when **`sudo -l`** lists your **`NOPASSWD`** lines. Rename the LAB include so it sorts **after** **`wheel`** — e.g. **`z-labop-host-report`**. **Do not** rely on a **`99-`** prefix to sort “last”: **digits sort before letters**, so **`99-…`** still comes **before** **`wheel`**.

### “Already up to date” on the lab host but Void still hits `apt` / `python3-apt` / `sshfs`

If **`git pull --ff-only origin main`** says **up to date** but **`lab-node-01-ansible-labop-podman-apply.sh --check`** still fails inside **`ansible.builtin.apt`** (or **`labop-share-client-install.sh`** still tries the **`sshfs`** package name on Void), the **canonical fixes are not on the Git remote** the host tracks — e.g. changes only exist on the **operator dev PC** working tree until **committed and pushed**. Confirm on the host: **`git log -1 --oneline`** matches **`main`** on GitHub, then pull again.

### Maestro target NFS / CIFS ensure (`Handle-target_nfs`, `Handle-target_cifs`)

Maestro handlers run **read-only** checks with **`--check`** (default) or **`--apply`** in **`-Deep`** mode:

```bash
sudo -n bash "$HOME/Projects/dev/data-boar/scripts/labop-nfs-server-ensure.sh" --check
sudo -n bash "$HOME/Projects/dev/data-boar/scripts/labop-smb-server-ensure.sh" --check
```

**`Cmnd_Alias`** entries must list **both** **`--check`** and **`--apply`**, and **both** **`/bin/bash`** and **`/usr/bin/bash`**, on the **canonical** repo path (not version-suffixed ephemeral checkouts). Tracked template: **`docs/private.example/homelab/labop-maestro-target-sudoers.example`**. Merge into **`/etc/sudoers.d/z-labop-host-report`** (sort **after** **`wheel`** — see above). Validate: **`sudo visudo -cf /etc/sudoers.d/z-labop-host-report`**.

## Guardrails

- Prefer removing the sudoers file after the collection window if you don't need it long term.
- Never use `NOPASSWD: ALL`.
- Keep hostnames, IPs and secrets out of tracked docs; store raw logs under `docs/private/homelab/reports/`.

