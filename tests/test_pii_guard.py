"""
Guardrail: tracked files must not contain PII patterns that belong
only in docs/private/ (gitignored stacked private repo).

Scans every file in the Git index for known sensitive literal strings
and regex patterns.  An optional external patterns file
(docs/private/pii-patterns.txt, gitignored) extends the built-in list
without exposing the patterns publicly.

RCA: PII was accidentally committed in .cursor/rules/ and scripts/.
Detected and scrubbed via git filter-repo.  This guard prevents
recurrence.
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]

_BUILTIN_LITERALS: list[str] = [
    "corporate-entity-a_dossie",
    "corporate-entity-a_dossier",
    "caso trabalhista",
    "dossie juridico",
    "processo juridico",
    "INDICE_EVIDENCIAS",
    "SUMARIO_EXECUTIVO_DOSSIE",
    "RISCOS_E_PROTECOES_PARA_ESPOSA",
    "CARTA_DISCLOSURE_Colleague-M_Colleague-N",
]

_BUILTIN_REGEXES: list[tuple[str, re.Pattern[str]]] = [
    # --- Credential / secret patterns (from security-guard complement) ---
    (
        "AWS IAM access key (AKIA prefix)",
        re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    ),
    (
        "GitHub PAT (ghp_ / gho_ / ghu_ / ghs_ / ghr_)",
        re.compile(r"\bgh[pousr]_[A-Za-z0-9]{36,}\b"),
    ),
    (
        "Bearer token in Authorization header",
        re.compile(r"(?i)bearer\s+[A-Za-z0-9\-_\.]{20,}"),
    ),
    (
        "Slack bot/user/app/refresh token (xox*)",
        re.compile(r"\bxox[baprs]-[A-Za-z0-9\-]{10,}\b"),
    ),
    (
        "Stripe live/test secret key",
        re.compile(r"\bsk_(live|test)_[A-Za-z0-9]{24,}\b"),
    ),
    (
        "PEM private key header",
        re.compile(r"-----BEGIN (RSA|EC|DSA|OPENSSH|PGP) PRIVATE KEY"),
    ),
    # --- Operator-specific PII patterns ---
    ("CRM with digits (medical license)", re.compile(r"CRM-\d{4,}")),
    (
        "Windows absolute user path (non-placeholder)",
        re.compile(
            r"(?i)\bc:\\users\\"
            r"(?!<username>|<you>|user(?:name)?\b|public\b|default\b|all users\b|\.\.\.)"
            r"(?!fabio\\)"
            r"[a-z0-9._-]+\\"
        ),
    ),
    (
        "Linux absolute /home path (non-placeholder)",
        re.compile(
            r"(?i)(?<!\w)/home/"
            r"(?!user/|you/|<user>/|replace_user/|\{\{|leitao/)"
            r"[a-z0-9._-]+/"
        ),
    ),
    (
        "LinkedIn profile URL (explicit personal slug)",
        re.compile(
            r"(?i)https?://(?:www\.)?linkedin\.com/in/"
            r"(?!example(?:[\"'\s`]|\Z)|<|\.{3}|replaced|redacted|\$|\{)"
            r"[^\s\"')]+"
        ),
    ),
    (
        "Family relationship phrase (sensitive context)",
        re.compile(r"(?i)\b(my\s+wife|my\s+sister(?:'s|s)\s+husband|cunhad[oa])\b"),
    ),
    (
        "Family phrase (Portuguese, high-signal)",
        re.compile(r"(?i)\btrabalho\s+da\s+esposa\b"),
    ),
    (
        "SSH URL with embedded user",
        re.compile(
            r"(?i)\bssh://(?!USER_REDACTED\b)([a-z0-9._-]+)@"
            r"(?!myserver\.example\.com\b|example\.com\b)"
        ),
    ),
    (
        "Utility account identifier (UC with many digits)",
        re.compile(r"(?i)\bUC\s*\d{6,}\b"),
    ),
]

_PRIVATE_PATTERNS_FILE = REPO_ROOT / "docs" / "private" / "pii-patterns.txt"

_ALLOWED_PATHS_PREFIXES = (
    "docs/private/",
    "docs/private.example/",
    ".cursor/private/",
    "tests/test_pii_guard.py",
    "scripts/pii_history_guard.py",
    "scripts/filter_repo_pii_replacements.txt",
)

_BINARY_EXTENSIONS = frozenset(
    {
        ".png",
        ".jpg",
        ".jpeg",
        ".gif",
        ".ico",
        ".webp",
        ".svg",
        ".woff",
        ".woff2",
        ".ttf",
        ".eot",
        ".pyc",
        ".pyo",
        ".so",
        ".dll",
        ".exe",
        ".zip",
        ".gz",
        ".tar",
        ".bz2",
        ".xz",
        ".xlsx",
        ".xls",
        ".pdf",
        ".db",
        ".sqlite",
        ".sqlite3",
        ".lock",
        ".gpg",
    }
)


def _git_ls_files() -> list[str]:
    proc = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=REPO_ROOT,
        capture_output=True,
        check=False,
    )
    if proc.returncode != 0 or not (REPO_ROOT / ".git").exists():
        pytest.skip("Not a git checkout or git ls-files failed.")
    raw = proc.stdout.split(b"\0")
    return [
        chunk.decode("utf-8", errors="replace").replace("\\", "/")
        for chunk in raw
        if chunk
    ]


def _load_private_patterns() -> list[str]:
    if not _PRIVATE_PATTERNS_FILE.is_file():
        return []
    return [
        line.strip()
        for line in _PRIVATE_PATTERNS_FILE.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]


def _is_allowed(path: str) -> bool:
    return any(path.startswith(pfx) for pfx in _ALLOWED_PATHS_PREFIXES)


def _is_binary(path: str) -> bool:
    return Path(path).suffix.lower() in _BINARY_EXTENSIONS


def _collect_violations(content: str, fpath: str, all_literals: list[str]) -> list[str]:
    lower_content = content.lower()
    violations: list[str] = []
    for lit in all_literals:
        if lit.lower() in lower_content:
            violations.append(f"  {fpath}: contains PII literal '{lit}'")
    for label, pattern in _BUILTIN_REGEXES:
        if pattern.search(content):
            violations.append(f"  {fpath}: matches PII regex '{label}'")
    return violations


def test_tracked_files_contain_no_pii_patterns():
    """Fail CI if any tracked file contains a known PII pattern."""
    all_literals = list(_BUILTIN_LITERALS) + _load_private_patterns()
    tracked = _git_ls_files()
    violations: list[str] = []

    for fpath in tracked:
        if _is_allowed(fpath) or _is_binary(fpath):
            continue
        full = REPO_ROOT / fpath
        if not full.is_file():
            continue
        try:
            content = full.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue

        violations.extend(_collect_violations(content, fpath, all_literals))

    assert not violations, (
        "PII guard failed -- move sensitive content to docs/private/ "
        "(gitignored stacked private repo):\n" + "\n".join(violations)
    )


def test_gitignore_covers_dossier_rule():
    """The old dossier rule file must stay gitignored."""
    gi = (REPO_ROOT / ".gitignore").read_text(encoding="utf-8", errors="replace")
    assert ".cursor/rules/dossier-update-on-evidence.mdc" in gi, (
        ".gitignore must keep .cursor/rules/dossier-update-on-evidence.mdc ignored"
    )


def test_guard_files_do_not_embed_sensitive_seed_literals():
    """
    Prevent recurrence where guardrails themselves reintroduce explicit
    sensitive literals used by long-run audits.

    Substrings are UTF-8 hex-encoded so this file does not contain greppable
    real names or home-path tokens (see CONTRIBUTING / public PII rules).
    """

    def _utf8_hex(h: str) -> str:
        return bytes.fromhex(h).decode("utf-8")

    banned = [
        _utf8_hex("6d792077696665"),
        _utf8_hex("6d792073697374657227732068757362616e64"),
        _utf8_hex("4976616e2046696c686f"),
        _utf8_hex("54616c697461204d6f7265697261"),
        _utf8_hex("4d61726c756365204c656974616f"),
        _utf8_hex("7373683a2f2f6c656974616f40"),
        _utf8_hex("433a5c55736572735c666162696f"),
        _utf8_hex("633a5c75736572735c666162696f"),
        _utf8_hex("2f686f6d652f6c656974616f"),
    ]
    targets = [
        REPO_ROOT / "scripts" / "pii_history_guard.py",
    ]

    violations: list[str] = []
    for target in targets:
        if not target.is_file():
            continue
        text = target.read_text(encoding="utf-8", errors="replace")
        lower = text.lower()
        for phrase in banned:
            if phrase.lower() in lower:
                violations.append(
                    f"  {target.relative_to(REPO_ROOT)} contains '{phrase}'"
                )

    assert not violations, (
        "Guard file leaked explicit sensitive seed literals:\n" + "\n".join(violations)
    )


_GRATITUDE_ATTRIBUTION_RE = re.compile(
    r"(?i)"
    r"\b(?:thanks?\s+to|thank\s+you\s+to"
    r"|agradec[ea](?:mos)?\s+[aà]"
    r"|agradeça\s+[aà]"
    r"|obrigad[oa]\s+[aà])\s+"
    r"[A-ZÁÉÍÓÚÂÊÎÔÛÀÈÌÒÙÃÕ][a-záéíóúâêîôûàèìòùãõ]{2,}"
    r"(?:\s+[A-ZÁÉÍÓÚÂÊÎÔÛÀÈÌÒÙÃÕ][a-záéíóúâêîôûàèìòùãõ]{2,})?"
)

# Paths that intentionally contain example gratitude phrases (rule definitions, etc.)
_GRATITUDE_ALLOWED_PATHS = {
    "tests/test_pii_guard.py",
    ".cursor/rules/private-pii-never-public.mdc",
}


def test_plan_and_usecase_files_no_gratitude_attribution():
    """
    Plan Motivation/Context sections must not contain gratitude phrases that
    attribute real people (e.g. 'thanks to a named contact', 'agradecemos a <nome>').

    Scans PLAN_*.md and docs/use-cases/**/*.md tracked files only — avoids
    false positives in generic docs where similar phrasing is legitimate.
    """
    tracked = _git_ls_files()
    violations: list[str] = []

    for fpath in tracked:
        if fpath in _GRATITUDE_ALLOWED_PATHS:
            continue
        if not (
            ("docs/plans/PLAN_" in fpath and fpath.endswith(".md"))
            or fpath.startswith("docs/use-cases/")
        ):
            continue
        full = REPO_ROOT / fpath
        if not full.is_file():
            continue
        try:
            content = full.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        if _GRATITUDE_ATTRIBUTION_RE.search(content):
            violations.append(
                f"  {fpath}: contains a gratitude attribution phrase "
                f"(real name in plan Motivation/Context — move to docs/private/)"
            )

    assert not violations, (
        "Plan/use-case PII guard failed — gratitude attribution with real name:\n"
        + "\n".join(violations)
    )


def test_pii_history_guard_diff_uses_three_dot_range(monkeypatch) -> None:
    """Regression #805: git diff must use merge-base (three-dot), not tree compare."""
    import scripts.pii_history_guard as guard

    calls: list[list[str]] = []

    def fake_git(args: list[str]) -> subprocess.CompletedProcess[str]:
        calls.append(args)
        return subprocess.CompletedProcess(args, 0, stdout="", stderr="")

    monkeypatch.setattr(guard, "_git", fake_git)
    guard._collect_lines_to_scan("origin/main..HEAD", 500)
    assert calls == [
        ["diff", "--unified=0", "--no-color", "origin/main...HEAD", "--", "."]
    ]


