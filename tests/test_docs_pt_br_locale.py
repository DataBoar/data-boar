"""
Guard: Brazilian Portuguese (pt-BR) docs must not use common European Portuguese (pt-PT) markers.

Scans ``**/*.pt_BR.md`` under the repo root (excluding ``.venv`` and ``node_modules``). By default **skips**
any path with a segment named ``private`` (e.g. ``docs/private/**``), matching ``test_markdown_lint`` and
``docs/TESTING.md`` — CI and pre-commit do not depend on gitignored operator notes. Opt in locally with
``pytest --include-private`` or ``INCLUDE_PRIVATE_LINT=1`` (see ``tests/conftest.py``).

Lines that only *illustrate* forbidden forms (policy examples) are skipped — see ``_line_is_locale_example``.

When adding copy for the private pitch (``docs/private/pitch/slides.yaml``) or future website, either keep it
English-only until reviewed or run the same vocabulary checks by hand; if those files become tracked, extend
``_extra_locale_scan_paths`` below.

Policy default for assistants: **``.cursor/rules/docs-locale-pt-br-contract.mdc``** (always applied).

**Gitignored Portuguese drafts:** ``docs/private/social_drafts/drafts/*.md`` (and editorial notes) are not on GitHub CI. Drafts use a
``YYYY-MM-DD_`` filename prefix (publication or next planned date per private hub). For locale guard on
Instagram copy, a **tracked mirror** lives under ``docs/private.example/social_drafts/drafts/`` — keep it in sync with
the private draft (see file header there).

Run: ``uv run pytest tests/test_docs_pt_br_locale.py -v``
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]

# Optional extra roots/files (relative to repo). Pitch deck source is often gitignored — add when tracked.
_extra_locale_scan_paths: tuple[str, ...] = (
    "docs/private.example/social_drafts/drafts/2026-04-08_instagram_databoar_patreon_apoio_oss.example.md",
)


def _iter_pt_br_markdown_files(*, include_private: bool) -> list[Path]:
    out: list[Path] = []
    for p in REPO_ROOT.rglob("*.pt_BR.md"):
        parts = p.parts
        parts_set = set(parts)
        if ".venv" in parts_set or "node_modules" in parts_set:
            continue
        if not include_private and "private" in parts:
            continue
        out.append(p)
    for rel in _extra_locale_scan_paths:
        candidate = REPO_ROOT / rel
        if candidate.is_file():
            out.append(candidate)
    return sorted(set(out), key=lambda x: str(x).lower())


def _line_is_locale_example(line: str) -> bool:
    """Skip lines that cite pt-PT only as a negative example."""
    if "como norma (ex.:" in line:
        return True
    if "não português europeu" in line.lower():
        return True
    if "*ficheiro*" in line or "*partilhar*" in line or "*secção*" in line:
        return True
    if "*por defeito*" in line:
        return True
    return False


# (label, regex) — use word boundaries; avoid matching inside compartilhar/compartilhamento.
PT_PT_MARKERS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("ficheiro", re.compile(r"\bficheiros?\b", re.IGNORECASE)),
    (
        "partilha(r)?",
        re.compile(r"\bpartilh(ar|a|as|amos|em|ado|ada|ados|adas)\b", re.IGNORECASE),
    ),
    ("secção", re.compile(r"\bsecção\b", re.IGNORECASE)),
    ("acções", re.compile(r"\bacções\b", re.IGNORECASE)),
    ("sítio (web sense)", re.compile(r"\bsítio\b", re.IGNORECASE)),
    ("écran", re.compile(r"\bécrans?\b", re.IGNORECASE)),
    ("equipa", re.compile(r"\bequipa\b", re.IGNORECASE)),
    ("utilizador", re.compile(r"\butilizadores?\b", re.IGNORECASE)),
    ("artefacto", re.compile(r"\bartefactos?\b", re.IGNORECASE)),
    (
        "actualizar",
        re.compile(r"\bactualiza(r|ção|ções|va|vam|mos|ste|ram)\b", re.IGNORECASE),
    ),
    ("subscrição", re.compile(r"\bsubscri(ção|ções)\b", re.IGNORECASE)),
    ("aceder", re.compile(r"\baced(e|em|es|eu|emos|em)\b", re.IGNORECASE)),
    ("consola (IT)", re.compile(r"\bconsolas?\b", re.IGNORECASE)),
    ("tu (possessive plural)", re.compile(r"\btuas\b", re.IGNORECASE)),
    ("foste", re.compile(r"\bfoste\b", re.IGNORECASE)),
    ("podes", re.compile(r"\bpodes\b", re.IGNORECASE)),
    # Infinitive + "a" + gerund (European periphrasis): "continua a usar"
    (
        "continua a + inf.",
        re.compile(r"\bcontinua\s+a\s+(usar|precisar|fazer|ter|ser)\b", re.IGNORECASE),
    ),
    # "X a falhar" (European)
    ("… a falhar", re.compile(r"\s+a\s+falhar\b", re.IGNORECASE)),
    # Obligation "tem de" (prefer "precisa", "tem que", "deve" in BR marketing/tech copy)
    ("tem de ", re.compile(r"\btem\s+de\s+", re.IGNORECASE)),
)


def _violations_in_file(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    bad: list[str] = []
    for i, line in enumerate(lines, start=1):
        if _line_is_locale_example(line):
            continue
        for label, rx in PT_PT_MARKERS:
            if rx.search(line):
                bad.append(
                    f"{path.relative_to(REPO_ROOT)}:{i}: [{label}] {line.strip()[:200]}"
                )
    return bad


def test_pt_br_markdown_avoids_european_portuguese_markers(
    include_private_lint: bool,
) -> None:
    failures: list[str] = []
    for path in _iter_pt_br_markdown_files(include_private=include_private_lint):
        issues = _violations_in_file(path)
        if issues:
            failures.extend(issues)
    if failures:
        msg = "pt-PT-like markers in pt_BR docs — prefer pt-BR (see docs-policy / docs-pt-br-locale rule):\n"
        msg += "\n".join(failures)
        pytest.fail(msg)


def test_pt_br_locale_scan_covers_at_least_one_file(include_private_lint: bool) -> None:
    files = _iter_pt_br_markdown_files(include_private=include_private_lint)
    assert len(files) >= 5, "Expected multiple *.pt_BR.md files under the repo"
