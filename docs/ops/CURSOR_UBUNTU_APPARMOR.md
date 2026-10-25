# Cursor on Ubuntu / Zorin OS with AppArmor

**Português (Brasil):** [CURSOR_UBUNTU_APPARMOR.pt_BR.md](CURSOR_UBUNTU_APPARMOR.pt_BR.md)

**Audience:** Operators using **Cursor** on **Ubuntu**-based desktops (**Zorin OS 18** ≈ **Ubuntu 24.04 noble** base) where **AppArmor** is enabled (default on supported flavours).

**Goal:** Install Cursor, confirm whether AppArmor affects it, and apply **safe, incremental** fixes if the kernel denies operations.

**Not covered here:** **Snap**-packaged editors (different confinement), **Flatpak** Cursor (Bubblewrap), **Firejail**/other wrappers layered on top of AppArmor—treat those as separate stacks.

---

## 1. Preconditions

1. **AppArmor** active (typical on Ubuntu/Zorin):

   ```bash
   systemctl is-active apparmor && sudo aa-status --enabled
   ```

1. Optional helpers:

   ```bash
   sudo apt update
   sudo apt install -y apparmor-utils
   ```

---

## 2. Install Cursor (official Linux `.deb`)

1. Download the **Linux** `.deb` from [cursor.com](https://cursor.com) (or your licensed channel).
1. Install:

   ```bash
   sudo apt install -y ./cursor_*.deb
   # or: sudo dpkg -i ./cursor_*.deb && sudo apt -f install
   ```

1. Confirm the launcher:

   ```bash
   command -v cursor
   cursor --version
   ```

**Typical paths** (may change between releases):

- Binary: `/usr/bin/cursor` → often points into `/usr/share/cursor/`
- User data: `~/.config/Cursor/`, `~/.cursor/` (extensions, rules)

---

## 3. Default case: no extra AppArmor work

On many **.deb** installs, Cursor runs **without a dedicated AppArmor profile** (process shows as **unconfined** in `aa-status`). In that case **AppArmor does not block** Cursor; focus troubleshooting on permissions, Wayland/X11, or GPU drivers—not MAC.

Check:

```bash
sudo aa-status 2>/dev/null | grep -i cursor || true
# If empty: usually no profile → unconfined for AppArmor purposes
```

Start Cursor from a terminal once to capture errors:

```bash
cursor --verbose 2>&1 | tee /tmp/cursor-launch.log
```

---

## 4. When AppArmor *does* block Cursor

Symptoms: editor crashes on startup, integrated **terminal** fails, **Git** operations fail, or **file save** to certain trees fails—**and** the kernel log shows **AppArmor DENIED** for `cursor`, `cursor-sandbox`, or a child (e.g. `node`, `bash`).

### 4.1 Collect evidence

```bash
sudo dmesg -T | tail -80
sudo journalctl -k -b --no-pager | grep -iE 'apparmor|denied' | tail -40
```

Note the **profile name** in the denial line (e.g. `usr.share.cursor.cursor`, `cursor`, or a path-based name).

### 4.2 See loaded profiles

```bash
sudo aa-status
```

If a **Cursor-related** profile appears in **enforce** mode and you see matching **DENIED** lines, continue to §5.

---

## 5. Remediation (prefer least privilege)

### 5.1 Update Cursor

Install the latest `.deb`; upstream sometimes adjusts install layout or adds compatibility.

### 5.2 Complain mode (temporary diagnostic)

**Only if** a profile exists and references Cursor. Switches that profile to **learn/allow while logging** (Ubuntu: `aa-complain`):

```bash
sudo aa-complain /etc/apparmor.d/<profile-name>
# Re-test Cursor; review logs; then tighten (§5.3) or return to enforce when fixed
sudo aa-enforce /etc/apparmor.d/<profile-name>
```

Replace `<profile-name>` with the file under `/etc/apparmor.d/` that corresponds to the denial (use `ls /etc/apparmor.d/ | grep -i cursor`).

### 5.3 Local overrides (preferred long-term)

Ubuntu-style packages often support **`#include <local/...>`** in the main profile. Add rules only in **`/etc/apparmor.d/local/`** so package upgrades do not wipe your edits.

1. Find the main profile:

   ```bash
   grep -ril cursor /etc/apparmor.d/ 2>/dev/null
   ```

1. Open it and confirm an include like:

   `#include <local/usr.bin.cursor>`

1. Create the local file (example name—**must match** the include in **your** system):

   ```bash
   sudo install -m 644 /dev/null /etc/apparmor.d/local/usr.bin.cursor
   sudo editor /etc/apparmor.d/local/usr.bin.cursor
   ```

1. Add **minimal** permissions. Common needs for an IDE (adjust to denials you actually see):

   - Read/write config and cache under **`@{HOME}/.config/Cursor/`** and **`@{HOME}/.cursor/`**
   - Read **`@{HOME}/.ssh/`** if Git uses SSH keys (often read-only)
   - **`ix`** (inherit execute) for **`/usr/bin/git`**, **`/bin/bash`** or **`/usr/bin/bash`** if the profile requires explicit execute rules

   **Do not** paste untrusted full profiles from the web; extend only what **`dmesg`**/**`journalctl`** shows as **DENIED**.

1. Reload:

   ```bash
   sudo apparmor_parser -r /etc/apparmor.d/<main-profile>
   ```

### 5.4 Custom profile from scratch

Reserved for advanced use: use **`aa-genprof`** / **`aa-logprof`** (see Ubuntu Server Guide — *Security — AppArmor*) to build a profile from audit logs. Expect iteration; Electron apps spawn many children.

### 5.5 What not to do

- **Do not** disable AppArmor globally (`systemctl disable apparmor` or kernel `apparmor=0`) on a machine you care about—unless you accept losing MAC for **all** applications.
- **Do not** set profiles to **unconfined** for convenience without documenting the risk.

---

## 6. Zorin OS notes

- **Zorin OS 18** uses an **Ubuntu noble** base for core packages; **AppArmor** behaviour matches **Ubuntu 24.04** for this guide.
- **Wayland** (default on recent GNOME) does not remove AppArmor; failures are still visible as **DENIED** in the kernel log if a profile applies.
- If **Lynis** reports *AppArmor present but “MAC framework NONE”* for specific services, that is a **separate** audit nuance—this doc only addresses **Cursor** usability with AppArmor.

---

## 7. Cross-links

- Operator homelab context (e.g. **`lab-op`** / Ubuntu-family desktop): private **`docs/private/homelab/LAB_SECURITY_POSTURE.md`** §2 (UFW, Lynis, AppArmor mentions)—**not** a substitute for this runbook.
- **Cursor + secrets / `docs/private/`:** **[PRIVATE_OPERATOR_NOTES.md](../PRIVATE_OPERATOR_NOTES.md)**.
- **Windows / WSL** Cursor path split: **[WINDOWS_WSL_MULTI_DISTRO_LAB.md](WINDOWS_WSL_MULTI_DISTRO_LAB.md)**.

---

## 8. Revision

| Date       | Note                                                 |
| ---------- | ----                                                 |
| 2026-03-22 | Initial runbook (Ubuntu / Zorin, AppArmor workflow). |
