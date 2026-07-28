"""Shared Markdown line + inline parsing for executive PDF/DOCX renderers."""

from __future__ import annotations

import html
import re
from collections.abc import Iterator
from dataclasses import dataclass
from enum import Enum


class LineKind(str, Enum):
    BLANK = "blank"
    H1 = "h1"
    H2 = "h2"
    H3 = "h3"
    H4 = "h4"
    H5 = "h5"
    BULLET = "bullet"
    BODY = "body"


@dataclass(frozen=True)
class ParsedLine:
    kind: LineKind
    text: str


_HEADING_PREFIXES: tuple[tuple[str, LineKind], ...] = (
    ("##### ", LineKind.H5),
    ("#### ", LineKind.H4),
    ("### ", LineKind.H3),
    ("## ", LineKind.H2),
    ("# ", LineKind.H1),
)

_INLINE_TOKEN_RE = re.compile(r"\*\*([^*]+)\*\*|`([^`]+)`")


def parse_executive_line(raw_line: str) -> ParsedLine:
    """Parse one Markdown-shaped executive report line."""
    line = raw_line.rstrip()
    if not line.strip():
        return ParsedLine(LineKind.BLANK, "")
    for prefix, kind in _HEADING_PREFIXES:
        if line.startswith(prefix):
            return ParsedLine(kind, line[len(prefix) :].strip())
    if line.startswith("- "):
        return ParsedLine(LineKind.BULLET, line[2:].strip())
    return ParsedLine(LineKind.BODY, line)


def iter_inline_segments(text: str) -> Iterator[tuple[str, str]]:
    """Yield ``(kind, segment)`` where kind is ``text``, ``bold``, or ``code``."""
    pos = 0
    for match in _INLINE_TOKEN_RE.finditer(text):
        if match.start() > pos:
            yield ("text", text[pos : match.start()])
        if match.group(1) is not None:
            yield ("bold", match.group(1))
        else:
            yield ("code", match.group(2))
        pos = match.end()
    if pos < len(text):
        yield ("text", text[pos:])


def markdown_inline_to_reportlab(text: str) -> str:
    """Convert inline ``**`` / `` ` `` to reportlab Paragraph markup (escape first)."""
    parts: list[str] = []
    for kind, segment in iter_inline_segments(text):
        if kind == "bold":
            inner = markdown_inline_to_reportlab(segment)
            parts.append(f"<b>{inner}</b>")
        elif kind == "code":
            escaped = html.escape(segment, quote=False)
            parts.append(f'<font face="Courier">{escaped}</font>')
        else:
            parts.append(html.escape(segment, quote=False))
    return "".join(parts).replace("\n", "<br/>")


def append_markdown_runs_to_paragraph(
    paragraph, text: str, *, bold: bool = False
) -> None:
    """Add inline-formatted runs to an existing python-docx paragraph."""
    for kind, segment in iter_inline_segments(text):
        if kind == "bold":
            append_markdown_runs_to_paragraph(paragraph, segment, bold=True)
            continue
        run = paragraph.add_run(segment)
        if bold:
            run.bold = True
        if kind == "code":
            run.font.name = "Courier New"


__all__ = [
    "LineKind",
    "ParsedLine",
    "append_markdown_runs_to_paragraph",
    "iter_inline_segments",
    "markdown_inline_to_reportlab",
    "parse_executive_line",
]
