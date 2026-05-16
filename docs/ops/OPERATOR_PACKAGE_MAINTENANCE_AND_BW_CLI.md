# Operator workstation: package maintenance, Bitwarden CLI, Topgrade

**Português (Brasil):** [OPERATOR_PACKAGE_MAINTENANCE_AND_BW_CLI.pt_BR.md](OPERATOR_PACKAGE_MAINTENANCE_AND_BW_CLI.pt_BR.md)

**Purpose:** Record **concrete, operator-tested** habits for keeping **Windows**, **WSL**, and **Linux** hosts updated (including **Debian/Ubuntu**, **Void / xbps**, and others) without fighting duplicate package managers, and to install **Bitwarden CLI** (`bw`) where this repo expects it. **No secrets** here — no tokens, no `BW_SESSION`, no webhook URLs.

**Audience:** Maintainer / operator. Aligns with [OPERATOR_SECRETS_BITWARDEN.md](OPERATOR_SECRETS_BITWARDEN.md) (repository contract) and [SECURITY.md](../../SECURITY.md).

---

## 1. Bitwarden desktop vs Bitwarden CLI (`bw`)

- Installing the **Bitwarden desktop** app (for example via **winget** as `Bitwarden.Bitwarden`) **does not** install the **`bw`** command.
- **`bw`** is a **separate** component. Install it explicitly on **each** environment where you want shell scripts or Cursor terminals to run it.

### 1.1 Windows (native PowerShell / cmd)

- **Recommended:** install with **winget** so the same ecosystem stays aligned with **Winget Auto-Update (WAU)** and other tooling you refresh with **Topgrade** on Windows:

  ```text
  winget install Bitwarden.CLI
  ```

  Verify `winget search "Bitwarden CLI"` — the **ID** may change over time; keep **one** install path per machine.

- After install, **close and reopen** the terminal (or Cursor) so **`PATH`** picks up `bw`.

- Check:

  ```powershell
  Get-Command bw
  bw --version
  ```

### 1.2 WSL and Linux (separate `PATH`)

- **WSL** and **Linux** hosts have their **own** `PATH`. Installing `bw` on **Windows** does **not** make it available inside **WSL**.

- Pick **one** method per environment (examples — use whichever you already standardize on): **Homebrew** (`brew install bitwarden-cli`), **npm** `@bitwarden/cli`, or a **distribution** package if maintained and trusted.

