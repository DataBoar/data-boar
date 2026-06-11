# Homelab power and electrical planning

**Purpose:** Calculate **total power draw**, **UPS capacity**, and **circuit breaker** requirements for the homelab machines documented in [HOMELAB_VALIDATION.md](HOMELAB_VALIDATION.md) §9. This helps avoid **overload**, **tripped breakers**, and **UPS runtime** surprises.

**Related:** [HOMELAB_VALIDATION.md](HOMELAB_VALIDATION.md) · [OPERATOR_IT_REQUIREMENTS.md](OPERATOR_IT_REQUIREMENTS.md) (data center context)

### Solar / PV (if you have rooftop or grid-tied solar)

**Vendor cloud + app:** If you want **APIs** or LAN polling of the **datalogger**, see **[HOMELAB_SOLAR_MONITORING_INTEGRATION.md](HOMELAB_SOLAR_MONITORING_INTEGRATION.md)** (what the repo can/cannot do; SolisCloud vs ShineMonitor-style stacks). Keep **credentials** in **env** / Bitwarden; **non-secret** inventory in **`docs/private/homelab/`** only ([PRIVATE_OPERATOR_NOTES.md](../PRIVATE_OPERATOR_NOTES.md)).

**Cheap or offset energy bills do not replace electrical planning.** The homelab doc still focuses on **safety and reliability**:

- **Breakers, cables, outlets:** A **15 A / 20 A** branch circuit does not get “bigger” because solar lowers your utility bill. Overload still **trips the breaker** or risks overheating if you exceed **continuous** ratings (see §6).
- **UPS:** Grid-tied solar often **does not** power your sockets during a **grid outage** (unless you have **battery backup** + transfer/islanding for those circuits). **UPS sizing** (§5) still matters for short outages and clean shutdown.
- **Inverter / export limits:** Your installer may have set limits on **import/export** or main breaker; that does not remove the need to stay within **each** homelab circuit’s **amps**.
- **Optional ops tweak:** You can **time** heavy work (Docker builds, long scans) to **high solar** hours to **self-consume** and reduce grid draw—that’s economic/comfort tuning, **not** a substitute for §3–§7.

---

## 1. Machines in scope (from homelab plan)

