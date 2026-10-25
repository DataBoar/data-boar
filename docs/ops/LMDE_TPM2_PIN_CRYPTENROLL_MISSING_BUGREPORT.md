# Bug report (copy/paste): LMDE missing `systemd-cryptenroll` blocks TPM2+PIN LUKS enrollment

**pt-BR:** [LMDE_TPM2_PIN_CRYPTENROLL_MISSING_BUGREPORT.pt_BR.md](LMDE_TPM2_PIN_CRYPTENROLL_MISSING_BUGREPORT.pt_BR.md)

## Where to report (recommended channels)

- **Primary (LMDE-specific)**: open an issue in `linuxmint/lmde7-beta` (GitHub).
- **Guidance**: [Reporting an issue](https://linuxmint.github.io/reporting-an-issue.html)

## Summary

On an installed LMDE 7 system, the `systemd-cryptenroll` utility is not available (`command not found` / missing binary). This blocks TPM2-based enrollment for LUKS (including the common “TPM2 + PIN” pattern), which is important for users who need full-disk encryption with pre-boot authentication (enterprise / high-assurance / “evil maid” threat model).

As a workaround, `clevis+tpm2` can provide TPM-only unlock, but it does not cover the same TPM2+PIN UX/security posture out of the box.

## Environment

- **Distro**: LMDE 7 “Gigi”
- **Goal**: LUKS2 full-disk encryption with TPM2-assisted unlock (preferably TPM2 + PIN)
- **Observed**: `systemd` is installed and running, but `systemd-cryptenroll` is missing from typical paths.

## Reproduction (minimal)

On the installed LMDE system:

```bash
command -v systemd-cryptenroll || true
ls -la /usr/bin/systemd-cryptenroll /usr/lib/systemd/systemd-cryptenroll 2>/dev/null || true
dpkg -L systemd | grep -i cryptenroll || true
apt-cache search --names-only cryptenroll || true
```

## Expected

- `systemd-cryptenroll` is available as part of the LMDE systemd tooling (as it is on Debian-family distributions), enabling:
  - `systemd-cryptenroll --tpm2-device=auto --tpm2-with-pin=yes ...`

## Actual

- `systemd-cryptenroll` is not found / not shipped, forcing users into alternative tooling.

## Why this matters (brief)

- TPM2+PIN provides a better balance between convenience and protection against offline/“evil maid” style attacks than TPM-only unlock.
- Lack of the tool nudges users toward weaker operational choices (shorter passphrases, TPM-only, or manual passphrase entry every boot).

## Suggested direction

- Ship `systemd-cryptenroll` in LMDE 7 (or document which package provides it in LMDE).
- If intentionally excluded, document the recommended supported approach for TPM2+PIN with LUKS on LMDE.

