# Known residual lab-script pitfalls (copy to `docs/private/homelab/`)

**Tracked template only.** Copy to **`docs/private/homelab/KNOWN_BUGS.md`** and fill site-specific notes there.

**Never** put real hostnames, RFC1918 IPs, or real home paths in **tracked** files, issues, or PRs.

## Privileged `$HOME` vs operator home

Under non-interactive `sudo`, `$HOME` is often the privileged account home. Tracked `labop-*-ensure.sh` scripts should resolve the operator home via `getent` / `SUDO_USER` (or an explicit CLI path) — not `$HOME` — for corpus/export and ephemeral-firewall state files.

Residual operator notes (defaults under `Documents/`, empty-`SUDO_USER` fallback policy, Maestro handler explicit paths) live only in the **private** copy of this file.

See public **`AGENTS.md`** (*Lab host preflight*) for the short, non-reproductive reminder and **`docs/PRIVATE_OPERATOR_NOTES.md`** for the private-tree pointer.
