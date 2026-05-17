---
name: video-frames-for-agent
description: Extract sparse PNG frames from operator video on Windows using scripts/video-frame-samples.ps1 and ffprobe; use L1-L3 taxonomy in docs/ops/VIDEO_FRAME_EXTRACT_FOR_AGENT.md.
---

# Video frames for agent context (Windows)

## When to use

- The operator shared an **MP4** (or other ffmpeg-readable media) and the assistant needs **visual context** (terminal, Maestro, UI).
- The operator can give **approximate seconds** (“interesting at ~3s”).

## Ritual (token-aware)

1. Read **`docs/ops/VIDEO_FRAME_EXTRACT_FOR_AGENT.md`** for the **L0-L3** ladder if unsure.
2. From repo root, prefer **`.\scripts\video-frame-samples.ps1`**:
   - **`-ProbeOnly`** first when duration / “is this worth sampling?” matters.
   - **`-Timestamp`** / **`-TimestampsCsv`** at operator hints.
   - **`-MaxWidth 960`** or **1280** when full resolution is unnecessary.
3. **`read_file`** on each printed **PNG** path (vision path).
4. If **ffmpeg** missing: report the script’s **one-line** install hint (`winget install ffmpeg`); do not pretend video was watched.

## Anti-patterns

- Claiming the model “watched” a video without **`ffprobe`** / frame extraction.
- Dense **fps=1** over long clips without operator approval (**L3** cost).

## Pointers

- **`scripts/video-frame-samples.ps1`** (`-Help`)
- **`docs/ops/VIDEO_FRAME_EXTRACT_FOR_AGENT.md`**
- Filename discovery elsewhere: **`scripts/es-find.ps1`**
