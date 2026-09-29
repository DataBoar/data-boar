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

# T7 (#1925): incident-shaped embedded experimental data (keen-platypus class), not loose numbers.
OPERATOR_DECISION_LINE_RE = re.compile(
    r"^[\s]*(?:>[\s]*)?(?:[-*+][\s]+)?(?:\*\*)?"
    r"Operator decision\s*\(\d{4}-\d{2}-\d{2}\)",
    re.MULTILINE | re.IGNORECASE,
)
BENCHMARK_TABLE_CELL_RE = re.compile(
    r"\d[\d.,]*\s*(?:(?:ms|µs|us|sec)(?![A-Za-z])|×|x\s*slower|req/s|MB/s)"
    r"|(?:\d+\.\d+|\d+)\s*×",
    re.IGNORECASE,
)
# Case-sensitive PASSED/FAILED (pytest); avoid matching `status: failed` in YAML samples.
TEST_RUNNER_IN_FENCE_RE = re.compile(
    r"\bPASSED\b|\bFAILED\b|\d+\s+passed\b|passed in \d+(?:\.\d+)?s",
)
FENCE_RE = re.compile(r"```[^\n]*\n(.*?)```", re.DOTALL)

T7_BAD_FIXTURE = (
    Path(__file__).resolve().parent
    / "fixtures"
    / "adr_t7_synthetic_bad_embedded_spike.md"
)
T7_GOOD_FIXTURE = (
    Path(__file__).resolve().parent
    / "fixtures"
    / "adr_t7_synthetic_good_benchmark_reference.md"
)
GRANDFATHER_FIXTURE = (
    Path(__file__).resolve().parent
    / "fixtures"
    / "adr_embedded_benchmark_grandfather.json"
)


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


def _markdown_table_blocks(text: str) -> list[list[str]]:
    blocks: list[list[str]] = []
    lines = normalize_eol(text).split("\n")
    index = 0
    while index < len(lines):
        if not lines[index].strip().startswith("|"):
            index += 1
            continue
        block: list[str] = []
        while index < len(lines) and lines[index].strip().startswith("|"):
            block.append(lines[index])
            index += 1
        if len(block) >= 3:
            blocks.append(block)
    return blocks


def _is_table_separator_row(line: str) -> bool:
    return bool(re.match(r"^\|\s*[-: ]+\|", line.replace(" ", "")))


def _table_data_rows(block: list[str]) -> list[str]:
    if not block:
        return []
    # Full table: header + separator + data. Staged + chunks may be data rows only.
    start = 2 if len(block) >= 2 and _is_table_separator_row(block[1]) else 0
    rows: list[str] = []
    for line in block[start:]:
        if _is_table_separator_row(line):
            continue
        rows.append(line)
    return rows


def _benchmark_dataset_table_violation(block: list[str]) -> bool:
    data_rows = _table_data_rows(block)
    if len(data_rows) < 3:
        return False
    measurement_rows = sum(
        1 for row in data_rows if BENCHMARK_TABLE_CELL_RE.search(row)
    )
    return measurement_rows >= 3


def _test_runner_codeblock_violation(text: str) -> bool:
    for match in FENCE_RE.finditer(normalize_eol(text)):
        body = match.group(1)
        if TEST_RUNNER_IN_FENCE_RE.search(body):
            return True
    return False


def embedded_experimental_data_violations(
    text: str, *, check_tables: bool = True
) -> list[str]:
    """Return stable violation codes for incident-shaped embedded benchmark/spike data.

    ``check_tables=False`` skips the 3+ row measurement-table heuristic (legacy Accepted
    ADRs may cite µs/call tables; non-retroactive posture — table rule targets staged
    additions and fixtures).
    """
    normalized = normalize_eol(text)
    hits: list[str] = []
    if OPERATOR_DECISION_LINE_RE.search(normalized):
        hits.append("operator_decision_line")
    if check_tables:
        for block in _markdown_table_blocks(normalized):
            if _benchmark_dataset_table_violation(block):
                hits.append("benchmark_dataset_table_3plus_rows")
                break
    if _test_runner_codeblock_violation(normalized):
        hits.append("test_runner_codeblock")
    return hits


def staged_adr_added_chunks() -> list[tuple[str, str]]:
    """Per staged ADR path, text formed only from added lines in the cached diff (A or M)."""
    proc = _git(["diff", "--cached", "-U0", "--", ADR_GLOB])
    if proc.returncode != 0 or not proc.stdout.strip():
        return []
    chunks: dict[str, list[str]] = {}
    current: str | None = None
    for line in proc.stdout.splitlines():
        if line.startswith("+++ b/"):
            current = line.removeprefix("+++ b/").strip()
            if current.startswith("docs/adr/"):
                chunks.setdefault(current, [])
            else:
                current = None
            continue
        if current is None or not line.startswith("+") or line.startswith("+++"):
            continue
        if line == r"\ No newline at end of file":
            continue
        chunks[current].append(line[1:])
    return [(path, "\n".join(lines)) for path, lines in chunks.items() if lines]


def load_grandfather_allowlist() -> dict[str, dict[str, str]]:
    if not GRANDFATHER_FIXTURE.is_file():
        return {}
    data = json.loads(GRANDFATHER_FIXTURE.read_text(encoding="utf-8"))
    return {str(k): dict(v) for k, v in data.items()}
