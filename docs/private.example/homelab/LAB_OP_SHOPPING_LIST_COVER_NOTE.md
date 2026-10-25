# Lab-op shopping list + power planning — private note

**The full document** (priorities, indicative BRL prices with timestamps, store hints, RAM (primary dev PC), Pi/Mac/UPS/power wall, sequencing) lives **only** in the operator workspace:

- **`docs/private/homelab/LAB_OP_SHOPPING_LIST_AND_POWER.md`** (gitignored — **never** commit)

## Add-on wishlist (operator): biometrics (fingerprint / face)

If you want “Windows Hello-like” authentication on Linux hosts (login/unlock/polkit/sudo where applicable), keep the **real** rows (device models, USB IDs, what worked per OS/kernel) in the private shopping list under `docs/private/`.

Tracked reference only (no prices, no store links): `docs/ops/LAB_OP_SHOPPING_LIST_EXAMPLE.md` (biometrics section).

**Urgent (operator):** Section **§0** requires **photos** of the utility meter (Enel / limits), **main house circuit breaker**, and **floor distribution panel** where the lab is fed. **Optional:** another-floor panel (living/kitchen) if you want a full map; **optional** appliance labels (fridge, chest freezer; occasional washer/microwave) for rough **W** — see private file **§0** table. Without the **meter** (and lab-panel context already captured), UPS sizing and Enel load requests stay **unsafe to guess** for “official” numbers.

**Optional (operator):** Section **§11** — **pCloud lifetime** upgrade / promo **TCO** (USD per TB·GB·MB, vs current **500 GB** quota, sync backup notes). **No** email or account identifiers in the tracked repo; **only** in the private copy.

**Optional (operator):** Section **§9** (after the in-service **Intelbras** UPS) — **stabilized isolation module** (not a battery UPS) + **×2** stored **NHS Compact Pro 1200** units (battery replacement / NHS service vs **plan B** new UPS). Shopping rows **B1/B2** in the private file **§3**.

## Tracked references (no prices):

- Electrical planning playbook: [HOMELAB_POWER_AND_ELECTRICAL_PLANNING.md](../../ops/HOMELAB_POWER_AND_ELECTRICAL_PLANNING.md) ([pt-BR](../../ops/HOMELAB_POWER_AND_ELECTRICAL_PLANNING.pt_BR.md))
- Lab sequencing: [PLAN_LAB_FIREWALL_ACCESS_AND_OBSERVABILITY.md](../../plans/PLAN_LAB_FIREWALL_ACCESS_AND_OBSERVABILITY.md)

After copying this structure, keep **all live prices and CEP-specific notes** in **`docs/private/`** only.
