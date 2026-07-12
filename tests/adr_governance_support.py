"""Shared helpers for ADR governance anti-regression tests (issue #1162, ADR-0045)."""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
ADR_DIR = REPO_ROOT / "docs" / "adr"
ADR_GLOB = "docs/adr/ADR-[0-9]*.md"
GENESIS_FIXTURE = (
    Path(__file__).resolve().parent / "fixtures" / "adr_genesis_date_lines.json"
)

# H1 uses em dash (U+2014), not filename hyphen — ADR-0045 §3.
H1_RE = re.compile(r"^# ADR \d{4} — ")

META_DATE_RE = re.compile(r"^- \*\*Date \(UTC\):\*\*", re.MULTILINE)
META_AUTHORS_RE = re.compile(r"^- \*\*Authors:\*\*", re.MULTILINE)
META_DECIDERS_RE = re.compile(r"^- \*\*Deciders:\*\*", re.MULTILINE)
DATE_LINE_RE = re.compile(r"^- \*\*Date \(UTC\):\*\*.*$", re.MULTILINE)
ISO_DATE_IN_DATE_LINE_RE = re.compile(
    r"^- \*\*Date \(UTC\):\*\*.*?(\d{4}-\d{2}-\d{2})", re.MULTILINE
)

STATUS_SECTION_RE = re.compile(r"(?ms)^## Status\s*\r?\n\s*([^\r\n#]+?)\s*(?:\r?\n|$)")

PT_BR_HEADING_DENYLIST: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("Contexto", re.compile(r"\bContexto\b")),
    ("Decisão", re.compile(r"\bDecis[aã]o\b")),
    ("Consequências", re.compile(r"\bConsequ[eê]ncias\b")),
    ("Governança", re.compile(r"\bGovernan[cç]a\b")),
    ("Autoridade", re.compile(r"\bAutoridade\b")),
    ("Justificativa", re.compile(r"\bJustificativa\b")),
    (
        "Alternativas Consideradas",
        re.compile(r"\bAlternativas Consideradas\b"),
    ),
    (
        "Decisões Relacionadas",
        re.compile(r"\bDecis[oõ]es Relacionadas\b"),
    ),
    ("Referências", re.compile(r"\bRefer[eê]ncias\b")),
)

NEW_ADR_ALLOWED_STATUSES = frozenset({"Proposed", "Reserved"})

OVERRIDE_MARKER_RE = re.compile(r"(?im)^\s*ADR-Governance-Override-Approved-By:\s*\S+")


def normalize_eol(text: str) -> str:
    return text.replace("\r\n", "\n").replace("\r", "\n")


def read_adr_text(path: Path) -> str:
    return normalize_eol(path.read_text(encoding="utf-8"))


def iter_adr_files() -> list[Path]:
    return sorted(ADR_DIR.glob("ADR-*.md"))


def parse_status(text: str) -> str | None:
    normalized = normalize_eol(text)
    match = STATUS_SECTION_RE.search(normalized)
    if not match:
        return None
    return match.group(1).strip()


def extract_date_line(text: str) -> str | None:
    match = DATE_LINE_RE.search(normalize_eol(text))
    return match.group(0).strip() if match else None


def load_genesis_fixture() -> dict[str, str | None]:
    data = json.loads(GENESIS_FIXTURE.read_text(encoding="utf-8"))
    return {str(k): (None if v is None else str(v)) for k, v in data.items()}


def _git(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(REPO_ROOT), *args],
        capture_output=True,
        text=True,
        check=False,
    )


def git_is_repo() -> bool:
    return _git(["rev-parse", "--git-dir"]).returncode == 0


def staged_adr_paths(*, diff_filter: str | None = None) -> list[str]:
    args = ["diff", "--cached", "--name-only"]
    if diff_filter:
        args.insert(3, f"--diff-filter={diff_filter}")
    args.append("--")
    args.append(ADR_GLOB)
    proc = _git(args)
    if proc.returncode != 0:
        return []
    return [line.strip() for line in proc.stdout.splitlines() if line.strip()]


def staged_name_status_with_renames() -> list[tuple[str, str, str | None]]:
    """Return (status, old_path, new_path) from cached diff with rename detection."""
    proc = _git(
        [
            "diff",
            "--cached",
            "-M",
            "--find-renames",
            "--name-status",
            "--",
            ADR_GLOB,
        ]
    )
    if proc.returncode != 0:
        return []
    rows: list[tuple[str, str, str | None]] = []
    for line in proc.stdout.splitlines():
        if not line.strip():
            continue
        parts = line.split("\t")
        status = parts[0]
        if status.startswith("R") and len(parts) >= 3:
            rows.append((status, parts[1], parts[2]))
        elif status == "D" and len(parts) >= 2:
            rows.append((status, parts[1], None))
        elif status == "A" and len(parts) >= 2:
            rows.append((status, parts[1], parts[1]))
        elif len(parts) >= 2:
            rows.append((status, parts[1], parts[1]))
    return rows


def pending_commit_message() -> str:
    for path in (REPO_ROOT / ".git" / "COMMIT_EDITMSG",):
        if path.is_file():
            return path.read_text(encoding="utf-8", errors="replace")
    proc = _git(["log", "-1", "--format=%B"])
    return proc.stdout if proc.returncode == 0 else ""


def governance_override_present() -> bool:
    return bool(OVERRIDE_MARKER_RE.search(pending_commit_message()))
