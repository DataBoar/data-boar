# Time Machine USB recovery and repurpose playbook (safe-first)

**Português (Brasil):** [TIME_MACHINE_USB_RECOVERY_AND_REPURPOSE.pt_BR.md](TIME_MACHINE_USB_RECOVERY_AND_REPURPOSE.pt_BR.md)

Use this runbook when you have a former macOS Time Machine USB disk and need to recover data **before** repairing/replacing the Mac.

## Scope and safety model

- Goal A: recover user data now.
- Goal B: repurpose the same USB disk as an external backup target (P0 storage lane).
- Safety rule: **never write to the source disk** before recovery/copy validation.

## 0) Preconditions

- A Linux host in lab-op with enough free space for recovered data.
- Stable USB cable/power (avoid hubs if possible).
- Packages available:
  - `smartmontools`, `gddrescue`, `rsync`, `util-linux`
  - optional filesystem tools depending on format (HFS+ vs APFS).

## 1) Intake and triage (read-only)

```bash
lsblk -o NAME,SIZE,FSTYPE,LABEL,MODEL,SERIAL,MOUNTPOINT
sudo smartctl -a /dev/sdX
sudo fdisk -l /dev/sdX
```

- Replace `sdX` with the real disk (not a partition).
- If SMART shows heavy failure signs, prioritize cloning with `ddrescue` first.

## 2) Decide filesystem path

### Path A — HFS+ Time Machine (older setups)

```bash
sudo mkdir -p /mnt/tm_ro
sudo mount -t hfsplus -o ro /dev/sdXn /mnt/tm_ro
```

### Path B — APFS Time Machine (newer macOS)

Linux APFS support is usually read-only and tool-dependent. If APFS mounting is unstable in your host:

- Preferred fallback: attach the disk temporarily to a working macOS machine for copy/export.
- If Linux APFS read-only is available in your environment, keep it strictly read-only and validate copies with checksums.

## 3) If disk health is bad: clone first

```bash
sudo ddrescue -f -n /dev/sdX /path/recovery/tm_image.img /path/recovery/tm_image.log
sudo ddrescue -d -r3 /dev/sdX /path/recovery/tm_image.img /path/recovery/tm_image.log
```

- Work on the image, not the original disk, after this point.

## 4) Copy data out (preserve metadata where possible)

```bash
mkdir -p /path/recovery/export
sudo rsync -aHAX --info=progress2 /mnt/tm_ro/ /path/recovery/export/
```

Then validate:

```bash
du -sh /mnt/tm_ro /path/recovery/export
```

Optional integrity sample:

```bash
find /path/recovery/export -type f | shuf -n 20 | xargs -I{} sha256sum "{}"
```

## 5) Only after recovery: repurpose disk for P0 external backup

1. Keep one additional copy (second location) before wiping.
1. Wipe partition table and recreate filesystem for your backup standard.
1. Example (ext4):

```bash
sudo wipefs -a /dev/sdX
sudo parted -s /dev/sdX mklabel gpt
sudo parted -s /dev/sdX mkpart primary ext4 1MiB 100%
sudo mkfs.ext4 -L LABOP_EXT_BACKUP /dev/sdX1
```

4. Mount and enforce backup policy (rotation + restore test).

## 6) Backup policy after repurpose (minimum)

- Keep at least 3 copies (working + local backup + offsite/cloud when possible).
- Schedule periodic backup and one restore test per month.
- Log backup and restore evidence in `docs/private/homelab/reports/`.

## 7) Urgency recommendation for your case

Given current P0 storage urgency, this makes sense **now**, with this sequence:

1. Triage and SMART.
1. Recover/copy (or ddrescue first if degraded).
1. Validate recovered data.
1. Only then repurpose the USB disk as external backup target.

This sequence minimizes the chance of losing old Time Machine data while still moving quickly toward a usable external backup lane.
