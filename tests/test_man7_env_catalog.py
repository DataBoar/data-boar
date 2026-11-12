"""
#1990: ``docs/data_boar.7`` must catalogue every environment variable that production code reads.

The inventory is a static (AST) analysis, so names resolved through module constants and the
defaults of ``*_from_env`` keys are found too; a plain ``grep`` for ``os.environ.get("X")``
misses them. A variable that production code reads must be cited in the page or listed in
``tests/man7_env_exclusions.txt`` with a reason.
"""

from __future__ import annotations

import ast
import os
import re
import shutil
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
MAN7_PATH = REPO_ROOT / "docs" / "data_boar.7"
EXCLUSIONS_PATH = Path(__file__).with_name("man7_env_exclusions.txt")

NAME_RE = re.compile(r"^[A-Z][A-Z0-9_]{2,}$")
SKIP_DIRS = {
    "tests",
    ".venv",
    "venv",
    "node_modules",
    "__pycache__",
    ".git",
    "build",
    "dist",
    "target",
    "staging",
    "site-packages",
    ".tox",
    ".mypy_cache",
    ".ruff_cache",
    ".pytest_cache",
}
EXCLUSION_REASONS = frozenset(
    {"ci", "release", "lab", "vendor-issuer", "licensing-pending"}
)
# Names documented on the page that production code only reaches through a config key
# (``api.api_key_from_env: AUDIT_API_KEY``), so no literal read exists to find.
INDIRECT_DOCUMENTED = frozenset({"AUDIT_API_KEY"})
# Operator decision (2026-11-12): never on the public page.
NEVER_ON_PAGE_PREFIXES = ("DATA_BOAR_LICENSE_",)
NEVER_ON_PAGE = frozenset(
    {
        "DATA_BOAR_MACHINE_SEED",
        "DATA_BOAR_EXPECTED_BUILD_DIGEST",
        "DATA_BOAR_RELEASE_MANIFEST_PATH",
        "DATA_BOAR_GRC_JSON",
    }
)


def _is_environ(node: ast.AST) -> bool:
    return (isinstance(node, ast.Attribute) and node.attr == "environ") or (
        isinstance(node, ast.Name) and node.id == "environ"
    )


def _is_os_getenv(func: ast.AST) -> bool:
    return (
        isinstance(func, ast.Attribute)
        and func.attr == "getenv"
        and isinstance(func.value, ast.Name)
        and func.value.id == "os"
    )


def scan_env_inventory(root: Path) -> tuple[dict[str, str], int]:
    """Return ``({NAME: first file}, number of config-named reads)`` for production code."""
    used: dict[str, str] = {}
    dynamic = 0
    for dirpath, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for fname in (f for f in files if f.endswith(".py")):
            path = Path(dirpath) / fname
            src = path.read_text(encoding="utf-8", errors="ignore")
            try:
                tree = ast.parse(src)
            except SyntaxError:
                continue
            consts = {
                t.id: n.value.value
                for n in ast.walk(tree)
                if isinstance(n, ast.Assign)
                and isinstance(n.value, ast.Constant)
                and isinstance(n.value.value, str)
                for t in n.targets
                if isinstance(t, ast.Name)
            }

            def resolve(arg: ast.AST, consts: dict[str, str] = consts) -> str | None:
                if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                    return arg.value
                if isinstance(arg, ast.Name):
                    return consts.get(arg.id)
                return None

            rel = path.relative_to(root).as_posix()
            for n in ast.walk(tree):
                name: str | None
                if (
                    isinstance(n, ast.Call)
                    and n.args
                    and isinstance(n.func, ast.Attribute)
                    and (
                        (n.func.attr == "get" and _is_environ(n.func.value))
                        or _is_os_getenv(n.func)
                    )
                ):
                    name = resolve(n.args[0])
                elif isinstance(n, ast.Subscript) and _is_environ(n.value):
                    name = resolve(n.slice)
                elif isinstance(n, ast.BoolOp) and isinstance(n.op, ast.Or):
                    seg = ast.get_source_segment(src, n) or ""
                    if re.search(r"from_env|_env[\"']", seg):
                        for v in n.values:
                            if (
                                isinstance(v, ast.Constant)
                                and isinstance(v.value, str)
                                and NAME_RE.match(v.value)
                                and len(v.value) >= 6
                            ):
                                used.setdefault(v.value, rel)
                    continue
                else:
                    continue
                if name and NAME_RE.match(name):
                    used.setdefault(name, rel)
                elif name is None:
                    dynamic += 1
    return used, dynamic


