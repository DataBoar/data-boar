# Bug report (copy/paste): LMDE installer manual partitioning hides dm-crypt (`/dev/mapper/*`)

This report is written for LMDE/Linux Mint installer maintainers (Ubiquity / partitioning UI). It intentionally avoids secrets and environment-specific LAN details.

## Where to report (recommended channels)

- **Primary**: open an issue in the GitHub repo `linuxmint/ubiquity` (Issues tab).
- **Community guidelines**: [Reporting an issue](https://linuxmint.github.io/reporting-an-issue.html)

## Summary

When installing **LMDE** using **manual partitioning**, already-unlocked **dm-crypt** mappings (e.g. `cryptsetup open … cryptroot` → `/dev/mapper/cryptroot`) are **not shown** in the partition list. As a result, the installer cannot select the mapper as `/`.

This makes the manual-partitioning path unsafe: users are pushed toward selecting the underlying raw partition (e.g. `/dev/nvme0n1p6`) and formatting it, which destroys the LUKS header and breaks the intended full-disk encryption flow.

## Impact

- **User-facing risk**: easy to brick the intended encryption setup by formatting the raw block device.
- **UX issue**: manual partitioning is effectively non-functional for dm-crypt/FDE workflows.
- **Support burden**: leads to install loops and recovery attempts.

## Environment

- **Distro**: LMDE 7 “Gigi” live ISO
- **Installer**: “Install Linux Mint” (Ubiquity-based manual partitioning UI)
- **Firmware**: UEFI, Secure Boot enabled
- **Disk layout goal**:
  - ESP (FAT32) mounted at `/boot/efi` (existing)
  - ext4 `/boot`
  - root intended inside LUKS2 (btrfs)
- **Goal**: dual boot (Windows preserved), LUKS2 for root, btrfs snapshots later

> If needed, I can add exact package versions for `ubiquity`/installer components; please point to the preferred command(s) in LMDE live session.

## Reproduction steps (minimal)

1. Boot LMDE live ISO.
2. Prepare partitions (or use an existing target partition):
   - keep existing ESP (FAT32)
   - create ext4 `/boot`
   - create a large partition to be encrypted (example: `/dev/nvme0n1p6`)
3. In the live session, create and unlock the dm-crypt mapping:

```bash
sudo cryptsetup luksFormat /dev/nvme0n1p6
sudo cryptsetup open /dev/nvme0n1p6 cryptroot
```

4. Verify the mapper exists (before launching the installer):

```bash
ls -la /dev/mapper/
lsblk -f
```

5. Start the installer and go to **Manual partitioning**.

## Expected behavior

- Manual partitioning lists `/dev/mapper/cryptroot` (or equivalent unlocked mapper) and allows selecting it as `/` (and formatting it as btrfs/ext4).

## Actual behavior

- Manual partitioning does **not** list any `/dev/mapper/*` entries.
- Only the underlying raw partition (`/dev/nvme0n1p6`) appears as a selectable target for `/` and formatting.

## Evidence to attach (non-sensitive)

- **Screenshot 1**: manual partitioning screen showing the absence of `/dev/mapper/*` entries.
- **Terminal output**:
  - `ls -la /dev/mapper/` (shows `cryptroot` mapping exists)
  - `lsblk -f` (shows `crypto_LUKS` + the mapping)

> Screenshots are not included in this repo draft. When filing the issue, attach the screenshots collected during the install attempt.

## Workaround used (works, but non-obvious)

Install first onto **plain btrfs** on the raw partition, **do not root**, then encrypt in-place using `cryptsetup reencrypt`, followed by initramfs/GRUB updates from a chroot (details available on request).

- Community guide reference: `https://gist.github.com/Leniwcowaty/4b2c239ca74629cad60d4718f79ff600`

## Additional context (kept brief)

In our setup we also tried to reach a “BitLocker-like” UX with strong FDE (LUKS) while minimizing boot friction:

- `systemd-cryptenroll` was not available on the installed LMDE environment, so we could not test TPM2+PIN enrollment via `systemd-cryptenroll`.
- We used `clevis+tpm2` as a workaround to reduce repeated passphrase entry, but this tends toward TPM-only unlock unless additional boot authentication is implemented.

This is **not** the core of this bug report, but it increased the cost of workarounds after the installer failed to expose `/dev/mapper/*` in manual partitioning.

Related issue (TPM2+PIN / `systemd-cryptenroll` availability): `https://github.com/linuxmint/live-installer/issues/177`

## Suggested fix direction

- In manual partitioning, refresh and include `/dev/mapper/*` devices once dm-crypt has been unlocked.
- Alternatively, provide an explicit UI action to “unlock encrypted volume”, and after unlock, surface the mapper device as a selectable target.