def test_pii_history_guard_ok_when_branch_is_ancestor_of_main(
    tmp_path: Path, monkeypatch
) -> None:
    """When HEAD has no commits ahead of origin/main, guard must not false-positive."""
    import scripts.pii_history_guard as guard

    repo = tmp_path / "repo"
    repo.mkdir()

    # Strip GIT_* control vars the runner may export (e.g. pre-commit stashes
    # changes and exports GIT_INDEX_FILE/GIT_DIR); without this, the tmp repo's
    # commits leak into the parent repo's index and fail with "invalid object".
    _git_env = {
        k: v
        for k, v in os.environ.items()
        if k
        not in {
            "GIT_DIR",
            "GIT_INDEX_FILE",
            "GIT_WORK_TREE",
            "GIT_OBJECT_DIRECTORY",
            "GIT_COMMON_DIR",
            "GIT_ALTERNATE_OBJECT_DIRECTORIES",
        }
    }

    def git(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["git", *args],
            cwd=repo,
            check=check,
            capture_output=True,
            text=True,
            env=_git_env,
        )

    git("init", "-b", "main")
    git("config", "user.email", "guard@test.example")
    git("config", "user.name", "Guard Test")
    sample = repo / "sample.md"
    sample.write_text(
        '"git_origin": "ssh://operator@lab-host-not-example/home/dev/data-boar"\n',
        encoding="utf-8",
    )
    git("add", "sample.md")
    git("commit", "-m", "base with ssh url")
    git("checkout", "-b", "feature-behind")
    git("checkout", "main")
    sample.write_text("git_origin placeholder only\n", encoding="utf-8")
    git("add", "sample.md")
    git("commit", "-m", "fix on main")
    main_sha = git("rev-parse", "main").stdout.strip()
    git("update-ref", "refs/remotes/origin/main", main_sha)
    git("checkout", "feature-behind")

    monkeypatch.setattr(guard, "REPO_ROOT", repo)
    monkeypatch.setattr(sys, "argv", ["pii_history_guard.py"])
    assert guard.main() == 0