From [HOMELAB_VALIDATION.md §9](HOMELAB_VALIDATION.md#9-multi-host-linux-optional-matrix-dns-ssh-different-distros) and [PLANS_TODO.md H1 #0](../plans/PLANS_TODO.md#h1u1-a-near-term-focus-current-billing-cycle):

| Role                                                                 | Status     | Notes                                                                                                                                                                    |
| ----                                                                 | ------     | -----                                                                                                                                                                    |
| **Primary lab / dashboard** (Ubuntu-family desktop, Docker CE/Swarm) | ✅ Active   | Desktop-class; likely **idle** most of the time unless scanning                                                                                                          |
| **Second x86_64** (Alpine Linux — musl-based, eMachines E527)         | ✅ Active   | Celeron 900, 3.8 GB RAM; low power typical; registered as 5th host ([#821](https://github.com/FabioLeitao/data-boar/issues/821)) |
| **ARM SBC** (e.g. Raspberry Pi 3)                                    | ⬜ Planned  | **Very low power** (~2–5 W idle, ~7–10 W under load)                                                                                                                     |
| **Proxmox main server** (HP ML310e Gen8–class, Xeon)                 | ⬜ Future   | **Tower server**; **highest draw** in the lab; 24/7 if it hosts long-lived services                                                                                      |
| **Legacy Intel Mac mini (mid-2011)**                                 | ⬜ Deferred | Older Mac; **moderate** (~10–20 W idle, ~30–50 W load)                                                                                                                   |
| **Spare commodity desktop** (Core i3–class)                          | ⬜ Optional | **Moderate** (~30–60 W idle, ~80–150 W load); only if you power it                                                                                                       |
| **Spare / stored laptop** (e.g. Lenovo—**optional**)                 | ⬜ Optional | Same class as **primary lab laptop** when on AC: often **~20–45 W** idle, **~45–90 W** load (varies by **CPU gen** and **GPU**); add a §3 row when you recover **model** |

**Monitors, switches, routers, etc.:** Add separately (see §3).

---

## 2. Power consumption lookup (what we need from you)

For **each** machine you plan to run, provide:

1. **Model number** (e.g. `HP ProLiant ML310e Gen8`, `Raspberry Pi 3 Model B+`, `Mac mini Mid 2011`, `Intel NUC 11`, etc.)
1. **CPU model** (if known; helps cross-check)
1. **RAM** (affects idle vs load)
1. **PSU wattage** (if visible on label; **not** the max draw, but helps sanity-check)
1. **Typical workload** for this machine:
   - **Idle** (OS running, no Data Boar scan)
   - **Light load** (Data Boar dashboard idle, small filesystem scan)
   - **Heavy load** (full database scan, Docker build, parallel workers)

## Where to find specs:
- **Server/tower:** Manufacturer spec sheet (HP, Dell, Supermicro), PSU label, or **idle/load** from reviews/forums
- **Mini-PC / NUC:** Intel/AMD spec pages, reviews (e.g. `techpowerup.com`, `servethehome.com`)
- **Raspberry Pi:** Official docs (`raspberrypi.org/documentation`) — Pi 3B+ ~2.5 W idle, ~7 W load
- **Mac mini:** Apple support pages or `everymac.com` (mid-2011 i5/i7: ~10–15 W idle, ~30–50 W load)
- **Desktop:** PSU label (e.g. `450W 80+ Bronze`) is **capacity**, not draw; measure with **Kill-A-Watt** or estimate from CPU TDP + GPU

**If you have a Kill-A-Watt or smart plug:** measure **idle** and **load** directly—that’s the most accurate.

---

## 3. Power calculation template (fill in per machine)

Copy this table and fill **one row per machine**:

| Machine role         | Model                       | CPU            | RAM    | PSU (W) | **Idle (W)**         | **Light load (W)**   | **Heavy load (W)**   | Notes               |
| ------------         | -----                       | ---            | ---    | ------- | ------------         | ------------------   | ------------------   | -----               |
| Primary (Linux lab)  | *[your model]*              | *[CPU]*        | *[GB]* | *[W]*   | *[measured or spec]* | *[measured or spec]* | *[measured or spec]* | Docker Swarm on     |
| Second x86_64 (musl) | eMachines E527              | Celeron 900    | 3.8 GB | ~65 W   | ~15 W                | ~25 W                | ~45 W                | Alpine Linux; musl; 5th lab host |
| ARM SBC (Pi)         | *[model]*                   | *[CPU]*        | *[GB]* | *[W]*   | *[W]*                | *[W]*                | *[W]*                |                     |
| Proxmox tower        | *[HP ML310e Gen8 or model]* | *[Xeon model]* | *[GB]* | *[W]*   | *[W]*                | *[W]*                | *[W]*                | 24/7 if main server |
| Mac mini 2011        | *[Mid 2011]*                | *[i5/i7]*      | *[GB]* | *[W]*   | *[W]*                | *[W]*                | *[W]*                | Deferred            |
| Spare i3 desktop     | *[model]*                   | *[i3 model]*   | *[GB]* | *[W]*   | *[W]*                | *[W]*                | *[W]*                | Optional            |

**Other devices** (add rows):

| Device                      | Model     | **Typical draw (W)** | Notes           |
| ------                      | -----     | -------------------- | -----           |
| Monitor (primary)           | *[model]* | *[W]*                | Only when on    |
| Monitor (secondary, if any) | *[model]* | *[W]*                |                 |
| Network switch              | *[model]* | *[W]*                | 24/7            |
| Router / gateway            | *[model]* | *[W]*                | 24/7            |
| UPS (self-consumption)      | *[model]* | *[W]*                | ~5–15 W typical |
| Other (NAS, printer, etc.)  | *[model]* | *[W]*                |                 |

---

## 4. Total power calculation

## Scenarios:

### Scenario A: “All machines running, light load” (typical day)
- Sum **idle** for machines that are **always on** (e.g. Proxmox tower if 24/7, switch, router)
- Sum **light load** for machines doing **Data Boar scans** (e.g. primary, musl, Pi)
- Add **monitors** if on
- Add **UPS self-consumption**

## Total A = _____ W

### Scenario B: “All machines running, heavy load” (worst case)
- Sum **heavy load** for all machines that can run simultaneously
- Add **monitors** if on
- Add **UPS self-consumption**

## Total B = _____ W

### Scenario C: “Minimal (only essentials)”
- Proxmox tower (if 24/7) **idle**
- Switch + router
- UPS self-consumption
- **No** monitors, **no** other machines

**Total C = _____ W** (baseline 24/7 draw)

---

## 5. UPS sizing

## Formula (UPS VA):

```
UPS capacity (VA) ≥ Total power (W) / Power factor
```

**Power factor** (typical):

- **Servers / desktops:** 0.8–0.9 (use **0.85** as safe default)
- **Raspberry Pi / low-power:** 0.95–1.0 (use **0.95**)
- **Mixed load:** Use **0.85** for safety

## Example:
- Total draw = 300 W
- Power factor = 0.85
- **Minimum UPS = 300 / 0.85 = 353 VA** → round up to **≥400 VA** or **≥500 VA**

**Runtime:** UPS spec sheets list **runtime at X% load**. For **5–10 minutes** of graceful shutdown:

- Check UPS datasheet: “Runtime at 50% load = Y minutes”
- If your **Total A** is ~50% of UPS capacity, you get that runtime
- If you need **longer runtime** (e.g. 30+ minutes), size UPS for **lower % load** or buy a larger unit

**Recommendation:** Size UPS for **Scenario B (worst case)** with **20–30% headroom**:

```
UPS VA ≥ (Total B × 1.25) / 0.85
```

**Example:** Total B = 400 W → UPS ≥ (400 × 1.25) / 0.85 = **588 VA** → choose **≥600 VA** or **≥750 VA**

### 5.1 Installed UPS: Intelbras **Attiv 1500 VA** (120 V → 120 V, monovolt)

You reported this **nobreak** powers **everything today**. For the homelab **energy budget**, the limiting number is usually **watts (W)**, not VA alone.

**Typical manufacturer-class specs for the Attiv 1500 VA line** (confirm on your **nameplate** and [Intelbras datasheet](https://backend.intelbras.com/sites/default/files/2022-03/ATTIV%201500%20VA%20BI%20-%20Datasheet_0.pdf) for your exact SKU—BI/monovolt variants exist):

| Spec                      | Typical value                                                 | Planning note                                                                                        |
| ----                      | -------------                                                 | -------------                                                                                        |
| **Nominal**               | **1500 VA**                                                   | Marketing headline                                                                                   |
| **Active power (W)**      | Often **~750 W** max sustained (datasheet: power factor ~0.5) | **Sum of all loads** plugged into the nobreak should stay **below this** with margin                 |
| **Outlets**               | **8** (NBR 14136, often **10 A** per socket)                  | Many plugs ≠ more **W**—the **750 W** class cap still applies to **total** load                      |
| **Topology**              | **Line-interactive**                                          | Good for brownouts; not the same as **online/double-conversion**                                     |
| **Battery mode waveform** | Often **modified / stepped sine**                             | Most PCs/switches OK; some picky **active PFC** PSUs can misbehave—watch for buzz/root on transfer |
| **Batteries**             | Often **2 × 12 V 7 Ah**                                       | **Runtime drops fast** above ~50% of rated W—plan for **short** ride-through + graceful shutdown     |

## Practical budget (this nobreak):

- Treat **~750 W** as the **hard ceiling** for everything on the Attiv (unless your label says a higher W—use the label).
- For **headroom** (inrush, aging batteries, alarm margin), aim **≤ ~600 W** sustained on that unit (**~80%** of 750 W).
- **Self-consumption** of the nobreak itself is small but non-zero—include it if you measure tightly.

## Why upgrades may be recommended as the lab grows:

1. **Proxmox tower + desktop + monitors + networking + LG split on the same circuit path** — If the **compressor** or **servers** spike together, you may **overload** the nobreak (beep/overload) even if the **wall breaker** is fine. **Operator-reported:** your **LG split** is on a **dedicated ~220 V** breaker **separate** from the **rest of the room**—that **avoids** stacking **compressor + lab** on one **customer branch** (see §8.2.1). The **Attiv** is still **120 V** class; keep **outdoor AC** off that nobreak.
1. **Large homelab on one 750 W UPS** — Runtime during outage may be **only a few minutes** at high load; not enough for orderly shutdown of many hosts.
1. **Air conditioner** — Many operators keep **split AC on utility power** (dedicated breaker), not on a small desktop UPS, unless using a **much larger** UPS/inverter designed for motor loads. **Do not** assume the Attiv should carry the outdoor unit.

## Reasonable upgrade / split strategies (discuss with electrician + budget):

| Approach                                 | When it helps                                                                                                                                        |
| --------                                 | -------------                                                                                                                                        |
| **Keep Attiv for “critical small load”** | e.g. **LAB-ROUTER-01-SE + core switch + one workstation** or **one server**—stay under **~600 W**                                                              |
| **Second nobreak / UPS**                 | Move **desktop OR tower** to a **second** UPS, or put **non-critical** loads on **surge-only** strips from the wall (not battery)                    |
| **Higher-power online UPS** for servers  | If you need **clean sine**, **higher W**, and **longer** runtime on the **tower**                                                                    |
| **Dedicated wall circuit for AC**        | Reduces competition with lab gear on the **same** customer-side path; see §8                                                                         |
| **UniFi SmartPower path** (see §5.2)     | Move **LAB-ROUTER-01-SE** (and optionally other UniFi gear) off the **Attiv** onto Ubiquiti’s **DC backup** stack—**frees W** on the Intelbras for PCs/servers |

**Action:** Add a row in §3 **Other devices**: `Intelbras Attiv 1500VA` — **self / alarm load** if known; and list **every** device currently plugged into it with **measured W** (Kill-A-Watt) so **Total B** can be compared to **~750 W**.

### 5.2 Offloading the Dream Machine SE: UniFi power vs a **second** nobreak

**Goal:** Your **Attiv ~750 W** budget is tight. If the **LAB-ROUTER-01-SE** (and maybe a **switch**) sit on the Attiv today, moving them to **another** backup path **frees watts** on the Attiv for **desktops / Proxmox tower / monitors**.

## Option A — UniFi ecosystem (integrated with LAB-ROUTER-01-SE)

Ubiquiti documents **SmartPower** redundancy for rack/pro gateways. For **LAB-ROUTER-01-SE** specifically, the Help Center lists **up to 220 W @ 52 V DC** on the SmartPower port (not the same as 12 V models). See **[Power Redundancy](https://help.ui.com/hc/en-us/articles/360042834933-Power-Redundancy)** for the compatibility table and architecture cases.

| Product direction                                                      | Role                                                                                                                    | Notes                                                                                                                                                                                                                                                                                                                                                                                                                                       |
| -----------------                                                      | ----                                                                                                                    | -----                                                                                                                                                                                                                                                                                                                                                                                                                                       |
| **USP-RPS** (Redundant Power / SmartPower backup unit) + **USP-Cable** | Supplies **52 V DC** to the LAB-ROUTER-01-SE’s SmartPower port when negotiated; unit has its **own AC input** and internal backup | **Removes gateway load from the Attiv** if you unplug the LAB-ROUTER-01-SE from the Intelbras and rely on **RPS + normal AC** per Ubiquiti wiring. You still need a **wall outlet** for the RPS (ideally **another circuit** or at least **not** everything daisy-chained on one strip). RPS can serve **multiple** compatible devices up to its **total DC budget**—plan ports if you also protect **PoE switches** (see table in Ubiquiti article). |
| **UniFi UPS** (rack **UPS 2U** and related)                            | Marketed as part of the **SmartPower** story; check **store.ui.com** for current SKUs and **your** region’s voltage     | Before buying, read **current** release notes / forums for **LAB-ROUTER-01-SE + smart shutdown** behaviour—capabilities depend on **UniFi OS / Network** versions. Treat marketing pages as **verify-before-purchase**.                                                                                                                                                                                                                               |
| **Mission Critical PoE switch** (Ubiquiti)                             | Battery-backed **PoE** plus a small number of **AC outlets** for **modem / gateway** class gear                         | Useful if you want **UPS + PoE** in one box; confirm **120 V** Brazil operation and **total W** vs your modem + mini-loads.                                                                                                                                                                                                                                                                                                                 |

## Option B — Generic second nobreak (non-UniFi)

- A **second** **600–900 W** (real watts on label) line-interactive UPS dedicated to **“network core”**: **LAB-ROUTER-01-SE + switch + modem** only.
- **Pros:** Often **cheaper** than full UniFi stack; simple; Attiv keeps **PC + server** only.
- **Cons:** No **single** UniFi UI for power state; you manage two batteries and two beep policies.

## Electrical reality check

- A **UniFi RPS/UPS** still plugs into **AC**. You **free the Attiv’s 750 W budget**, but you add **another** device that needs an **outlet** and possibly **another breaker headroom** on the same room circuit—see §6.
- **Watt estimation:** Measure **LAB-ROUTER-01-SE + switch** on a Kill-A-Watt today; that’s roughly what you **move off** the Attiv.

## Recommendation framing

- If you want **tight integration** and may add **SmartPower-capable switches/NVR** later, **USP-RPS + cable** is the **logical** UniFi-native way to **stop feeding the gateway from the Attiv**.
- If you only need **“second small UPS for router stack”**, a **good second nobreak** is **fine** and may be **easier on budget**.

---

## 6. Circuit breaker / outlet capacity

**Voltage:** Assume **120 V** (North America) or **230 V** (Europe/Brazil). If unsure, check your outlet or breaker panel label.

## Formula (circuit current):

```
Max current (A) = Total power (W) / Voltage (V)
```

**Safety margin:** Circuit breakers are rated for **80% continuous load** (NEC / local code). For a **15 A** breaker:

- **Max continuous = 15 A × 0.8 = 12 A**
- At **120 V:** 12 A × 120 V = **1,440 W max**
- At **230 V:** 12 A × 230 V = **2,760 W max**

## For 20 A breaker:
- **Max continuous = 20 A × 0.8 = 16 A**
- At **120 V:** 16 A × 120 V = **1,920 W max**
- At **230 V:** 16 A × 230 V = **3,680 W max**

## Check your breaker:
1. Find the **circuit** that powers your lab outlets
1. Read the **breaker rating** (e.g. `15 A`, `20 A`)
1. Calculate: **Total B (W) / Voltage (V) = _____ A**
1. Ensure: **_____ A ≤ (Breaker A × 0.8)**

**Dedicated high-voltage AC circuit (common in Brazil):** If the **split HVAC** is on its **own ~220 V** breaker **separate** from **general room outlets** (127/220 layout), **do not** add the **compressor current** to the **lab outlet** breaker math—those are **different branches**. You still care about **total home** draw for **utility / solar**, but **§4–§6** for “will my lab trip the breaker?” uses the **lab circuit** only.

## If overloaded:
- **Option 1:** Split machines across **multiple circuits** (different breakers)
- **Option 2:** Upgrade breaker (requires **electrician**; may need thicker wire)
- **Option 3:** Reduce simultaneous load (power down optional machines during heavy scans)

---

## 7. Outlet count

## Typical outlets per circuit:
- **15 A circuit:** ~8–10 outlets (code allows more, but **don’t load all at once**)
- **20 A circuit:** ~10–12 outlets

## Per machine:
- Each machine needs **1 outlet** (or a **power strip** with surge protection)
- **Monitors** share strips with their machines (common)
- **UPS** plugs into wall; machines plug into **UPS outlets** (count UPS outlets vs machines)

## If you run out of outlets:
- Use **power strips** (with surge protection) plugged into wall outlets
- **Don’t daisy-chain** strips (safety risk)
- **Don’t exceed** strip rating (usually **15 A** or **1,875 W at 125 V**)

---

## 8. Thermal comfort and cooling (hot climate + split AC)

**Why this is in the homelab plan:** In **warm, humid** coastal climates (e.g. **Niterói / RJ**), room temperature affects **people**, **electronics**, and **electrical load**. Cooling is not optional for a **comfortable** lab and helps **reliability**.

### 8.1 Heat and equipment

- **CPUs and PSUs** throttle or shorten life if intake air is too hot; **tower servers** (e.g. future Proxmox host) move a lot of air—don’t trap them in a **closed cabinet** without exhaust.
- **Hard drives** and **UPS batteries** age faster above ~25–30 °C sustained; keep the **UPS** in the same cooled space you care about, not a baking closet.
- **Humidity:** normal coastal humidity is fine if condensation is avoided (avoid cold surfaces + warm moist air); follow AC manufacturer guidance for **drainage** and **filters**.

### 8.2 Split AC (your LG unit)

**Mini-split / split inverter** systems have at least:

- **Outdoor unit** (compressor + fan) — often the **largest** single load in the room’s electrical picture when cooling hard.
- **Indoor unit** (fan + electronics) — smaller, but continuous when the system runs.

#### 8.2.1 Dedicated 220 V circuit (operator-reported)

You reported the **LG split** is on a **dedicated ~220 V** **circuit breaker**, **electrically separated** from the **rest of the room** (general outlets / lab path).

## Why this matters:

| Topic                  | Effect                                                                                                                                                                                        |
| -----                  | ------                                                                                                                                                                                        |
| **Breaker overload**   | **Lab** machines + **monitors** + **Attiv** are evaluated against **their** branch; the **AC compressor** does **not** add amps to **that** same breaker.                                     |
| **UPS (Attiv)**        | Still **do not** connect the **outdoor unit** (or whole split) to a **small desktop UPS**—motor/inrush and **voltage** (often **220 V** branch) are wrong tool for a **120 V** class nobreak. |
| **Comfort / thermals** | Unchanged: cooling still drives **room** conditions for **people** and **gear**; you just avoid **one** failure mode where **AC + servers** fight for one **15–20 A** socket circuit.         |
| **Utility / solar**    | Whole-house **kWh** still includes **both** circuits; **§4** “Scenario B” for **billing** awareness can note **AC nameplate W** separately from **lab W**.                                    |

Record **breaker rating (A)** for the **AC** branch in **`docs/private/homelab/`** if you want a full **panel picture**—**do not** commit **panel photos** or **exact** domestic wiring details to the **public** repo ([PRIVATE_OPERATOR_NOTES.md](../PRIVATE_OPERATOR_NOTES.md)).

**For power planning (§3–§6):** add a row under **Other devices**:

| Device        | Model                    | **Typical draw (W)** | Notes                                            |
| ------        | -----                    | -------------------- | -----                                            |
| Split AC (LG) | *[model from nameplate]* | *[see below]*        | Cooling + dehumidification; peak in mid-day heat |

**What to copy from the nameplate / manual** (when you locate the LG model):

1. **Model number** (indoor + outdoor if different) — we can cross-check **cooling capacity (BTU/h or kW)** and **electrical input**.
1. **Rated voltage** and **maximum current (A)** or **input power (W)** for the **outdoor** unit — use for **utility / solar** “worst day” awareness. If the split is on a **dedicated** breaker **separate** from lab outlets (§8.2.1), you **do not** sum **compressor amps** into the **lab** breaker check.
1. **SEER / efficiency class** — higher SEER/inverter units use **less kWh** for the same comfort (aligns with **solar self-consumption**).

## Electrical recommendation (generic, not a substitute for your electrician):

- If the **AC** and **several servers** are on the **same** **15 A** circuit, **summer peaks** can trip the breaker—prefer a **dedicated circuit** for the AC per local code/installer practice.
- **Inverter:** when the compressor starts, **inrush** is lower than old fixed-speed units, but **continuous** W still matters for §6.

**Comfort / capacity (high level):** Manufacturer specs list **nominal cooling kW or BTU/h** vs **room area** (m²). If the room grows (more towers, racks), **heat load** from IT can be **hundreds of watts**—that reduces effective margin for **solar gain** and **people**. If scans are **CPU-heavy** for hours, treat that as extra heat; **good airflow** (front intake / rear exhaust) reduces reliance on AC alone.

### 8.3 Cheap wins (before upsizing AC)

- **Clean / replace** indoor filters on schedule; keep **outdoor coil** unobstructed.
- **Cable management** and **clear fan paths** on servers and desktops.
- **Run heavy jobs** when the room is already cool (morning / night) if that fits your routine and **tariff/solar** profile.

When you have the **LG model number(s)**, paste them (and your **room rough size** if you want) and we can align **nameplate W** with **§4 scenarios** and flag **same-circuit** risks.

---

## 9. What to send back (for calculation help)

1. **Filled table** from §3 (model numbers, measured or spec power)
1. **Your voltage** (120 V or 230 V)
1. **Breaker rating** for the lab circuit (e.g. `15 A`, `20 A`) — and whether **AC shares** that circuit
1. **Current nobreak/UPS:** **Intelbras Attiv 1500 VA 120 V** (installed)—confirm **W** on label; list **all** loads plugged into it (see §5.1)
1. **Which machines run 24/7** vs **on-demand**
1. **LG split model** (indoor/outdoor) and, if visible, **plate A or W** (§8.2)

Then we can:

- Calculate **Total A, B, C**
- Recommend **UPS size** (VA + runtime check)
- Verify **breaker capacity** (A vs max continuous)
- Suggest **outlet / strip** layout
- Flag **overload risks** (including **AC + lab** on one circuit)

---

## 10. Example (placeholder — replace with your data)

| Machine        | Model                                                     | Idle (W)   | Light (W)       | Heavy (W)     |
| -------        | -----                                                     | --------   | ---------       | ---------     |
| Primary laptop | *Your* Linux lab notebook (see §10.1 — **generic** class) | *~20–35*   | *~40–70*        | *~60–90*      |
| Proxmox tower  | *Your* tower model (e.g. **ML310e Gen8–class**)           | *[lookup]* | *[lookup]*      | *[lookup]*    |
| Pi 3           | Raspberry Pi 3B+                                          | ~2.5       | ~5              | ~7            |
| LG split AC    | *[model]*                                                 | *[plate]*  | *[typical run]* | *[peak cool]* |

**Total A (light):** *[calculated after you fill]*
**Total B (heavy):** *[calculated]*
**UPS recommendation:** *[calculated]*
**Breaker check:** *[calculated]*

### 10.1 Primary lab laptop (illustrative **class** — not your exact SKU)

**Public doc:** Describes a **common** pattern: **Ivy Bridge–era** (or similar) **14"** business notebook (~2012), often **8 GB RAM** ceiling, **Ubuntu-family** desktop, used as **primary** homelab GUI host. **Exact make, model, serial, hostname** → **`docs/private/homelab/`** only ([PRIVATE_OPERATOR_NOTES.md](../PRIVATE_OPERATOR_NOTES.md)).

| Topic            | Notes                                                                                                                                                                                               |
| -----            | -----                                                                                                                                                                                               |
| **AC adapter**   | Many vendors shipped **65 W** (iGPU) or **90 W** (dGPU) class bricks—**90 W** is a **ceiling**, not typical draw. Planning: assume **≤ ~90 W** from the nobreak for this machine at **worst case**. |
| **Typical draw** | **Idle/light desktop:** often **~20–45 W**; **CPU + disk busy** (scan/build): **~50–90 W** depending on GPU, screen brightness, and battery charging. **Measure** with a Kill-A-Watt for your unit. |
| **RAM / disk**   | **DDR3** generation often tops out around **8 GB**; **SSD** (SATA) strongly recommended for desktop + `uv`/Docker responsiveness.                                                                   |
| **Thermal**      | Older chassis: clean fans/heatsink; sustained **100% CPU** scans may throttle—acceptable for lab validation, not a throughput record.                                                               |
| **Attiv budget** | **One** primary laptop + **LAB-ROUTER-01-SE** + **switch** + **monitor** can approach **Intelbras ~750 W** limits if a **tower** is added—see **§5.1** and **§5.2** (offload gateway to RPS / second UPS).    |

---

**Português (Brasil):** [HOMELAB_POWER_AND_ELECTRICAL_PLANNING.pt_BR.md](HOMELAB_POWER_AND_ELECTRICAL_PLANNING.pt_BR.md)
