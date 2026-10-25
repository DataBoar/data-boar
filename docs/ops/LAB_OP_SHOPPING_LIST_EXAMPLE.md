# Lab-op shopping list (example, tracked)

This is a **public, tracked** example shopping list that demonstrates how we structure hardware planning **without** leaking operator-specific pricing, store links, CEP/location hints, serials, or home/lab identifiers.

## Principles

- **Track categories and rationale**, not live prices.
- **Prefer compatibility facts** (DDR generation, voltage, speed, rank) over “best deal” links.
- Keep the **real** shopping plan in `docs/private/` (gitignored).

## Full structure (how to think about “everything”)

In the real lab, the shopping list is a **master map** spanning:

- hosts (laptops/servers/SBCs) + upgrades (RAM/SSD)
- storage + backup strategy
- networking (LAB-ROUTER-01/switch/APs) + redundancy
- power (UPS, circuit capacity) + solar + monitoring
- HVAC/environment (cooling, sensors)
- physical/operational safety (spares, labeling, tooling)
- software/services: licenses, subscriptions, tokens, training

We keep that master plan in a private file (gitignored) so it can contain real prices, store links, and local constraints.

## Example: RAM upgrade planning (generic)

### Identify your target

- **Laptop model**: ThinkPad *L-series (14-inch class)* / *LAB-NODE-01* (exact generation matters)
- **Goal**: e.g. 16→32 GiB, 16→64 GiB, dual-channel, low-power idle, stability

### Checklist to collect before buying

- Current RAM layout: 1× or 2× modules, soldered + slot, max supported
- DDR generation (DDR4 vs DDR5)
- SODIMM vs soldered-only (varies by generation)
- Speed target: match the platform default (avoid overpaying for clocks you can’t use)
- Voltage and JEDEC profile (avoid “XMP-only” kits for laptops)

### Example bill of materials (no prices)

- **RAM**: 2×16 GiB or 2×32 GiB SODIMM kit (JEDEC, laptop-friendly)
- **Tools**: small Phillips, spudger, ESD strap (optional), tray for screws
- **Validation**: `memtest86+` / `memtester`, and a short stress run after install

## Where the real plan lives

- Tracked decision spine (no prices): `docs/plans/PLAN_LAB_OP_CAPEX_OPEX_AND_PROCUREMENT.md`
- Private cover note (tracked): `docs/private.example/homelab/LAB_OP_SHOPPING_LIST_COVER_NOTE.md`
- Real list (gitignored): `docs/private/homelab/LAB_OP_SHOPPING_LIST_AND_POWER.pt_BR.md`

## Example: Biometrics (fingerprint / face) for Linux hosts (generic)

### Goal (operator UX)

- Use biometrics (at least **fingerprint**) in Linux in a “Windows Hello-like” way where possible:
  - login / unlock
  - (optionally) polkit prompts
  - (optionally) sudo (see caution)

### Compatibility checklist (before buying or assuming it works)

- **Identify the device**:
  - built-in laptop reader: `lsusb` (or `lspci` if internal) to get the vendor:product ID
  - USB reader: `lsusb` to get the vendor:product ID
- **Check support**: `libfprint` supported devices list:
  - `https://fprint.freedesktop.org/supported-devices.html`
- **Enroll & verify** (on a Linux host):
  - install `fprintd` + PAM integration
  - run `fprintd-enroll` and `fprintd-verify`

### Example “shopping rows” (no prices, no store links)

- **USB fingerprint reader**: pick a model explicitly supported by `libfprint` (confirm by USB ID).
- **Spare input**: enroll multiple fingers (thumb + index) to avoid lockouts.
- **Webcam / IR camera**: face recognition on Linux exists but is less standardized than fingerprints; treat as “nice-to-have” unless you’re ready to maintain it.

### Caution (security posture)

- For admin elevation (`sudo`), prefer keeping the **password requirement** as the baseline, and treat fingerprint as convenience only if you accept the trade-offs (e.g., shoulder-surfing vs biometric spoofing vs auditability).

