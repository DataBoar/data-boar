"""
Optional steganography *hints* for rich-media containers (opt-in via ``file_scan.scan_for_stego``).

This is a bounded, heuristic signal (byte-sample entropy), not a stego extraction tool.
"""

from __future__ import annotations

import math
from collections import Counter
from pathlib import Path

from core.rich_media_magic import RICH_MEDIA_SCAN_EXTENSIONS

_STEGO_READ_CAP = 524_288  # 512 KiB


def append_stego_hint(path: Path, ext: str, base: str, max_chars: int) -> str:
    """Append a short entropy hint when the extension is a rich-media container; cap total length."""
    hint = build_stego_hint_text(path, ext)
    if not hint:
        return base[:max_chars]
    combined = f"{base}\n{hint}".strip() if base else hint
    return combined[:max_chars]


def build_stego_hint_text(path: Path, ext: str) -> str:
    """Return a one-line heuristic or empty string if not applicable / on error."""
    ext_l = (ext or "").lower()
    if ext_l not in RICH_MEDIA_SCAN_EXTENSIONS:
        return ""
    try:
        data = path.read_bytes()[:_STEGO_READ_CAP]
    except OSError:
        return ""
    if len(data) < 64:
        return ""
    ent = _shannon_entropy_bytes(data)
    if ent >= 7.8:
        bucket = "high"
    elif ent >= 6.5:
        bucket = "moderate"
    else:
        bucket = "typical"
    return f"stego_hint: sample_entropy={ent:.2f} ({bucket}; not proof of hidden data)"


def _shannon_entropy_bytes(data: bytes) -> float:
    n = len(data)
    if n == 0:
        return 0.0
    counts = Counter(data)
    return float(-sum((c / n) * math.log2(c / n) for c in counts.values()))
