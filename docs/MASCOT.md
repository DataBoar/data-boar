# Data Boar mascot assets

Branding images (colored and black & white, with white or transparent backgrounds). Used in the web app, README, and documentation. Assets live in **api/static/mascot/**.

## Brand narrative: minors and the boar metaphor

The **boar** stands for stubborn, deep search in messy “data soup.” That same metaphor maps to **child- and minor-related inventory**: the application elevates **possible minor** signals with dedicated detection and report language (not a buried checkbox next to generic PII), so governance teams see those rows **early**—aligned with LGPD Art. 14 / GDPR Art. 8-style urgency, without pretending to verify parental consent in software. Mascot surfaces (README hero, dashboard headers, Excel **Report info**) stay consistent with that positioning; technical limits live in [MINOR_DETECTION.md](MINOR_DETECTION.md) ([pt-BR](MINOR_DETECTION.pt_BR.md)).

## Copyright and license

The Data Boar mascot assets in `api/static/mascot/` are **original artwork** created for this project (or commissioned with full rights assigned to the project). They are **copyright-safe** for use as the application logo and branding: no third-party clip art or unlicensed stock art is used. The assets are part of the repository and are covered by the same **BSD 3-Clause License** as the rest of the project (see the root [LICENSE](../LICENSE)). You may use, modify, and redistribute them in accordance with that license when distributing or deriving from this project.

## Current set (2026-11)

The canonical source of the current art is the public site repository (`images/`); the product keeps byte-identical copies in **api/static/mascot/**. Placement rule: a small **face mark** on every screen; a **large illustration only** on the About page, the empty Reports state and the idle dashboard; working screens carry only the small mark.

| File | What it is | Used in |
| ---- | ---------- | ------- |
| `mascot-pot.png` | boar with the soup pot (tusk fixed) | About page |
| `mascot-hero.png` | the boar alone | idle dashboard (hidden while a scan runs) |
| `data-soup-pot.png` | the pot and steam alone | Reports page, empty state |
| `mascot-mark-face.png` | the face (mark) | small anchor in the heading of every page and in the dashboard footer |
| `favicon-32.png`, `icon-192.png`, `apple-touch-icon.png` (and `api/static/favicon.ico`) | favicon set | `base.html` |

Everything listed under **Files** below is the **previous art** (the original SVG and its derivatives). It is kept for lineage and still feeds the Excel report and heatmap (see below); no dashboard template uses it any more. `scripts/build_favicon.py` still builds a favicon from that legacy art: do not run it to replace the current favicon.

## Files

| File                                      | Description          | Suggested use                                              |
| ------                                    | -------------        | ----------------                                           |
| `data_boar_mascote_color.svg`             | Color vector         | **Primary:** About page, web UI, docs, README; scales to any size. README uses this SVG so GitHub light/dark themes both look correct. |
| `data_boar_mascote_bw.svg`                | Black & white vector | Print, dark backgrounds, or minimal branding.              |
| `data_boar_mascote_color_translucent.png` | Color, transparent   | Legacy/alternate raster; older favicon source.             |
| `data_boar_mascote_color_translucent_not_zombie.png` | Color, transparent (dark-tuned) | **Favicon** PNG in `base.html`, `build_favicon.py` source; better on dark browser chrome than the plain translucent export. |
| `data_boar_mascote_color_translucent_not_zombie_half.png` | Same, half-size export | Optional; same use as above if you standardise on this asset size. |
| `data_boar_mascote_bw_translucent.png`    | B&W, transparent     | Favicon or header when a neutral icon is preferred.        |
| `data_boar_mascote_color_full.png`        | Color, full (opaque) | Reports, PDFs, or where a solid background is needed.      |
| `data_boar_mascote_bw_full.png`           | B&W, full            | Same, B&W variant.                                         |
| `data_boar_mascote_bw_core.png`           | B&W core             | Alternate compact icon.                                    |
| `data_boar_mascot_original.png`           | Original source      | Reference; use derived assets above in the app.            |

All paths below are relative to the repository root. The assets are in **api/static/mascot/**.

## Where they are used in the project

- **Favicon (browser tab):** `base.html` → `favicon.ico`, `favicon-32.png`, `icon-192.png` and `apple-touch-icon.png` (current set, see above). `scripts/build_favicon.py` is legacy.
- **About page:** `about.html` → `mascot-pot.png` (large) and the face mark in the heading.
- **Dashboard / Reports / Config / Help:** each page uses the face mark (40×35) in the main heading, and the dashboard also in the attribution block (32×28). Reports shows `data-soup-pot.png` when there are no sessions; the dashboard shows `mascot-hero.png` while idle.
- **README (GitHub / IDE preview):** `![Data Boar mascot](https://databoar.com.br/images/mascot-pot.png)` (EN and pt-BR), centered. The URL is pinned by `tests/test_docs_markdown.py`.
- **Docs:** Use the same SVG or PNG where the Data Boar logo is shown (naming checklist history: archived under `docs/plans/completed/` in the repo tree).
- **Excel report:** The Report info sheet includes a small mascot (48×48 px) at D1; generated by `report/generator.py` from `data_boar_mascote_color_full.png`.
- **Heatmap PNG:** The sensitivity/risk heatmap image includes a small mascot in the lower-right corner (8% size); same source PNG.
- **Heatmap data sheet:** The same heatmap PNG is embedded in the Excel "Heatmap data" sheet below the raw data table, scaled to fit one page (letter/A4) when printed.

## Favicon

`api/static/favicon.ico` is generated from the dark-tuned translucent mascot PNG (16×16 and 32×32). To regenerate after changing the mascot:

```bash
uv run python scripts/build_favicon.py
```

## Manual conversion (if you prefer)

- **Inkscape (Windows):** Open `data_boar_mascote_color.svg` → File → Export PNG Image → set width/height 32 → Export. Then in GIMP: open the PNG → Image → Scale to 32×32 and 16×16, export as `.ico` (GIMP can save as ICO with multiple layers/sizes), or use a site/tool to combine two PNGs into one ICO.
- **GIMP:** Open `data_boar_mascote_color_translucent_not_zombie.png` → Image → Scale Image to 32×32; duplicate layer, scale to 16×16; File → Export As → `favicon.ico` (choose ICO and include both sizes if the export dialog allows).
- **ImageMagick (Linux):** `convert api/static/mascot/data_boar_mascote_color_translucent_not_zombie.png -resize 32x32 -resize 16x16 api/static/favicon.ico` (or use `magick` and create 16 and 32 in one ICO: see `magick convert -help` for multi-size ICO). Simpler: `magick api/static/mascot/data_boar_mascote_color_translucent_not_zombie.png -define icon:auto-resize=16,32,48 api/static/favicon.ico`.
