"""
Anti-regression guard: no third-party feature-flag SDK lands silently.

This guard is the seatbelt that pairs with
``docs/ops/sre_audits/STALE_FEATURE_FLAG_AUDIT_2026-04-27.md``. The
SRE Automation Agent's cleanup protocol asked: "are stale flags rolled out
at 100% lying around?" — the answer was "no SDK is wired in at all." This
test pins that answer so a future PR has to (a) update this list and
(b) ship an ADR if it really wants to add a vendor.

Doctrine references:
  - docs/ops/inspirations/DEFENSIVE_SCANNING_MANIFESTO.md (no surprise side
    effects: this test never opens a network or DB connection).
  - docs/ops/inspirations/THE_ART_OF_THE_FALLBACK.md (diagnostic on fall:
    when a manifest is missing we explain what was checked, not raise a
    cryptic FileNotFoundError).
  - docs/ops/inspirations/SUPPLY_CHAIN_AND_TRUST_SIGNALS.md (every new
    runtime dependency is a supply-chain hop; flag SDKs in particular
    phone home, so they need an ADR + sunset plan).
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]

# Vendors that ship general-purpose runtime feature-flag SDKs in Python.
# Names are matched case-insensitively as **substrings** of dependency
# names / Python module imports. This list is intentionally finite; the
# point is to fail loudly enough that a maintainer notices, not to be
# exhaustive of every flag SaaS in existence.
KNOWN_FLAG_SDK_TOKENS: tuple[str, ...] = (
    "statsig",
    "launchdarkly",
    "ldclient",
    "unleash",
    "flagsmith",
    "splitio",
    "split-sdk",
)

# Repository paths whose presence of these tokens is allowed because
# they are *meta* references (this test, the audit doc echoing them,
# the SRE protocol prompt). Anything else is a real dependency.
ALLOWED_PATHS: frozenset[Path] = frozenset(
    {
        Path("tests") / "test_no_third_party_feature_flag_sdks.py",
        Path("docs") / "ops" / "sre_audits" / "STALE_FEATURE_FLAG_AUDIT_2026-04-27.md",
        Path("docs")
        / "ops"
        / "sre_audits"
        / "STALE_FEATURE_FLAG_AUDIT_2026-04-27.pt_BR.md",
    }
)


def _read_text_or_skip(rel_path: str) -> str:
    """Return file text or skip the test with a clear diagnostic."""
    p = REPO_ROOT / rel_path
    if not p.exists():
        pytest.skip(f"manifest not present in this checkout: {rel_path}")
    return p.read_text(encoding="utf-8", errors="replace")


def _dep_lines(text: str) -> list[str]:
    """Return non-comment, non-empty lines plausibly listing dependencies.

    Conservative parser by design: we never want to evaluate TOML or
    requirements syntax to grep for vendor names. We just need enough
    structure to reject obvious comment / heading lines.
    """
    out: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("#"):
            continue
        out.append(stripped.lower())
    return out


# ---------------------------------------------------------------------------
# 1) Dependency manifests
# ---------------------------------------------------------------------------


def test_pyproject_toml_has_no_flag_sdk_dependency():
    text = _read_text_or_skip("pyproject.toml")
    lower = text.lower()
    for token in KNOWN_FLAG_SDK_TOKENS:
        assert token not in lower, (
            f"pyproject.toml mentions {token!r}; a third-party feature-flag SDK "
            "must not land without (a) an ADR and (b) updating "
            "tests/test_no_third_party_feature_flag_sdks.py allow-list."
        )


def test_requirements_txt_has_no_flag_sdk_dependency():
    text = _read_text_or_skip("requirements.txt")
    for line in _dep_lines(text):
        for token in KNOWN_FLAG_SDK_TOKENS:
            assert token not in line, (
                f"requirements.txt line mentions {token!r}: {line!r}. "
                "Add an ADR and extend KNOWN_FLAG_SDK_TOKENS only after "
                "review."
            )


def test_pylock_toml_has_no_flag_sdk_dependency():
    p = REPO_ROOT / "pylock.toml"
    if not p.exists():
        pytest.skip("pylock.toml not present in this checkout")
    text = p.read_text(encoding="utf-8", errors="replace").lower()
    # pylock.toml is verbose (URLs, hashes); we only care about
    # `name = "..."` lines for package identity.
    name_lines = re.findall(r"^\s*name\s*=\s*\"([^\"]+)\"\s*$", text, flags=re.M)
    for token in KNOWN_FLAG_SDK_TOKENS:
        offending = [n for n in name_lines if token in n]
        assert not offending, (
            f"pylock.toml lists package(s) {offending!r} matching banned "
            f"token {token!r}. See "
            "docs/ops/sre_audits/STALE_FEATURE_FLAG_AUDIT_2026-04-27.md."
        )


# ---------------------------------------------------------------------------
# 2) No tracked Python source imports a flag SDK
# ---------------------------------------------------------------------------


_PY_DIRS_TO_SCAN: tuple[str, ...] = (
    "core",
    "connectors",
    "api",
    "app",
    "report",
    "scanners",
    "schemas",
    "logging_custom",
    "utils",
    "cli",
    "analysis",
    "pro",
    "file_scan",
)


def _python_files() -> list[Path]:
    out: list[Path] = []
    for sub in _PY_DIRS_TO_SCAN:
        root = REPO_ROOT / sub
        if not root.exists():
            continue
        out.extend(p for p in root.rglob("*.py") if p.is_file())
    main_py = REPO_ROOT / "main.py"
    if main_py.exists():
        out.append(main_py)
    return out


def test_no_python_module_imports_flag_sdk():
    pattern = re.compile(
        r"^\s*(?:from|import)\s+([A-Za-z0-9_.]+)",
        flags=re.M,
    )
    failures: list[str] = []
    for path in _python_files():
        rel = path.relative_to(REPO_ROOT)
        if rel in ALLOWED_PATHS:
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        for match in pattern.finditer(text):
            module = match.group(1).lower()
            for token in KNOWN_FLAG_SDK_TOKENS:
                if token in module:
                    failures.append(f"{rel}: imports {match.group(1)!r}")
    assert not failures, (
        "third-party feature-flag SDK import detected:\n  - "
        + "\n  - ".join(failures)
        + "\nSee docs/ops/sre_audits/STALE_FEATURE_FLAG_AUDIT_2026-04-27.md "
        "for the rationale and the ADR/allow-list workflow."
    )


# ---------------------------------------------------------------------------
# 3) Self-check: the audit doc that justifies this guard exists
# ---------------------------------------------------------------------------


def test_audit_doc_pair_exists():
    en = (
        REPO_ROOT
        / "docs"
        / "ops"
        / "sre_audits"
        / "STALE_FEATURE_FLAG_AUDIT_2026-04-27.md"
    )
    pt = (
        REPO_ROOT
        / "docs"
        / "ops"
        / "sre_audits"
        / "STALE_FEATURE_FLAG_AUDIT_2026-04-27.pt_BR.md"
    )
    assert en.is_file(), f"missing audit doc (EN): {en}"
    assert pt.is_file(), f"missing audit doc (pt-BR): {pt}"
