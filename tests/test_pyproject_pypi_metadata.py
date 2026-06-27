"""PyPI packaging metadata guards (#1042 / ADR-0031)."""

from __future__ import annotations

import subprocess
import tomllib
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
PYPROJECT = REPO_ROOT / "pyproject.toml"

# Trove classifiers must match PyPI allow-list (invalid = upload rejected).
_EXPECTED_CLASSIFIERS = (
    "Development Status :: 5 - Production/Stable",
    "Intended Audience :: Developers",
    "Intended Audience :: System Administrators",
    "Intended Audience :: Legal Industry",
    "License :: OSI Approved :: BSD License",
    "Operating System :: OS Independent",
    "Programming Language :: Python :: 3.12",
    "Programming Language :: Python :: 3.13",
    "Programming Language :: Python :: 3.14",
    "Topic :: Security",
    "Topic :: Database",
)


def _project() -> dict:
    with PYPROJECT.open("rb") as handle:
        data = tomllib.load(handle)
    project = data.get("project")
    assert isinstance(project, dict), "pyproject.toml must define [project]"
    return project


def test_pyproject_pypi_license_and_authors() -> None:
    project = _project()
    assert project.get("license") == "BSD-3-Clause"
    assert project.get("license-files") == ["LICENSE"]
    authors = project.get("authors")
    assert isinstance(authors, list) and authors
    first = authors[0]
    assert isinstance(first, dict)
    assert first.get("name")
    assert first.get("email") == "author@databoar.com.br"


def test_pyproject_pypi_classifiers_are_valid_trove() -> None:
    """Classifiers must be on PyPI trove allow-list (uvx — no lock churn)."""
    project = _project()
    classifiers = project.get("classifiers")
    assert isinstance(classifiers, list)
    assert tuple(classifiers) == _EXPECTED_CLASSIFIERS
    script = (
        "from trove_classifiers import sorted_classifiers\n"
        "import sys\n"
        "valid = set(sorted_classifiers)\n"
        "bad = [c for c in sys.argv[1:] if c not in valid]\n"
        "sys.exit(1) if bad else sys.exit(0)\n"
    )
    proc = subprocess.run(
        ["uvx", "--from", "trove-classifiers", "python", "-c", script, *classifiers],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr or proc.stdout or "trove check failed"


def test_pyproject_pypi_urls_present() -> None:
    with PYPROJECT.open("rb") as handle:
        data = tomllib.load(handle)
    urls = data.get("project", {}).get("urls")
    assert isinstance(urls, dict)
    for key in ("Homepage", "Repository", "Issues", "Changelog", "Docker Hub"):
        assert urls.get(key), f"missing [project.urls] {key}"
