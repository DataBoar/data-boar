"""Public wording lint — legal/forensic overclaims (#1193).

Fails CI when a public doc or operator-facing string asserts an absolute
legal/forensic claim (certifies compliance, admissible evidence, …).
ADR-0025 and meta docs that *explain* the ceiling are allowlisted.

Negated uses (“not a legal conclusion”, “avoid certifies compliance”) are
not hits — those restatements are the doctrine, not the overclaim.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]

# Class of absolute legal/forensic claims (EN + pt-BR mirrors).
_CLAIM_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("certifies_compliance", re.compile(r"\bcertif(?:y|ies|ied)\s+compliance\b", re.I)),
    ("guarantees_compliance", re.compile(r"\bguarantees?\s+compliance\b", re.I)),
    ("proves_compliance", re.compile(r"\bproves?\s+compliance\b", re.I)),
    ("legal_conclusion", re.compile(r"\blegal\s+conclusions?\b", re.I)),
    ("admissible_evidence", re.compile(r"\badmissible\s+evidence\b", re.I)),
    ("forensic_proof", re.compile(r"\bforensic\s+(?:proof|evidence)\b", re.I)),
    ("deteccao_completa", re.compile(r"\bdetec[cç][aã]o\s+completa\b", re.I)),
    ("certifica_conformidade", re.compile(r"\bcertifica(?:r)?\s+conformidade\b", re.I)),
    ("garante_conformidade", re.compile(r"\bgarante\s+conformidade\b", re.I)),
    ("prova_conformidade", re.compile(r"\bprova\s+conformidade\b", re.I)),
    ("evidencia_admissivel", re.compile(r"\bevid[eê]ncia\s+admiss[ií]vel\b", re.I)),
    ("prova_forense", re.compile(r"\bprova\s+forense\b", re.I)),
)

_MD_EMPHASIS_RE = re.compile(r"[*_`]+")

_NEGATION_MARKERS = (
    "not a ",
    "not an ",
    "not the ",
    "not ",
    "no ",
    "never ",
    "avoid",
    "without ",
    "não ",
    "nao ",
    "nunca ",
    "nada de ",
    "sem ",
    "≠",
    "vs ",
    "versus ",
    "unlike ",
    "rather than ",
    "instead of ",
    "do not ",
    "don't ",
    "cannot ",
    "can't ",
    "or legal conclusion",
)

# Docs that teach the ceiling (quote the forbidden phrases on purpose).
_ALLOWLIST_REL: frozenset[str] = frozenset(
    {
        "docs/adr/ADR-0025-compliance-positioning-evidence-inventory-not-legal-conclusion-engine.md",
        "docs/CANONICAL_PRODUCT_FACTS.md",
        "docs/COMPLIANCE_AND_LEGAL.md",
        "docs/COMPLIANCE_AND_LEGAL.pt_BR.md",
        "docs/TALENT_POOL_LEARNING_PATHS.md",
        "docs/TALENT_POOL_LEARNING_PATHS.pt_BR.md",
        "docs/ops/EVIDENCE_PACKET_TEMPLATE.md",
        "docs/ops/EVIDENCE_PACKET_TEMPLATE.pt_BR.md",
        "docs/primers/FORENSICS_AND_EVIDENCE_PRIMER.md",
        "docs/primers/FORENSICS_AND_EVIDENCE_PRIMER.pt_BR.md",
        "tests/test_public_claims_lint.py",
    }
)

_SKIP_DIR_PARTS = frozenset(
    {
        ".git",
        ".venv",
        "node_modules",
        "private",
        "docs/private",
    }
)


def _is_negated(text: str, match_start: int) -> bool:
    raw = text[max(0, match_start - 240) : match_start]
    window = _MD_EMPHASIS_RE.sub("", raw).lower()
    return any(marker in window for marker in _NEGATION_MARKERS)


def find_overclaims(text: str) -> list[tuple[str, int, str]]:
    """Return (rule_id, 1-based line, snippet) for non-negated hits."""
    hits: list[tuple[str, int, str]] = []
    for rule_id, pat in _CLAIM_PATTERNS:
        for m in pat.finditer(text):
            if _is_negated(text, m.start()):
                continue
            line_no = text.count("\n", 0, m.start()) + 1
            snippet = m.group(0)
            hits.append((rule_id, line_no, snippet))
    return hits


def _skip_rel(rel: Path) -> bool:
    posix = rel.as_posix()
    if posix in _ALLOWLIST_REL:
        return True
    parts = rel.parts
    if any(p in _SKIP_DIR_PARTS for p in parts):
        return True
    if "private" in parts:
        return True
    if posix.startswith("docs/private"):
        return True
    return False


def _iter_public_paths() -> list[Path]:
    patterns = ("*.md", "*.mdc", "*.py", "*.html")
    out: list[Path] = []
    try:
        proc = subprocess.run(
            ["git", "ls-files", "-z", *patterns],
            cwd=REPO_ROOT,
            check=True,
            capture_output=True,
        )
        for entry in proc.stdout.split(b"\0"):
            if not entry:
                continue
            rel = Path(entry.decode("utf-8", errors="replace"))
            if _skip_rel(rel):
                continue
            # Public product/docs surface — skip test fixtures and vendor-ish trees.
            if rel.parts and rel.parts[0] == "tests":
                continue
            if rel.parts and rel.parts[0] in {".cursor", "rust"}:
                continue
            out.append(REPO_ROOT / rel)
    except (FileNotFoundError, subprocess.CalledProcessError, OSError):
        for pat in patterns:
            for path in REPO_ROOT.rglob(pat):
                try:
                    rel = path.relative_to(REPO_ROOT)
                except ValueError:
                    continue
                if _skip_rel(rel):
                    continue
                if rel.parts and rel.parts[0] in {"tests", ".cursor", "rust"}:
                    continue
                out.append(path)
    return sorted(set(out))


def test_matcher_flags_absolute_overclaim() -> None:
    text = "This product certifies compliance with GDPR.\n"
    hits = find_overclaims(text)
    assert any(h[0] == "certifies_compliance" for h in hits)


def test_matcher_ignores_negated_legal_conclusion() -> None:
    text = "Outputs are evidence, not a legal conclusion.\n"
    assert find_overclaims(text) == []


def test_matcher_ignores_markdown_emphasis_not() -> None:
    text = "Findings are indicators (**not** legal conclusions).\n"
    assert find_overclaims(text) == []


def test_adr_0025_is_allowlisted() -> None:
    rel = (
        "docs/adr/ADR-0025-compliance-positioning-evidence-inventory-"
        "not-legal-conclusion-engine.md"
    )
    assert rel in _ALLOWLIST_REL
    path = REPO_ROOT / rel
    assert path.is_file(), "ADR-0025 must remain the doctrine anchor for this lint"


def test_public_tree_has_no_absolute_legal_forensic_claims() -> None:
    failures: list[str] = []
    for path in _iter_public_paths():
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        rel = path.relative_to(REPO_ROOT).as_posix()
        for rule_id, line_no, snippet in find_overclaims(text):
            failures.append(f"{rel}:{line_no}: {rule_id} → {snippet!r}")
    assert not failures, (
        "Public wording asserts an absolute legal/forensic claim (#1193 / ADR-0025). "
        "Reword to indicators/evidence, or add a meta-doc to the allowlist if the "
        "file explains what not to say:\n  " + "\n  ".join(failures)
    )
