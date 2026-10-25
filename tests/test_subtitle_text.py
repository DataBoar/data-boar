"""Tests for subtitle sidecar normalization (SRT, VTT, ASS)."""

from __future__ import annotations

import unittest

from utils.subtitle_text import (
    looks_like_subtitle_markup,
    normalize_subtitle_sample,
)


class TestSubtitleText(unittest.TestCase):
    def test_normalize_srt_strips_timing(self) -> None:
        raw = """1
00:00:01,234 --> 00:00:03,500
Hello from Maria

2
00:00:04,000 --> 00:00:06,000
Second line here
"""
        out = normalize_subtitle_sample(raw, ".srt")
        self.assertNotIn("-->", out)
        self.assertIn("Hello from Maria", out)
        self.assertIn("Second line here", out)

    def test_normalize_vtt_strips_header_and_timing(self) -> None:
        raw = """WEBVTT

00:00:00.000 --> 00:00:02.000
First cue

00:00:02.500 --> 00:00:05.000
Second cue text
"""
        out = normalize_subtitle_sample(raw, ".vtt")
        self.assertNotIn("WEBVTT", out)
        self.assertNotIn("-->", out)
        self.assertIn("First cue", out)

    def test_looks_like_subtitle_markup_raw_cues(self) -> None:
        self.assertTrue(
            looks_like_subtitle_markup(
                "00:00:01,000 --> 00:00:03,000\nHello\n\n00:00:04,000 --> 00:00:06,000\nBye\n"
            )
        )

    def test_looks_like_subtitle_markup_normalized_short_lines(self) -> None:
        lines = "\n".join(f"Short line number {i} here" for i in range(10))
        self.assertTrue(looks_like_subtitle_markup(lines))


if __name__ == "__main__":
    unittest.main()
