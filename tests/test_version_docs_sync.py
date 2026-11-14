"""Version docs stay in sync after a bump or a publish (#2247).

The bump checklist (docs/VERSIONING.md, section 5) and ``test_published_sync``
did not cover SECURITY / CONTRIBUTING / the VERSIONING "current lines" table,
so they drifted after the 1.8.0 publish. This test pins:

- SECURITY.md / SECURITY.pt_BR.md "Supported versions" table cites the latest
  published **GA** tag (local ``v*`` tags, PEP 440 only, pre-releases ignored);
- the ``main`` row there names the ``pyproject.toml`` version and is not called
  ``-rc`` / ``-beta`` when the pyproject version has no such suffix;
- CONTRIBUTING (en / pt_BR) never says a published version "matches"
  ``pyproject.toml`` unless the versions are equal;
- the "main working tree" row of docs/VERSIONING(.pt_BR).md cites the
  ``pyproject.toml`` version.
"""

from __future__ import annotations

import re
import subprocess
import tomllib
from pathlib import Path

import pytest
from packaging.version import InvalidVersion, Version

REPO_ROOT = Path(__file__).resolve().parents[1]
SECURITY = {
    "en": (REPO_ROOT / "SECURITY.md", "## Supported versions", "**Not supported"),
    "pt_BR": (
        REPO_ROOT / "SECURITY.pt_BR.md",
        "## Versões suportadas",
        "**Não suportado",
    ),
}
CONTRIBUTING = {
    "en": REPO_ROOT / "CONTRIBUTING.md",
    "pt_BR": REPO_ROOT / "CONTRIBUTING.pt_BR.md",
}
VERSIONING = {
    "en": (REPO_ROOT / "docs" / "VERSIONING.md", "| **`main` working tree**"),
    "pt_BR": (REPO_ROOT / "docs" / "VERSIONING.pt_BR.md", "| **Working tree `main`**"),
}
_SEMVERISH = re.compile(r"\b\d+\.\d+\.\d+(?:\.post\d+|-rc(?:[.-]?\d+)?|-beta)?\b")


def _pyproject_version() -> str:
    with (REPO_ROOT / "pyproject.toml").open("rb") as f:
        return str(tomllib.load(f)["project"]["version"])


def _latest_published_ga() -> str:
    proc = subprocess.run(
        ["git", "tag", "-l", "v*"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr
    best: Version | None = None
    for tag in proc.stdout.split():
        try:
            v = Version(tag.removeprefix("v"))
        except InvalidVersion:
            continue  # labels such as v1.7.2-safe
        if v.is_prerelease or v.is_devrelease:
            continue
        # A .postN republication belongs to the same public line X.Y.Z.
        base = Version(v.base_version)
        if best is None or base > best:
            best = base
    assert best is not None, "expected at least one published v* tag"
    return str(best)


def _has_suffix(version: str) -> bool:
    return bool(re.search(r"-(rc|beta)", version)) or Version(version).is_prerelease


def _section(text: str, start: str, end: str) -> str:
    assert start in text, f"missing heading {start!r}"
    body = text.split(start, 1)[1]
    assert end in body, f"missing {end!r} after {start!r}"
    return body.split(end, 1)[0]


@pytest.mark.parametrize("lang", sorted(SECURITY))
def test_d2247_security_table_cites_latest_published_tag(lang: str) -> None:
    path, start, end = SECURITY[lang]
    table = _section(path.read_text(encoding="utf-8"), start, end)
    latest = _latest_published_ga()
    assert f"**{latest}**" in table, (
        f"{path.name}: 'Supported versions' must list the latest published "
        f"tag {latest} (local v* tags)"
    )


@pytest.mark.parametrize("lang", sorted(SECURITY))
def test_d2247_security_main_row_matches_pyproject(lang: str) -> None:
    path, start, end = SECURITY[lang]
    table = _section(path.read_text(encoding="utf-8"), start, end)
    rows = [ln for ln in table.splitlines() if ln.startswith("| **`main`**")]
    assert len(rows) == 1, f"{path.name}: expected one `main` row, got {rows}"
    version = _pyproject_version()
    assert f"**{version}**" in rows[0], (
        f"{path.name}: `main` row must cite pyproject version {version}"
    )
    if not _has_suffix(version):
        assert not re.search(r"-(rc|beta)\b", rows[0]), (
            f"{path.name}: `main` row calls main -rc/-beta but pyproject is {version}"
        )


@pytest.mark.parametrize("lang", sorted(CONTRIBUTING))
def test_d2247_contributing_matching_claim_is_true(lang: str) -> None:
    path = CONTRIBUTING[lang]
    version = _pyproject_version()
    text = path.read_text(encoding="utf-8")
    claims = [
        ln
        for ln in text.splitlines()
        if "pyproject.toml" in ln and re.search(r"\b(matching|alinhad[oa])\b", ln)
    ]
    for line in claims:
        quoted = _SEMVERISH.findall(line)
        assert quoted, f"{path.name}: matching claim without a version: {line!r}"
        assert all(q == version for q in quoted), (
            f"{path.name}: claims {quoted} match pyproject.toml, which is {version}"
        )


@pytest.mark.parametrize("lang", sorted(VERSIONING))
def test_d2247_versioning_main_row_cites_pyproject(lang: str) -> None:
    path, prefix = VERSIONING[lang]
    rows = [
        ln
        for ln in path.read_text(encoding="utf-8").splitlines()
        if ln.startswith(prefix)
    ]
    assert len(rows) == 1, f"{path.name}: expected one {prefix!r} row, got {rows}"
    version = _pyproject_version()
    assert f"**`{version}`**" in rows[0], (
        f"{path.name}: main working tree row must cite pyproject version {version}"
    )
