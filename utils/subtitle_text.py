"""
Normalize sidecar subtitle/caption files (SRT, VTT, ASS/SSA) to plain dialogue text for sensitivity scan.

Strips cue indices, timing lines, and markup so the detector sees conversational text rather than
timestamps—reducing noise while preserving phrases that may contain PII or sensitive categories.
"""

from __future__ import annotations

import re

# Extensions handled by normalize_subtitle_sample (also listed in filesystem_connector _TEXT_EXTENSIONS).
SUBTITLE_EXTENSIONS = frozenset({".srt", ".vtt", ".ass", ".ssa"})

# SRT / VTT cue timing line (hours may be omitted in some VTT).
_RE_CUE_TIMING = re.compile(
    r"^\s*\d{1,2}:\d{2}:\d{2}[,.]\d{3}\s*-->\s*\d{1,2}:\d{2}:\d{2}[,.]\d{3}",
)
_RE_CUE_TIMING_SHORT = re.compile(
    r"^\s*\d{1,2}:\d{2}[,.]\d{3}\s*-->\s*\d{1,2}:\d{2}[,.]\d{3}",
)
_RE_NUMERIC_CUE_INDEX = re.compile(r"^\s*\d+\s*$")
_RE_ASS_OVERRIDE = re.compile(r"\{[^}]*\}")


def normalize_subtitle_sample(raw: str, ext: str) -> str:
    """
    Return dialogue-ish text suitable for ``scan_file_content`` / ML+regex.

    * ``.srt`` / ``.vtt`` — drop WEBVTT headers, cue indices, timing lines; keep text lines.
    * ``.ass`` / ``.ssa`` — strip override blocks ``{...}``, drop section lines ``[...]``;
      pull text from ``Dialogue:`` rows (field after last comma cluster — best-effort).
    """
    if not raw:
        return ""
    ext_l = (ext or "").lower()
    if ext_l not in SUBTITLE_EXTENSIONS:
        return raw

    if ext_l in (".srt", ".vtt"):
        return _normalize_srt_or_vtt(raw, ext_l)
    return _normalize_ass_ssa(raw)


def _normalize_srt_or_vtt(raw: str, ext_l: str) -> str:
    lines_out: list[str] = []
    for line in raw.splitlines():
        s = line.strip()
        if not s:
            continue
        if ext_l == ".vtt":
            if s.upper() == "WEBVTT":
                continue
            if s.startswith("NOTE") or s.startswith("STYLE") or s.startswith("REGION"):
                continue
        if _RE_NUMERIC_CUE_INDEX.match(s):
            continue
        if _RE_CUE_TIMING.match(s) or _RE_CUE_TIMING_SHORT.match(s) or "-->" in s:
            continue
        lines_out.append(s)
    return "\n".join(lines_out)


def _normalize_ass_ssa(raw: str) -> str:
    lines_out: list[str] = []
    for line in raw.splitlines():
        s = line.strip()
        if not s or s.startswith(";"):
            continue
        if s.startswith("[") and s.endswith("]"):
            continue
        upper = s.upper()
        if upper.startswith("DIALOGUE:"):
            body = s.split(":", 1)[1].strip()
            # ASS: Layer, Start, End, Style, Actor, MarginL, MarginR, MarginV, Effect, Text
            parts = body.split(",", 9)
            if len(parts) >= 10:
                text = parts[9].strip()
            else:
                text = body
            text = _RE_ASS_OVERRIDE.sub(" ", text)
            text = text.replace("\\N", " ").replace("\\n", " ").strip()
            if text:
                lines_out.append(text)
        else:
            # Comments / format lines — skip
            if upper.startswith("FORMAT:") or upper.startswith("STYLE:"):
                continue
    return "\n".join(lines_out)


def looks_like_subtitle_markup(sample: str) -> bool:
    """
    True when raw sample contains subtitle timing/markup, or normalized text still looks like
    caption dialogue (many medium-short lines). Used by detector entertainment context when
    the path is not already a known subtitle extension.
    """
    if not (sample or "").strip():
        return False
    head = sample[:4000]
    if "-->" in head and (
        _RE_CUE_TIMING.search(sample)
        or _RE_CUE_TIMING_SHORT.search(sample)
        or "WEBVTT" in sample[:500].upper()
    ):
        return True
    lines = [ln.strip() for ln in sample.splitlines() if ln.strip()]
    if len(lines) < 3:
        return False
    timing_hits = sum(
        1
        for ln in lines[:40]
        if "-->" in ln or _RE_CUE_TIMING.match(ln) or _RE_CUE_TIMING_SHORT.match(ln)
    )
    if timing_hits >= 2:
        return True
    # Normalized sidecar dialogue: many short lines (typical of captions / transcripts)
    if len(lines) >= 8:
        lengths = [len(ln) for ln in lines[:48]]
        if not lengths:
            return False
        med = sorted(lengths)[len(lengths) // 2]
        avg = sum(lengths) / len(lengths)
        longest = max(lengths)
        if med <= 62 and avg < 72 and longest <= 220:
            return True
    return False