def load_exclusions() -> dict[str, str]:
    """Parse ``man7_env_exclusions.txt``; a missing or unknown reason is an error."""
    out: dict[str, str] = {}
    for lineno, raw in enumerate(
        EXCLUSIONS_PATH.read_text(encoding="utf-8").splitlines(), start=1
    ):
        line = raw.split("#", 1)[0].strip()
        if not line:
            continue
        parts = line.split()
        assert len(parts) == 2, (
            f"{EXCLUSIONS_PATH.name}:{lineno}: expected 'NAME REASON', got {raw!r}"
        )
        name, reason = parts
        assert NAME_RE.match(name), (
            f"{EXCLUSIONS_PATH.name}:{lineno}: bad name {name!r}"
        )
        assert reason in EXCLUSION_REASONS, (
            f"{EXCLUSIONS_PATH.name}:{lineno}: reason {reason!r} not in "
            f"{sorted(EXCLUSION_REASONS)}"
        )
        assert name not in out, f"{EXCLUSIONS_PATH.name}:{lineno}: duplicate {name}"
        out[name] = reason
    return out


@pytest.fixture(scope="module")
def man7_text() -> str:
    assert MAN7_PATH.is_file(), f"missing {MAN7_PATH}"
    return MAN7_PATH.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def inventory() -> dict[str, str]:
    used, dynamic = scan_env_inventory(REPO_ROOT)
    assert used, "inventory is empty: the scanner is broken"
    assert dynamic > 0, "no config-named reads found: the scanner is broken"
    return used


def _cited(man7_text: str) -> set[str]:
    """Every upper-case variable-like token in the page, troff escapes removed."""
    plain = man7_text.replace("\\-", "-").replace("\\_", "_")
    return set(re.findall(r"\b[A-Z][A-Z0-9_]{2,}\b", plain))


def _defined(man7_text: str) -> set[str]:
    """Variables defined as ``.TP`` / ``.B NAME`` entries (the page's own definitions)."""
    out: set[str] = set()
    lines = man7_text.splitlines()
    for i, line in enumerate(lines[:-1]):
        if line.strip() == ".TP":
            m = re.fullmatch(r"\.B ([A-Z][A-Z0-9_]{2,})", lines[i + 1].strip())
            if m:
                out.add(m.group(1))
    return out


def test_man7_exists_and_has_no_tq(man7_text: str) -> None:
    assert ".TQ" not in man7_text, (
        ".TQ is a GNU groff extension; mandoc hosts reject it"
    )
    assert "\n.SH ENVIRONMENT\n" in man7_text


@pytest.mark.skipif(shutil.which("groff") is None, reason="groff not installed")
def test_man7_groff_clean() -> None:
    result = subprocess.run(
        ["groff", "-man", "-ww", "-z", str(MAN7_PATH)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert result.stderr.strip() == "", result.stderr


def test_every_production_env_var_is_documented_or_excluded(
    inventory: dict[str, str], man7_text: str
) -> None:
    exclusions = load_exclusions()
    missing = sorted(set(inventory) - _cited(man7_text) - set(exclusions))
    assert not missing, (
        "production code reads environment variables that docs/data_boar.7 does not "
        "cite and tests/man7_env_exclusions.txt does not exclude: "
        + ", ".join(f"{n} ({inventory[n]})" for n in missing)
        + ". Document them in docs/data_boar.7 or add 'NAME reason' to the exclusion list."
    )


def test_every_defined_variable_exists_in_code(
    inventory: dict[str, str], man7_text: str
) -> None:
    phantom = sorted(_defined(man7_text) - set(inventory) - INDIRECT_DOCUMENTED)
    assert not phantom, (
        f"docs/data_boar.7 defines variables that production code never reads: {phantom}"
    )


def test_exclusions_are_not_stale(inventory: dict[str, str]) -> None:
    stale = sorted(set(load_exclusions()) - set(inventory))
    assert not stale, f"exclusions no longer read by production code: {stale}"


def test_excluded_variables_are_not_also_documented(man7_text: str) -> None:
    both = sorted(set(load_exclusions()) & _defined(man7_text))
    assert not both, f"documented in data_boar.7 and excluded at once: {both}"


def test_licensing_and_issuer_variables_stay_off_the_page(man7_text: str) -> None:
    cited = _cited(man7_text)
    exclusions = load_exclusions()
    private = {
        n
        for n, reason in exclusions.items()
        if reason in {"vendor-issuer", "licensing-pending"}
    } | NEVER_ON_PAGE
    leaked = sorted(
        n for n in cited if n in private or n.startswith(NEVER_ON_PAGE_PREFIXES)
    )
    assert not leaked, f"operator decision: these must not be on the page: {leaked}"


def test_internal_variables_are_marked_do_not_set(man7_text: str) -> None:
    section = man7_text.split(".SS Variables set by the program (do not set)", 1)[1]
    section = section.split(".SS ", 1)[0]
    for name in (
        "DATA_BOAR_DASHBOARD_TRANSPORT",
        "DATA_BOAR_DASHBOARD_INSECURE_OPT_IN",
        "DATA_BOAR_HTTPS_CERT_FILE",
        "DATA_BOAR_HTTPS_KEY_FILE",
        "DATA_BOAR_TLS_POSTURE",
    ):
        assert name in section, f"{name} must sit in the do-not-set section"
