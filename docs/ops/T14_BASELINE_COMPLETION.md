# ThinkPad LAB-NODE-01 — finish LAB-OP baseline (Ansible) and secret-session workflow

**Português (Brasil):** [LAB-NODE-01_BASELINE_COMPLETION.pt_BR.md](LAB-NODE-01_BASELINE_COMPLETION.pt_BR.md)

This runbook ties together **repeatable host hardening** (Ansible in this repo) and **operator habits** (sudo credential, Bitwarden CLI, optional VeraCrypt) without putting secrets in Git.

## 1. Finish the Ansible baseline (on the LAB-NODE-01)

1. **Sync the repo:** `git pull` in your clone of `data-boar`.
2. **Inventory:** `ops/automation/ansible/inventory.local.ini` must include **`localhost ansible_connection=local`** under `[lab-node-01]` when you run the playbook **on the laptop itself** (not from another PC over SSH).
3. **Preflight:** from the repo root, run **`bash scripts/lab-node-01-ansible-preflight.sh`** — checks Ansible, inventory, sudo, `docker.list` permissions, and `bw` presence.
4. **Only `bw` missing / `docker.list` noise:** from the repo root, **`bash scripts/lab-node-01-bitwarden-cli-bootstrap.sh`** (installs **`@bitwarden/cli`**, fixes permissions and **`PATH`** for tmux). Then **`source /etc/bash.bashrc`** or open a **new tmux pane**.
5. **Sudo:** `sudo -v` so the password prompt succeeds before a long run.
6. **Apply:** from `ops/automation/ansible/`, run **`ansible-playbook -i inventory.local.ini --ask-become-pass playbooks/lab-node-01-baseline.yml --diff`** (see **[ops/automation/ansible/README.md](../../ops/automation/ansible/README.md)** for troubleshooting).

After a successful run, **`bw`** should be at **`/usr/local/bin/bw`**. Role **`lab_node_01_bitwarden_cli`** installs **`/etc/profile.d/zz-local-bin.sh`** and a block in **`/etc/bash.bashrc`** so **tmux** / non-login interactive bash gets **`PATH`**. If `bw` is still missing, open a **new tmux pane** or run **`source /etc/bash.bashrc`**, or call **`/usr/local/bin/bw`** directly.

## 2. Session warm-up: sudo + Bitwarden CLI (no VeraCrypt)

Typical order:

1. **`export PATH="/usr/local/bin:$PATH"`** (or source **`profile.d`** as above).
2. **`sudo -v`** — refreshes sudo timestamp; avoids mid-task password prompts during installs or mounts.
3. **`bw login`** (once per machine) / **`bw unlock`** — then **`export BW_SESSION=…`** as documented by Bitwarden for your shell.

**Note:** Debian **`command-not-found`** may suggest **`bundlewrap`** when you type **`bw`** — ignore; use the full path **`/usr/local/bin/bw`** if needed.

**Flatpak + alias:** If you use **`alias bw='flatpak run --command=bw …'`** in **`~/.bashrc`**, **`command -v bw`** may print **`alias`** — that is expected (see [OPERATOR_PACKAGE_MAINTENANCE_AND_BW_CLI.md](OPERATOR_PACKAGE_MAINTENANCE_AND_BW_CLI.md), section **1.2.2**).

**Session hygiene:** Treat **`BW_SESSION`** like a secret. When you are done, run **`bw lock`** (or **`bw logout`**). Before screenshots or sharing a terminal view, lock proactively or redact session output; use only fake/demo material if you need an example line.

## 3. VeraCrypt + stacked private repo (operator-only)

Paths, keyfiles, and container locations are **not** duplicated here (they belong in **gitignored** notes). After baseline and `bw` work, follow the operator’s **VeraCrypt + private Git** guide under **`docs/private/homelab/`** (e.g. **`VERACRYPT_PRIVATE_REPO_SETUP.pt_BR.md`**, section **6.6** for the LAB-NODE-01 flow: baseline → sudo warm → `bw` → mount).

**Tracked helpers (no secrets):** **`scripts/lab-node-01-install-veracrypt-console-debian13.sh`** (download/verify GPG, `apt install` console `.deb` for Debian 13 amd64) and **`scripts/lab-node-01-veracrypt-mount-private-repo.sh`** (mount **`~/.kb-cache/private_repo.vc`** with default Colleague-K + keyfile path; password prompt only). The volume’s hash (e.g. SHA-512) is set at creation time, not passed at mount.

## 4. Related docs

- **[LMDE7_LAB-NODE-01_DEVELOPER_SETUP.md](LMDE7_LAB-NODE-01_DEVELOPER_SETUP.md)** — full LAB-NODE-01 + LMDE preparation (dual boot, packages, uv, etc.).
- **[ops/automation/ansible/README.md](../../ops/automation/ansible/README.md)** — baseline playbook, inventory, BECOME issues.
- **`scripts/lab-node-01-ansible-preflight.sh`** — preflight checks.
- **`scripts/lab-node-01-session-warm.sh`** — optional: PATH (`/usr/local/bin`, Flatpak exports), `sudo -v`, `bw` check (npm **or** Flatpak), tmux hints (safe to commit; no secrets).
