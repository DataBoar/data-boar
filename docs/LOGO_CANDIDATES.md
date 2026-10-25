# Logo candidates (Compliance Crawler)

This document describes **logo variants** held in **api/static/logo-candidates/** while the final mark is chosen. The selected file will be copied to `api/static/logo.svg` (and PNG/favicon exports) for use in the app.

## Refinements applied across variants (except v0)

- **No blue bleed:** The C is drawn as a single **path** (thick arc), not a circle + white rectangle, so there is no overlap or edge bleed.
- **Cream "paper":** Background uses off-white/cream (`#faf6ef`) with subtle **notepad lines** (`#e8e2d8` / `#e5dfd4`) to suggest office/stationery.
- **Database-like teal symbol:** Teal element is either a **table** (rows/lines), a **cylinder**, or a **table with header** to better match "scanning databases/tables."
- **Scan metaphor:** Different treatments for the "scan" idea:
- **v1** – Radar sweep (semi-transparent arc).
- **v2** – Laser beams (sharp lines, optional secondary beams).
- **v3** – Crawler (dashed rays + small "node" dots).
- **v4** – Strong radar (wider sweep arc).

## Files

| File                              | Description                                                                                                                                                                                                                             |
| ------                            | -------------                                                                                                                                                                                                                           |
| **v0-original.svg**               | First sketch: white rect "cut" C, simple teal block, basic scan lines. Kept for reference.                                                                                                                                              |
| **v1-cream-notepad-radar.svg**    | Cream notepad, path C, teal database cylinder, **radar dish silhouette** (dish + feed + stand) with semi-transparent sweep, **ID-style document** (driver license–like) with **paper clip** on the sheet (PII/sensitive data metaphor). |
| **v2-cream-laser-db.svg**         | Cream + notepad, path C, teal **database cylinder**, laser-style sharp lines.                                                                                                                                                           |
| **v3-cream-crawler-db.svg**       | Cream + notepad, path C, teal table with header row, **dashed rays + dots** (crawler).                                                                                                                                                  |
| **v4-cream-radar-table.svg**      | Cream + notepad, path C, teal table with header, **wide radar sweep** (double arc).                                                                                                                                                     |
| **v5-cream-scan-docs-floppy.svg** | **Left = scan/crawler** (radar dish + sweep). **Right = documents** (cream notepad, ID card, paper clip). No cylinder or floppy; clean base to iterate from.                                                                            |
| **v6-leitao-piglet.svg**          | **Leitao (piglet)** theme: cute pig head 3/4 view, pink/coral palette, scent trail from the left (truffle/data metaphor). Identity + crawler + data idea.                                                                               |
| **v7-javali-data-soup.svg**       | **Javali (wild boar)** theme: cute cartoon javali with tusks and bristly mane, facing right toward a **pot of data soup** almost out of frame. Friendly mascot, data-as-soup metaphor.                                                  |

All variant SVGs use **ASCII-only** text in `<title>` and `<desc>` (e.g. hyphen `-` instead of en-dash) so they parse correctly in browsers and XML validators; control characters in SVG can cause "PCDATA invalid Char value" errors.

## Next steps

1. Choose one variant (or request tweaks).
1. Copy the chosen SVG to `api/static/logo.svg`.
1. Export PNG (32 px, 64 px) and favicon (16/32 PNG or ICO) from that SVG.
1. Optionally remove or archive the `api/static/logo-candidates/` folder once the final logo is in place.