- **Debian/Ubuntu + npm:** Bitwarden’s [CLI documentation](https://bitwarden.com/help/cli/) states that installing via `npm` on Linux may require the **`build-essential`** metapackage (or your distribution’s equivalent) first, for example `sudo apt install build-essential`. The **`lab-node-01_bitwarden_cli`** Ansible role and **`scripts/lab-node-01-bitwarden-cli-bootstrap.sh`** install it alongside **`nodejs`** / **`npm`**.

- Verify with:

  ```bash
  command -v bw && bw --version
  ```

### 1.2.1 Void Linux (`xbps`) — Bitwarden CLI

There is **no** `bitwarden-cli` package in Void’s default `xbps` repos. Use **Node.js** from Void (`npm` ships **inside** the `nodejs` package — there is **no** separate `npm` package on Void):

```bash
sudo xbps-install -S nodejs
```

By default, **`npm install -g`** writes under **`/usr/lib/node_modules`**, so a normal user gets **`EACCES`**. Pick **one**:

**A — System-wide (simplest on a personal lab host):**

```bash
sudo npm install -g @bitwarden/cli
command -v bw && bw --version
```

**B — User prefix (no `sudo npm`):**

```bash
mkdir -p ~/.local
npm config set prefix ~/.local
grep -q '\.local/bin' ~/.bashrc 2>/dev/null || echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
export PATH="$HOME/.local/bin:$PATH"
npm install -g @bitwarden/cli
command -v bw && bw --version
```

For other Node major versions, search `xbps-query -Rs nodejs` (e.g. `nodejs-lts`). **`bw login` / `bw unlock`** stay manual (warm session); do not paste secrets into tracked docs.

**Git `pull` after a force-pushed `main`:** if Git reports **divergent branches**, either reconcile with `git pull --rebase origin main` (or merge), or — if the clone has **no local commits** you need — align to the server: `git fetch origin && git reset --hard origin/main`.

### 1.2.2 Linux (Flatpak + alias) — Bitwarden CLI

If you prefer **not** to use **`npm`** on the host, Bitwarden documents installing the **desktop** Flatpak and invoking the CLI through it ([CLI help — Flatpak](https://bitwarden.com/help/cli/)):

```bash
flatpak install flathub com.bitwarden.desktop
# one-off:
flatpak run --command=bw com.bitwarden.desktop --version
# shell alias (e.g. in ~/.bashrc):
alias bw='flatpak run --command=bw com.bitwarden.desktop'
```

After defining the alias, **`command -v bw`** may show `alias` (that is expected). For **LAB-NODE-01 baseline**, set **`lab-node-01_install_bitwarden_cli: false`** in inventory if you standardize on Flatpak-only **`bw`**, so Ansible does not also install **`@bitwarden/cli`** via **`npm`**.

### 1.3 One package manager per tool (avoid duplicates)

- **Do not** install the same binary (`bw`, `git`, `python`, …) via **winget**, **Chocolatey**, **Scoop**, and **manual** copies on the **same** Windows profile. Pick **one** primary source per tool and **keep a private note** (for example under `docs/private/`) of “`bw` = winget” so upgrades stay predictable.

---

## 2. `gta` + Topgrade on Linux (overlap and roles)

Many operators keep a **shell script** (often nicknamed **`gta`** — “get them all”) that runs a **full** OS maintenance sequence for that **distribution**, then **`topgrade`**.

On **Debian/Ubuntu**, that often means **`dpkg` / `apt`** steps, then **`topgrade`**, then an optional **tail** with **`needrestart`** and sometimes **bootloader / initramfs** refresh (see **section 2.4**).

**Topgrade** (`~/.config/topgrade.toml` on Unix) orchestrates **many** steps (brew, cargo, flatpak, **system** packages bound to **whatever packager that host uses**, …). On **Debian/Ubuntu**, the **OS package** step (often shown as **System** in Topgrade output) can overlap with **`apt`** if you already ran **`apt`** inside **`gta`**.

### 2.1 Why overlap matters (Debian / Ubuntu)

- Running **full `apt`** in **`gta`** and then letting Topgrade run the **system** step **again** in the **same session** is usually **harmless** if the first pass completed, but it **wastes time** and can **prompt** again (`sudo`, `needrestart`) when you expected a quiet tail.

### 2.2 Concrete adjustments — Debian / Ubuntu (pick one strategy)

1. **Split cadence (recommended starting point)**
   - **Heavy day:** run **`gta`** end-to-end.
   - Then run Topgrade **skipping** the OS step for **that** run only, so Topgrade still refreshes **brew**, **flatpak**, **cargo**, **git pulls**, etc.
   - The exact flag depends on your Topgrade version — check **`topgrade --help`** for **`--disable`** / **`--only`** and the step name your distro uses (often **`system`** on Debian/Ubuntu).

2. **Single owner for `apt`**
   - Slim **`gta`** to **repair** + **`apt update`** + **`apt -f install`**, and let **Topgrade** own **`full-upgrade`** — **or** the opposite: **`gta` owns all `apt`**, and **Topgrade** never touches OS packages.
   - **Do not** mix “two owners” without a clear rule, or you will not know which log to trust after a bad upgrade.

3. **Global Topgrade config**
   - If you **always** run **`gta` before `topgrade`** and you **never** rely on standalone Topgrade for OS upgrades, you can add the OS step to **`[misc] disable`** in **`topgrade.toml`** (alongside any existing entries such as **`nix`**, **`containers`**).
   - **Trade-off:** a **standalone** `topgrade` run **without** `gta` would then **not** upgrade system packages until you run **`gta`** again.

4. **Unattended runs**
   - Consider **`pre_sudo = true`** under **`[misc]`** so **`sudo -v`** runs **early** and avoids a **blocking** password prompt in the middle of a long run (see Topgrade’s own comments in the generated config reference).

### 2.3 `topgrade.toml` differs per machine (illustrative)

- On one workstation you might set **`disable = ["nix", "containers"]`** under **`[misc]`**; on another Linux box the **`disable`** list may be **empty** (everything still default/commented in the template). **`~/.config/topgrade.toml`** is **per user, per host** — **do not** assume copies behave the same after `scp`.
- When you adopt one of the strategies in **section 2.2**, **document the change** in a **gitignored** note or in a **comment** at the top of your own `gta` so you remember why **`system`** is disabled or why the **`apt`** block was slimmed.

### 2.4 Multiple Linux hosts — Debian / Ubuntu `gta` tails

You may use **`gta`** on **several** Debian/Ubuntu systems (for example a **daily driver** and a **lab / secondary** install). **Do not** put **real hostnames** or LAN identities into **tracked** repo docs — keep that mapping under **`docs/private/`** (per **[AGENTS.md](../../AGENTS.md)**).

**Shared core (typical):** heavy **`apt`** repair and upgrade **→** **`topgrade -y`** so **brew**, **cargo**, **flatpak**, **git** pulls, etc. still run even when **`apt`** already upgraded the OS.

**Tail variants (choose per host):**

1. **Minimal tail:** run **`needrestart`** after Topgrade (or rely on your distro’s own prompts) so you see **services / kernel** that still need a restart.
2. **Kernel / boot maintenance tail:** after Topgrade, run **`update-grub2`** (or your distro’s supported bootloader update command) **→** **`update-initramfs -u`** **→** **`needrestart`**. Use when you want the **same** maintenance window to refresh **initramfs** and **bootloader config** after **`apt`** pulled a new kernel or related meta-package — **`needrestart`** **last** gives a single summary of what still wants a root or service bounce.

**Commented blocks** you sometimes enable on only one machine (**`nala`**, **`deb-get`**, **`snap` / `flatpak`**, **container image pulls**) are **host policy**. Record **why** in private notes so future you does not “uncomment everything” blindly on a slow lab box.

### 2.5 Non-Debian `gta` (Void Linux / `xbps` pattern)

On **`xbps`**-based systems (for example **Void Linux**), **`gta`** is **not** an `apt` workflow. A pattern that works for some operators:

- **`xbps-install -Suy`** (or the **current** documented full-system upgrade for that Void install).
- **Helper tools** such as **`vpm`** (**`vpm update`**, **`vpm cleanup`**) when you use them — **confirm** subcommands against upstream docs; names and flags evolve.
- **`topgrade -y`** for userland and cross-ecosystem refresh.
- **Old kernel images:** **`vkpurge list`** then **`vkpurge rm all`** (or equivalent) so **`/boot`** does not fill after repeated kernel updates.
- **GRUB:** **`update-grub`** or **`grub-mkconfig`** when your layout needs a config rewrite after kernel rotation — enable only when your image actually uses GRUB that way.
- **`touch /forcefsck`** only when you **deliberately** schedule a full **fsck** on **next root** (understand downtime, **LUKS**, and rescue access first).

A **commented-out Debian `apt` block** in the same script can be a **portable template** between machines — **do not** uncomment it on **Void**. **Topgrade’s OS step** on that host maps to **`xbps`**, not **`apt`**.

**Shebang:** keep **`#!/bin/bash`** or **`#!/usr/bin/env bash`** — fix typos (for example **`bas0`**) before wiring the script into **cron** or **launchers**.

### 2.6 Debian on ARM / SBC — Topgrade only inside a Python `venv`

**Single-board** hosts (for example **Raspberry Pi**-class systems on **Debian** or **Raspberry Pi OS**) often reuse the **same `apt`-heavy `gta`** as desktops. **Topgrade** is sometimes installed **only** with **`pip`** into a user **virtualenv** (for example **`$HOME/.venv`**).

**Typical wrap:**

1. `source "$HOME/.venv/bin/activate"`
2. `topgrade -y`
3. `deactivate`

**Why `topgrade: command not found` happens:** interactive shells that **never** `source` the venv do not put **`topgrade`** on **`PATH`**. Running **`topgrade --config-reference`** “bare” will fail the same way — use the venv first, or install Topgrade somewhere **global** (**pipx**, **distro package**, **release binary**, **cargo**, …).

**Hardening (pick one):**

- Always drive updates through **`gta`** (or a one-line wrapper) that **activates** before **Topgrade**.
- Prefer **`pipx install topgrade`** (or equivalent) so the CLI lands in a **stable bin dir** you already put on **`PATH`**.
- If you extend **`PATH`** with **`$HOME/.venv/bin`**, do it deliberately (login shell vs **cron** vs **SSH**) so **cron** and **non-interactive** jobs do not silently skip **Topgrade**.

**Tail variant:** some **`gta`** copies end with **`update-initramfs -u`** **without** **`needrestart`** or **GRUB** refresh — common on **lighter** images; keep the per-host story in **private** notes.

**`touch /forcefsck`:** same caution as in **section 2.5** — only when you **mean** to force **fsck** on **next boot**.

---

## 3. Topgrade on Windows

- Windows uses a **separate** Topgrade configuration (see **`topgrade --config-reference`** on Windows for paths and keys).
- **winget** and **Chocolatey** / **Scoop** steps may all exist — **prefer one** primary manager per package (see section 1.3) to avoid conflicting versions.

---

## 4. Homelab and repo scripts

- **GitHub Actions** stays on **[repository secrets](../../.github/)** — **not** Bitwarden on public runners by default ([OPERATOR_SECRETS_BITWARDEN.md](OPERATOR_SECRETS_BITWARDEN.md)).
- **LAB-OP** scripts and **`homelab-host-report.sh`** only **see** `bw` if it is installed on **that** host’s **PATH** — see [HOMELAB_HOST_PACKAGE_INVENTORY.md](HOMELAB_HOST_PACKAGE_INVENTORY.md).

---

## 5. tmux dotfiles on LAB-OP Linux (`tmux-configs`)

Use one GitHub repo as the **source of truth** for terminal layout and key bindings, then apply it on **each** lab Linux host (Zorin/lab-node-02, Raspberry Pi, Void/LAB-NODE-03, LMDE/LAB-NODE-01, etc.):

- **Repository:** [github.com/FabioLeitao/tmux-configs](https://github.com/FabioLeitao/tmux-configs) (clone URL: `https://github.com/FabioLeitao/tmux-configs.git`).
- **Install `tmux` first** via the host’s packager (`apt` / `xbps-install` / Ansible baseline on LAB-NODE-01 already includes it).
- **Then** clone and follow that repo’s **README** (typically symlink `~/.tmux.conf`, TPM/plugins, prefix key). Example skeleton:

  ```bash
  mkdir -p ~/Projects/dev && cd ~/Projects/dev
  git clone https://github.com/FabioLeitao/tmux-configs.git
  cd tmux-configs
  # README: apply config (symlink or copy), install plugin manager if required, open new tmux session and validate.
  ```

- Keep **one** layout per machine (same clone path on every host, or document exceptions in private notes).

---

## See also

- [OPERATOR_SECRETS_BITWARDEN.md](OPERATOR_SECRETS_BITWARDEN.md) — `bw` contract, CI, tests.
- [LMDE7_LAB-NODE-01_DEVELOPER_SETUP.md](LMDE7_LAB-NODE-01_DEVELOPER_SETUP.md) — ThinkPad LAB-NODE-01 + LMDE baseline.
- [HOMELAB_HOST_PACKAGE_INVENTORY.md](HOMELAB_HOST_PACKAGE_INVENTORY.md) — inventory capture.
- [tmux-configs](https://github.com/FabioLeitao/tmux-configs) — tmux dotfiles (section **5** above).

**Last review:** 2026-04 — added Void `bw` (§1.2.1), tmux-configs §5, Bitwarden CLI IDs on [bitwarden.com](https://bitwarden.com/) / **winget** — confirm at install time.
