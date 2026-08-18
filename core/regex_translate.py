"""
Python ``re`` → Rust ``regex`` mechanical translator (#1414 / PLAN_RUST_REGEX_STAGE §2.7).

Python is the semantic source of truth; Rust receives patterns already corrected.
``translate(pattern) -> (rust_pattern | None, reason)`` where ``None`` means keep
the Python fallback path for that pattern only.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum

# Turkish / dotted-I case-folding pair — sole BMP divergence for Python (?i) vs Rust.
_TURKISH_I_EXPANSION = "iIİı"


class RoutingKind(str, Enum):
    DIRECT = "direct"
    TRANSLATED = "translated"
    PYTHON_FALLBACK = "python_fallback"
    RUST_ONLY = "rust_only"


@dataclass(frozen=True)
class PatternRouting:
    name: str
    python_pattern: str
    rust_pattern: str | None
    kind: RoutingKind
    reason: str


_CLASS_A_MARKERS: tuple[tuple[str, str], ...] = (
    ("(?<=", "lookbehind"),
    ("(?<!", "lookbehind_neg"),
    ("(?=", "lookahead"),
    ("(?!", "lookahead_neg"),
    ("(?>", "atomic_group"),
    ("(?(", "conditional"),
    ("\\Z", "z_anchor"),
)

_POSSESSIVE = re.compile(r"(?<!\\)(?:\*\++|\+\++|\?\++|\}\++)")


def _class_a_reason(pattern: str) -> str | None:
    for marker, label in _CLASS_A_MARKERS:
        if marker in pattern:
            return label
    if re.search(r"\\[1-9]", pattern):
        return "backreference"
    if re.search(r"\(\?[aL]:|\(\?[aL]\)", pattern):
        return "ascii_or_locale_flag"
    return None


def _class_b_reason(pattern: str) -> str | None:
    if "(?i:" in pattern:
        return "scoped_case_insensitive"
    idx = pattern.find("(?i)")
    if idx > 0:
        return "mid_pattern_case_insensitive"
    if _POSSESSIVE.search(pattern):
        return "possessive_quantifier"
    return None


def _find_char_class_end(pattern: str, start: int) -> int:
    """Return index of closing ``]`` for class starting at ``start`` (which is ``[``)."""
    i = start + 1
    n = len(pattern)
    if i < n and pattern[i] == "]":
        return i
    while i < n:
        if pattern[i] == "\\":
            i += 2
            continue
        if pattern[i] == "]":
            return i
        i += 1
    return n - 1


def _char_in_range(lo: str, hi: str, target_ord: int) -> bool:
    return ord(lo) <= target_ord <= ord(hi)


def _class_content_needs_turkish_i(content: str) -> bool:
    if any(ch in content for ch in _TURKISH_I_EXPANSION):
        return False
    i = 0
    n = len(content)
    while i < n:
        ch = content[i]
        if ch == "\\":
            i += 2
            continue
        if ch in "iI":
            return True
        if i + 2 < n and content[i + 1] == "-":
            lo, hi = content[i], content[i + 2]
            if _char_in_range(lo, hi, ord("i")) or _char_in_range(lo, hi, ord("I")):
                return True
            i += 3
            continue
        i += 1
    return False


def _expand_char_class_for_ci(content: str) -> str:
    if not _class_content_needs_turkish_i(content):
        return content
    return f"{content}İı"


def _translate_dollar_anchor(body: str) -> str:
    if "(?m)" in body:
        return body
    out: list[str] = []
    i = 0
    n = len(body)
    while i < n:
        if body[i] == "\\":
            out.append(body[i : i + 2] if i + 1 < n else body[i])
            i += 2 if i + 1 < n else 1
            continue
        if body[i] == "$":
            out.append("(?:\\n?\\z)")
            i += 1
            continue
        out.append(body[i])
        i += 1
    return "".join(out)


def _translate_case_insensitive_body(body: str) -> str:
    out: list[str] = []
    i = 0
    n = len(body)
    while i < n:
        ch = body[i]
        if ch == "\\":
            out.append(body[i : i + 2] if i + 1 < n else body[i])
            i += 2 if i + 1 < n else 1
            continue
        if ch == "[":
            end = _find_char_class_end(body, i)
            inner = body[i + 1 : end]
            out.append("[")
            out.append(_expand_char_class_for_ci(inner))
            out.append("]")
            i = end + 1
            continue
        if ch == "(":
            end = _find_group_end(body, i)
            group = body[i:end]
            out.append(_translate_case_insensitive_group(group))
            i = end
            continue
        if ch in "iI":
            out.append(f"[{_TURKISH_I_EXPANSION}]")
            i += 1
            continue
        out.append(ch)
        i += 1
    return "".join(out)


def _find_group_end(pattern: str, start: int) -> int:
    depth = 0
    i = start
    n = len(pattern)
    while i < n:
        if pattern[i] == "\\":
            i += 2
            continue
        if pattern[i] == "[":
            i = _find_char_class_end(pattern, i) + 1
            continue
        if pattern[i] == "(":
            depth += 1
        elif pattern[i] == ")":
            depth -= 1
            if depth == 0:
                return i + 1
        i += 1
    return n


def _translate_case_insensitive_group(group: str) -> str:
    if not group.startswith("("):
        return group
    # Non-capturing / flag-only groups: (?m), (?s), (?x), (?:...)
    if (
        group.startswith("(?")
        and not group.startswith("(?P")
        and not group.startswith("(?<")
    ):
        close = group.find(")")
        if close != -1 and close < len(group) - 1:
            prefix = group[: close + 1]
            rest = group[close + 1 : -1]
            if rest:
                return prefix + _translate_case_insensitive_body(rest) + ")"
            return group
    if group.startswith("(?P<"):
        gt = group.find(">", 3)
        if gt == -1:
            return group
        prefix = group[: gt + 1]
        rest = group[gt + 1 : -1]
        return prefix + _translate_case_insensitive_body(rest) + ")"
    if group.startswith("(?<") and ">" in group:
        gt = group.find(">", 3)
        prefix = group[: gt + 1]
        rest = group[gt + 1 : -1]
        return prefix + _translate_case_insensitive_body(rest) + ")"
    inner = group[1:-1]
    return "(" + _translate_case_insensitive_body(inner) + ")"


def translate(pattern: str) -> tuple[str | None, str]:
    """
    Return ``(rust_pattern, reason)``.

    ``rust_pattern is None`` → keep Python matching for this pattern only.
    """
    reason_a = _class_a_reason(pattern)
    if reason_a:
        return None, reason_a
    reason_b = _class_b_reason(pattern)
    if reason_b:
        return None, reason_b

    body = pattern
    translated_ci = False
    if body.startswith("(?i)") and not body.startswith("(?i:"):
        body = body[4:]
        translated_ci = True

    new_body = _translate_dollar_anchor(body)
    dollar_changed = new_body != body
    body = new_body

    if translated_ci:
        body = _translate_case_insensitive_body(body)

    if translated_ci or dollar_changed:
        return body, "translated"
    return pattern, "direct"


def classify_pattern(name: str, pattern: str) -> PatternRouting:
    rust_pattern, reason = translate(pattern)
    if rust_pattern is None:
        return PatternRouting(
            name=name,
            python_pattern=pattern,
            rust_pattern=None,
            kind=RoutingKind.PYTHON_FALLBACK,
            reason=reason,
        )
    kind = RoutingKind.TRANSLATED if reason == "translated" else RoutingKind.DIRECT
    return PatternRouting(
        name=name,
        python_pattern=pattern,
        rust_pattern=rust_pattern,
        kind=kind,
        reason=reason,
    )
