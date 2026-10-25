# Video frame extract for agent context (Windows, token-aware)

**Português (Brasil):** [VIDEO_FRAME_EXTRACT_FOR_AGENT.pt_BR.md](VIDEO_FRAME_EXTRACT_FOR_AGENT.pt_BR.md)

## Purpose

Chat models do not reliably **decode video** the way humans watch a stream. On the **operator Windows workstation**, assistants should use a **structured ladder**: metadata first, then **sparse PNG frames** at **named timestamps** (or a small CSV list). That mirrors the repo pattern for **`es-find.ps1`** (fast path + documented install) instead of blind full-disk walks.

## Taxonomy (complexity vs tokens)

| Level | What | When |
| ----- | ---- | ---- |
| **L0** | Do nothing with the file | Video is huge, irrelevant, or operator will paste text/screenshot. |
| **L1** | **`ffprobe`** only: duration, codecs, resolution | Decide how many samples; detect audio-only. |
| **L2** | **`video-frame-samples.ps1`**: a few PNGs at **operator-supplied seconds** (e.g. “~3s shows the error”) | Default for Maestro / terminal / UI proof clips. |
| **L3** | Dense sampling (e.g. ffmpeg `fps=1` over full video) | Only when the operator cannot name any timestamp; **high** image token cost. |

## Primary automation

**Script:** **`scripts/video-frame-samples.ps1`**

**Install (operator PC):** `winget install ffmpeg` (puts **`ffmpeg`** / **`ffprobe`** on PATH; WinGet Links is also probed).

**Examples:**

```powershell
# Duration only
.\scripts\video-frame-samples.ps1 -MediaPath "D:\Captures\clip.mp4" -ProbeOnly

# Operator hint: interesting content near 3s and 12s
.\scripts\video-frame-samples.ps1 -MediaPath "D:\Captures\clip.mp4" -Timestamp 3 -Timestamp 12

# Comma-separated list
.\scripts\video-frame-samples.ps1 -MediaPath "D:\Captures\clip.mp4" -TimestampsCsv "0,3,10.5"

# Downscale for smaller vision payloads (max width 1280px)
.\scripts\video-frame-samples.ps1 -MediaPath "D:\Captures\clip.mp4" -Timestamp 3 -MaxWidth 1280
```

Output prints **`output_dir`** and one line per **PNG** path; the assistant **`read_file`** on those images (same as screenshot workflow).

## Contract with the operator

1. Prefer **seconds** (“~3s”, “at 0:12”) so the assistant runs **L2** without scanning the whole clip.
2. If the path has spaces or unicode, use quotes; the script uses **`-LiteralPath`** where it matters.
3. If **`ffmpeg`** is missing, the script exits **3** with a **one-line** `winget` hint — same honesty rule as **`es-find`** when **`es.exe`** is absent.

## Optional tooling (not required)

| Tool | Role |
| ---- | ---- |
| **ffmpeg** | Required for this workflow; encodes/decodes and seeks. |
| **whisper / local STT** | Transcript of speech — separate token budget; add only if the task is dialogue-heavy. |

There is no need for a second “video Everything”: **path discovery** stays **`es-find.ps1`**; **time extraction** stays **`video-frame-samples.ps1`**.

## Pairing with still photos (EXIF / OCR)

For **JPEG / HEIC / PNG** and optional **Tesseract** on visible text, use **`scripts/image-inspect.ps1`** — [IMAGE_EXIF_OCR_FOR_AGENT.md](IMAGE_EXIF_OCR_FOR_AGENT.md).

## References

- **`docs/ops/TOKEN_AWARE_SCRIPTS_HUB.md`** (hub row)
- **`docs/ops/WINDOWS_FAST_CLI_WRAPPERS.md`**
- **`.cursor/skills/video-frames-for-agent/SKILL.md`**
- **`.cursor/rules/repo-scripts-wrapper-ritual.mdc`**
